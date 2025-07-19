#!/usr/bin/env python3
import os
import sys

"""
Standalone Django script for managing retention policies.

Usage examples:
  docker-compose exec django python scripts/manage_retention.py cleanup --dry-run
  docker-compose exec django python scripts/manage_retention.py status
  docker-compose exec django python scripts/manage_retention.py status --challenge-id 123
  docker-compose exec django python scripts/manage_retention.py set-log-retention 123 --days 30
  docker-compose exec django python scripts/manage_retention.py generate-report --format csv --output report.csv
  docker-compose exec django python scripts/manage_retention.py check-health --verbose

Note: This script is designed to run inside the Django Docker container.
"""

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)) + "/../")

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.common")
import django

django.setup()

import csv
import json
import logging
from datetime import timedelta
from io import StringIO

from challenges.aws_utils import (
    calculate_retention_period_days,
    calculate_submission_retention_date,
    cleanup_expired_submission_artifacts,
    delete_submission_files_from_storage,
    map_retention_days_to_aws_values,
    record_host_retention_consent,
    set_cloudwatch_log_retention,
    update_submission_retention_dates,
    weekly_retention_notifications_and_consent_log,
)
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
from hosts.utils import is_user_a_host_of_challenge
from jobs.models import Submission

logger = logging.getLogger(__name__)


def print_success(message):
    print(f"SUCCESS: {message}")


def print_error(message):
    print(f"ERROR: {message}")


def print_warning(message):
    print(f"WARNING: {message}")


def print_info(message):
    print(f"INFO: {message}")


def handle_cleanup(dry_run=False):
    """Clean up expired submission artifacts"""
    if dry_run:
        print_info("DRY RUN: Showing what would be cleaned up...")

    now = timezone.now()
    eligible_submissions = Submission.objects.filter(
        retention_eligible_date__lte=now,
        retention_eligible_date__isnull=False,  # Exclude indefinite retention
        is_artifact_deleted=False,
    ).select_related("challenge_phase__challenge")

    if not eligible_submissions.exists():
        print_success(
            "✅ CLEANUP COMPLETED: No submissions eligible for cleanup - all submissions are either not expired or already cleaned up."
        )
        return

    print_info(
        f"Found {eligible_submissions.count()} submissions eligible for cleanup:"
    )

    for submission in eligible_submissions:
        challenge_name = submission.challenge_phase.challenge.title
        phase_name = submission.challenge_phase.name
        print_info(
            f"  - Submission {submission.pk} from challenge '{challenge_name}' phase '{phase_name}' (eligible since {submission.retention_eligible_date})"
        )

    if dry_run:
        print_success(
            "✅ DRY RUN COMPLETED: Would clean up {eligible_submissions.count()} expired submission artifacts"
        )
        return

    confirm = input("\nProceed with cleanup? (yes/no): ")
    if confirm.lower() != "yes":
        print_info("Cleanup cancelled.")
        return

    # Run the actual cleanup
    result = cleanup_expired_submission_artifacts.delay()
    print_success(
        f"✅ CLEANUP INITIATED: Started cleanup task for {eligible_submissions.count()} expired submission artifacts. Task ID: {result.id}"
    )


def handle_update_dates():
    """Update retention eligible dates for submissions"""
    print_info("Updating submission retention dates...")

    try:
        # Run directly instead of via Celery in development
        result = update_submission_retention_dates()
        updated_count = result.get("updated_submissions", 0)
        print_success(
            f"✅ RETENTION DATES UPDATED: Successfully updated retention eligible dates for {updated_count} submissions"
        )
    except Exception as e:
        print_error(f"Failed to update retention dates: {e}")
        logger.exception("Error updating retention dates")


def handle_send_warnings():
    """Send retention warning notifications to challenge hosts"""
    print_info("Sending retention warning notifications...")

    result = weekly_retention_notifications_and_consent_log.delay()
    print_success(
        f"✅ WARNING NOTIFICATIONS SENT: Started notification task to send retention warnings to challenge hosts. Task ID: {result.id}"
    )


def handle_set_log_retention(challenge_id, days=None):
    """Set CloudWatch log retention for a specific challenge"""
    try:
        challenge = Challenge.objects.get(id=challenge_id)
    except Challenge.DoesNotExist:
        print_error(f"Challenge {challenge_id} does not exist")
        return

    print_info(
        f"Setting log retention for challenge {challenge_id}: {challenge.title}"
    )

    result = set_cloudwatch_log_retention(challenge_id, days)

    if result.get("success"):
        retention_days = result["retention_days"]
        log_group = result["log_group"]
        print_success(
            f"✅ LOG RETENTION SET: Successfully configured CloudWatch log retention to {retention_days} days for challenge '{challenge.title}' (ID: {challenge_id}). Log group: {log_group}"
        )
    else:
        print_error(f"Failed to set log retention: {result.get('error')}")


def handle_force_delete(submission_id, confirm=False):
    """Force delete submission files for a specific submission"""
    try:
        submission = Submission.objects.get(id=submission_id)
    except Submission.DoesNotExist:
        print_error(f"Submission {submission_id} does not exist")
        return

    if submission.is_artifact_deleted:
        print_warning(f"Submission {submission_id} artifacts already deleted")
        return

    challenge_name = submission.challenge_phase.challenge.title
    phase_name = submission.challenge_phase.name

    print_info(
        f"Submission {submission_id} from challenge '{challenge_name}' phase '{phase_name}'"
    )

    if not confirm:
        confirm_input = input(
            "Are you sure you want to delete the submission files? (yes/no): "
        )
        if confirm_input.lower() != "yes":
            print_info("Deletion cancelled.")
            return

    result = delete_submission_files_from_storage(submission)

    if result["success"]:
        deleted_count = len(result["deleted_files"])
        failed_count = len(result.get("failed_files", []))
        print_success(
            f"✅ SUBMISSION FILES DELETED: Successfully deleted {deleted_count} files for submission {submission_id} from challenge '{challenge_name}'"
        )
        if failed_count > 0:
            print_warning(
                f"⚠️  PARTIAL FAILURE: Failed to delete {failed_count} files for submission {submission_id}"
            )
    else:
        print_error(
            f"Failed to delete submission files: {result.get('error')}"
        )


def handle_status(challenge_id=None):
    """Show retention status for challenges and submissions"""
    if challenge_id:
        show_challenge_status(challenge_id)
    else:
        show_overall_status()


def show_challenge_status(challenge_id):
    """Show retention status for a specific challenge"""
    try:
        challenge = Challenge.objects.get(id=challenge_id)
        print_info(f"Retention status for challenge: {challenge.title}")
        print_info("=" * 50)

        # Show consent status prominently
        print_info("📋 CONSENT STATUS:")
        if challenge.retention_policy_consent:
            print_success("✅ HOST HAS CONSENTED TO 30-DAY RETENTION POLICY")
            print_info(
                f"   Consent provided by: {challenge.retention_policy_consent_by.username if challenge.retention_policy_consent_by else 'Unknown'}"
            )
            print_info(
                f"   Consent date: {challenge.retention_policy_consent_date.strftime('%Y-%m-%d %H:%M:%S') if challenge.retention_policy_consent_date else 'Unknown'}"
            )
            if challenge.retention_policy_notes:
                print_info(f"   Notes: {challenge.retention_policy_notes}")
            print_info(f"   Retention policy: 30-day retention allowed")
        else:
            print_warning(
                "❌ HOST HAS NOT CONSENTED - INDEFINITE RETENTION APPLIED"
            )
            print_info(
                f"   Retention policy: Indefinite retention (no automatic cleanup)"
            )
            print_info(
                f"   Action needed: Host must provide consent for 30-day retention"
            )

        # Show admin override if set
        if challenge.log_retention_days_override:
            print_info("🔧 ADMIN OVERRIDE:")
            print_info(
                f"   Log retention override: {challenge.log_retention_days_override} days"
            )

        phases = ChallengePhase.objects.filter(challenge=challenge)

        for phase in phases:
            print_info(f"\nPhase: {phase.name}")
            print_info(f"  End date: {phase.end_date}")
            print_info(f"  Is public: {phase.is_public}")

            # Calculate retention period based on consent status
            if phase.end_date:
                retention_days = calculate_retention_period_days(
                    phase.end_date, challenge
                )
                aws_retention_days = map_retention_days_to_aws_values(
                    retention_days
                )
                print_info(
                    f"  Calculated retention period: {retention_days} days"
                )
                print_info(
                    f"  AWS CloudWatch retention: {aws_retention_days} days"
                )

            retention_date = calculate_submission_retention_date(phase)
            if retention_date:
                print_info(f"  Retention eligible date: {retention_date}")
            else:
                if phase.is_public:
                    print_info(
                        "  Retention not applicable (phase still public)"
                    )
                elif not phase.end_date:
                    print_info("  Retention not applicable (no end date)")
                else:
                    print_info("  Retention: Indefinite (no host consent)")

            submissions = Submission.objects.filter(challenge_phase=phase)
            total_submissions = submissions.count()
            deleted_submissions = submissions.filter(
                is_artifact_deleted=True
            ).count()
            eligible_submissions = submissions.filter(
                retention_eligible_date__lte=timezone.now(),
                is_artifact_deleted=False,
            ).count()

            print_info(f"  Total submissions: {total_submissions}")
            print_info(f"  Artifacts deleted: {deleted_submissions}")
            print_info(f"  Eligible for cleanup: {eligible_submissions}")

        # Show actionable information for admins
        print_info("💡 ADMIN ACTIONS:")
        if not challenge.retention_policy_consent:
            print_warning(
                "   • Host needs to provide consent for 30-day retention"
            )
            print_info(
                "   • Use: docker-compose exec django python manage.py shell < scripts/manage_retention.py record-consent <challenge_id> --username <host_username>"
            )
        else:
            print_success(
                "   • Host has consented - 30-day retention policy can be applied"
            )
            print_info(
                "   • Use: docker-compose exec django python manage.py shell < scripts/manage_retention.py set-log-retention <challenge_id>"
            )

    except Challenge.DoesNotExist:
        print_error(f"Challenge {challenge_id} does not exist")


def show_overall_status():
    """Show overall retention status"""
    print_info("Overall retention status:")
    print_info("=" * 30)

    total_submissions = Submission.objects.count()
    deleted_submissions = Submission.objects.filter(
        is_artifact_deleted=True
    ).count()
    eligible_submissions = Submission.objects.filter(
        retention_eligible_date__lte=timezone.now(),
        retention_eligible_date__isnull=False,  # Exclude indefinite retention
        is_artifact_deleted=False,
    ).count()

    print_info(f"Total submissions: {total_submissions}")
    print_info(f"Artifacts deleted: {deleted_submissions}")
    print_info(f"Eligible for cleanup: {eligible_submissions}")

    # Show consent statistics
    total_challenges = Challenge.objects.count()
    consented_challenges = Challenge.objects.filter(
        retention_policy_consent=True
    ).count()
    non_consented_challenges = total_challenges - consented_challenges

    print_info("📋 CONSENT STATISTICS:")
    print_info(f"Total challenges: {total_challenges}")
    print_info(f"With consent (30-day retention): {consented_challenges}")
    print_info(
        f"Without consent (indefinite retention): {non_consented_challenges}"
    )

    if non_consented_challenges > 0:
        print_warning(
            f"⚠️  {non_consented_challenges} challenges need consent for 30-day retention policy!"
        )
    else:
        print_success("🎉 All challenges have consent for 30-day retention!")

    # Show challenges with upcoming retention dates
    upcoming_date = timezone.now() + timedelta(days=14)
    upcoming_submissions = Submission.objects.filter(
        retention_eligible_date__lte=upcoming_date,
        retention_eligible_date__gt=timezone.now(),
        retention_eligible_date__isnull=False,  # Exclude indefinite retention
        is_artifact_deleted=False,
    ).select_related("challenge_phase__challenge")

    if upcoming_submissions.exists():
        print_info(
            f"\nUpcoming cleanups (next 14 days): {upcoming_submissions.count()}"
        )

        challenges = {}
        for submission in upcoming_submissions:
            challenge_id = submission.challenge_phase.challenge.pk
            if challenge_id not in challenges:
                challenges[challenge_id] = {
                    "name": submission.challenge_phase.challenge.title,
                    "count": 0,
                    "has_consent": submission.challenge_phase.challenge.retention_policy_consent,
                }
            challenges[challenge_id]["count"] += 1

        for challenge_data in challenges.values():
            consent_status = (
                "✅ 30-day"
                if challenge_data["has_consent"]
                else "❌ Indefinite"
            )
            print_info(
                f"  - {challenge_data['name']}: {challenge_data['count']} submissions ({consent_status})"
            )


def handle_bulk_set_log_retention(
    challenge_ids=None, all_active=False, days=None, dry_run=False
):
    """Set CloudWatch log retention for multiple challenges"""
    if not challenge_ids and not all_active:
        print_error("Must specify either --challenge-ids or --all-active")
        return

    if all_active:
        # Get all active challenges (those with phases that haven't ended)
        active_challenges = Challenge.objects.filter(
            phases__end_date__gt=timezone.now()
        ).distinct()
        challenge_ids = list(active_challenges.values_list("id", flat=True))

    if dry_run:
        print_info("DRY RUN: Would set log retention for challenges:")

        for challenge_id in challenge_ids:
            try:
                challenge = Challenge.objects.get(id=challenge_id)
                print_info(f"  - Challenge {challenge_id}: {challenge.title}")
            except Challenge.DoesNotExist:
                print_info(f"  - Challenge {challenge_id}: NOT FOUND")
        print_success(
            f"✅ DRY RUN COMPLETED: Would set log retention for {len(challenge_ids)} challenges"
        )
        return

    print_info(f"Setting log retention for {len(challenge_ids)} challenges...")

    results = {"success": [], "failed": []}

    for challenge_id in challenge_ids:
        try:
            result = set_cloudwatch_log_retention(challenge_id, days)
            if result.get("success"):
                results["success"].append(
                    {
                        "challenge_id": challenge_id,
                        "retention_days": result.get("retention_days"),
                        "log_group": result.get("log_group"),
                    }
                )
                print_info(
                    f"✅ Challenge {challenge_id}: {result.get('retention_days')} days"
                )
            else:
                results["failed"].append(
                    {
                        "challenge_id": challenge_id,
                        "error": result.get("error"),
                    }
                )
                print_info(
                    f"❌ Challenge {challenge_id}: {result.get('error')}"
                )
        except Exception as e:
            results["failed"].append(
                {
                    "challenge_id": challenge_id,
                    "error": str(e),
                }
            )
            print_info(f"❌ Challenge {challenge_id}: {str(e)}")

    # Summary
    success_count = len(results["success"])
    failed_count = len(results["failed"])

    if success_count > 0:
        print_success(
            f"✅ BULK LOG RETENTION COMPLETED: Successfully set log retention for {success_count} challenges"
        )
    if failed_count > 0:
        print_error(
            f"❌ BULK LOG RETENTION FAILED: Failed to set log retention for {failed_count} challenges"
        )

    summary_text = f"✅ {success_count} successful, ❌ {failed_count} failed"
    if success_count > failed_count:
        print_success(summary_text)
    elif failed_count > success_count:
        print_error(summary_text)
    else:
        print_warning(summary_text)


def handle_generate_report(format_type="json", output=None, challenge_id=None):
    """Generate detailed retention report"""
    print_info("Generating retention report...")

    try:
        report_data = build_retention_report(challenge_id)

        if format_type == "csv":
            report_content = convert_report_to_csv(report_data)
        else:
            report_content = json.dumps(report_data, indent=2, default=str)

        if output:
            with open(output, "w") as f:
                f.write(report_content)
            print_success(
                f"✅ REPORT GENERATED: Retention report saved to '{output}' in {format_type.upper()} format"
            )
        else:
            print_success(
                f"✅ REPORT GENERATED: Retention report output in {format_type.upper()} format:"
            )
            print(report_content)

    except Exception as e:
        print_error(f"Error generating report: {str(e)}")
        logger.exception("Error generating report")


def build_retention_report(challenge_id=None):
    """Build comprehensive retention report data"""
    now = timezone.now()

    # Base query
    challenges_query = Challenge.objects.all()
    if challenge_id:
        challenges_query = challenges_query.filter(id=challenge_id)

    report_data = {
        "generated_at": now.isoformat(),
        "summary": {},
        "challenges": [],
    }

    # Summary statistics
    total_challenges = challenges_query.count()
    total_submissions = Submission.objects.count()
    deleted_submissions = Submission.objects.filter(
        is_artifact_deleted=True
    ).count()
    eligible_submissions = Submission.objects.filter(
        retention_eligible_date__lte=now,
        is_artifact_deleted=False,
    ).count()

    report_data["summary"] = {
        "total_challenges": total_challenges,
        "total_submissions": total_submissions,
        "deleted_submissions": deleted_submissions,
        "eligible_for_cleanup": eligible_submissions,
        "deletion_rate": (
            (deleted_submissions / total_submissions * 100)
            if total_submissions > 0
            else 0
        ),
    }

    # Per-challenge data
    for challenge in challenges_query.select_related("creator"):
        # Get host team name and emails
        host_team = challenge.creator.team_name if challenge.creator else None
        host_emails = None
        if challenge.creator:
            try:
                host_emails = ", ".join(
                    [user.email for user in challenge.creator.members.all()]
                )
            except Exception:
                host_emails = None

        challenge_data = {
            "id": challenge.pk,
            "title": challenge.title,
            "host_team": host_team,
            "host_emails": host_emails,
            "created_at": (
                challenge.created_at.isoformat()
                if challenge.created_at
                else None
            ),
            "retention_consent": {
                "has_consent": challenge.retention_policy_consent,
                "consent_date": (
                    challenge.retention_policy_consent_date.isoformat()
                    if challenge.retention_policy_consent_date
                    else None
                ),
                "consent_by": (
                    challenge.retention_policy_consent_by.username
                    if challenge.retention_policy_consent_by
                    else None
                ),
                "notes": challenge.retention_policy_notes,
                "retention_policy": (
                    "30-day"
                    if challenge.retention_policy_consent
                    else "indefinite"
                ),
            },
            "admin_override": {
                "log_retention_days_override": challenge.log_retention_days_override,
            },
            "phases": [],
            "submissions": {
                "total": 0,
                "deleted": 0,
                "eligible": 0,
            },
        }

        # Phase data
        for phase in challenge.challengephase_set.all():
            phase_data = {
                "id": phase.pk,
                "name": phase.name,
                "start_date": (
                    phase.start_date.isoformat() if phase.start_date else None
                ),
                "end_date": (
                    phase.end_date.isoformat() if phase.end_date else None
                ),
                "is_public": phase.is_public,
                "retention_eligible_date": None,
            }

            # Calculate retention date using consent-aware calculation
            if phase.end_date and not phase.is_public:
                retention_days = calculate_retention_period_days(
                    phase.end_date, challenge
                )
                retention_date = phase.end_date + timedelta(
                    days=retention_days
                )
                phase_data["retention_eligible_date"] = (
                    retention_date.isoformat()
                )

            challenge_data["phases"].append(phase_data)

        # Submission data for this challenge
        challenge_submissions = Submission.objects.filter(
            challenge_phase__challenge=challenge
        )
        challenge_data["submissions"]["total"] = challenge_submissions.count()
        challenge_data["submissions"]["deleted"] = (
            challenge_submissions.filter(is_artifact_deleted=True).count()
        )
        challenge_data["submissions"]["eligible"] = (
            challenge_submissions.filter(
                retention_eligible_date__lte=now,
                retention_eligible_date__isnull=False,  # Exclude indefinite retention
                is_artifact_deleted=False,
            ).count()
        )

        report_data["challenges"].append(challenge_data)

    return report_data


def convert_report_to_csv(report_data):
    """Convert report data to CSV format"""
    output = StringIO()
    writer = csv.writer(output)

    # Write summary
    writer.writerow(["SUMMARY"])
    writer.writerow(["Metric", "Value"])
    for key, value in report_data["summary"].items():
        writer.writerow([key.replace("_", " ").title(), value])

    writer.writerow([])
    writer.writerow(["CHALLENGES"])
    writer.writerow(
        [
            "Challenge ID",
            "Title",
            "Host Team",
            "Host Emails",
            "Has Consent",
            "Consent Date",
            "Consent By",
            "Retention Policy",
            "Admin Override",
            "Total Submissions",
            "Deleted Submissions",
            "Eligible for Cleanup",
        ]
    )

    for challenge in report_data["challenges"]:
        writer.writerow(
            [
                challenge["id"],
                challenge["title"],
                challenge["host_team"] or "",
                challenge["host_emails"] or "",
                (
                    "Yes"
                    if challenge["retention_consent"]["has_consent"]
                    else "No"
                ),
                challenge["retention_consent"]["consent_date"] or "",
                challenge["retention_consent"]["consent_by"] or "",
                challenge["retention_consent"]["retention_policy"],
                (
                    str(
                        challenge["admin_override"][
                            "log_retention_days_override"
                        ]
                    )
                    if challenge["admin_override"][
                        "log_retention_days_override"
                    ]
                    else ""
                ),
                challenge["submissions"]["total"],
                challenge["submissions"]["deleted"],
                challenge["submissions"]["eligible"],
            ]
        )

    return output.getvalue()


def handle_storage_usage(challenge_id=None, top=10):
    """Show storage usage by challenge/phase"""
    if challenge_id:
        show_challenge_storage_usage(challenge_id)
    else:
        show_top_storage_usage(top)


def show_challenge_storage_usage(challenge_id):
    """Show storage usage for a specific challenge"""
    try:
        challenge = Challenge.objects.get(id=challenge_id)
    except Challenge.DoesNotExist:
        print_error(f"Challenge {challenge_id} does not exist")
        return

    print_info(f"Storage usage for challenge: {challenge.title}")
    print_info("=" * 50)

    # Get submission file sizes (approximate)
    submissions = Submission.objects.filter(
        challenge_phase__challenge=challenge
    ).select_related("challenge_phase")

    total_size = 0
    phase_breakdown = {}

    for submission in submissions:
        # Estimate file size (this is approximate since we don't store actual sizes)
        estimated_size = 100 * 1024  # 100KB per submission as estimate
        total_size += estimated_size

        phase_name = submission.challenge_phase.name
        if phase_name not in phase_breakdown:
            phase_breakdown[phase_name] = {
                "submissions": 0,
                "size": 0,
            }
        phase_breakdown[phase_name]["submissions"] += 1
        phase_breakdown[phase_name]["size"] += estimated_size

    print_info(f"Total estimated storage: {format_bytes(total_size)}")
    print_info(f"Total submissions: {submissions.count()}")
    print_success(
        f"✅ STORAGE ANALYSIS COMPLETED: Analyzed storage usage for challenge '{challenge.title}' (ID: {challenge_id})"
    )

    if phase_breakdown:
        print_info("Breakdown by phase:")
        for phase_name, data in phase_breakdown.items():
            print_info(
                f"  {phase_name}: {data['submissions']} submissions, {format_bytes(data['size'])}"
            )


def show_top_storage_usage(top_n):
    """Show top N challenges by storage usage"""
    print_info(f"Top {top_n} challenges by estimated storage usage:")
    print_info("=" * 60)

    # Get challenges with submission counts
    challenges = (
        Challenge.objects.annotate(
            submission_count=Count("challengephase__submissions")
        )
        .filter(submission_count__gt=0)
        .order_by("-submission_count")[:top_n]
    )

    print_info(
        f"{'Rank':<4} {'Challenge ID':<12} {'Submissions':<12} {'Est. Storage':<15} {'Title'}"
    )
    print_info("-" * 80)

    for rank, challenge in enumerate(challenges, 1):
        estimated_storage = (
            challenge.submission_count * 100 * 1024
        )  # 100KB per submission
        print_info(
            f"{rank:<4} {challenge.pk:<12} {challenge.submission_count:<12} {format_bytes(estimated_storage):<15} {challenge.title[:40]}"
        )

    print_success(
        f"✅ STORAGE ANALYSIS COMPLETED: Analyzed top {top_n} challenges by storage usage"
    )


def format_bytes(bytes_value):
    """Format bytes into human readable format"""
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"


def handle_check_health(verbose=False):
    """Check retention system health"""
    print_info("Retention System Health Check")
    print_info("=" * 30)

    health_status = {
        "overall": "HEALTHY",
        "issues": [],
        "warnings": [],
    }

    # Check 1: Database connectivity
    try:
        Submission.objects.count()
        health_status["database"] = "OK"
    except Exception as e:
        health_status["database"] = "ERROR"
        health_status["issues"].append(f"Database connectivity: {str(e)}")
        health_status["overall"] = "UNHEALTHY"

    # Check 2: Orphaned submissions
    orphaned_submissions = Submission.objects.filter(
        challenge_phase__isnull=True
    ).count()
    if orphaned_submissions > 0:
        health_status["warnings"].append(
            f"Found {orphaned_submissions} submissions without challenge phases"
        )

    # Check 3: Submissions with missing retention dates (excluding indefinite retention)
    # Only count submissions that should have retention dates but don't
    missing_retention_dates = Submission.objects.filter(
        retention_eligible_date__isnull=True,
        is_artifact_deleted=False,
        challenge_phase__end_date__isnull=False,  # Has end date
        challenge_phase__is_public=False,  # Phase is not public
        challenge_phase__challenge__retention_policy_consent=True,  # Has consent
    ).count()
    if missing_retention_dates > 0:
        health_status["warnings"].append(
            f"Found {missing_retention_dates} submissions without retention dates (should have 30-day retention)"
        )

    # Check 4: Recent errors (if verbose)
    if verbose:
        health_status["recent_errors"] = "No recent errors found"

    # Display results
    print_info(f"Overall Status: {health_status['overall']}")
    print_info(f"Database: {health_status.get('database', 'UNKNOWN')}")

    if health_status["issues"]:
        print_info("Issues:")
        for issue in health_status["issues"]:
            print_error(f"  ✗ {issue}")

    if health_status["warnings"]:
        print_info("Warnings:")
        for warning in health_status["warnings"]:
            print_warning(f"  ⚠ {warning}")

    if verbose and "recent_errors" in health_status:
        print_info(f"Recent Errors: {health_status['recent_errors']}")

    # Final success message
    if health_status["overall"] == "HEALTHY":
        print_success("✅ HEALTH CHECK COMPLETED: Retention system is healthy")
    else:
        print_error(
            f"❌ HEALTH CHECK COMPLETED: Retention system has issues - {len(health_status['issues'])} issues found"
        )


def handle_extend_retention(challenge_id, days, confirm=False):
    """Extend retention for specific challenges"""
    try:
        challenge = Challenge.objects.get(id=challenge_id)
    except Challenge.DoesNotExist:
        print_error(f"Challenge {challenge_id} does not exist")
        return

    # Get current retention period
    phases = ChallengePhase.objects.filter(challenge=challenge)
    if not phases.exists():
        print_error(f"No phases found for challenge {challenge_id}")
        return

    latest_end_date = max(phase.end_date for phase in phases if phase.end_date)
    current_retention_days = calculate_retention_period_days(
        latest_end_date, challenge
    )
    new_retention_days = current_retention_days + days

    print_info(f"Challenge: {challenge.title}")
    print_info(f"Current retention: {current_retention_days} days")
    print_info(f"New retention: {new_retention_days} days")
    print_info(f"Extension: +{days} days")

    if not confirm:
        confirm_input = input("\nProceed with extension? (yes/no): ")
        if confirm_input.lower() != "yes":
            print_info("Extension cancelled.")
            return

    # Set the new retention
    result = set_cloudwatch_log_retention(challenge_id, new_retention_days)

    if result.get("success"):
        print_success(
            f"✅ RETENTION EXTENDED: Successfully extended retention from {current_retention_days} to {result['retention_days']} days for challenge '{challenge.title}' (ID: {challenge_id})"
        )
    else:
        print_error(f"Failed to extend retention: {result.get('error')}")


def handle_emergency_cleanup(challenge_id=None, force=False):
    """Emergency cleanup with bypass of safety checks"""
    print_warning("⚠️  EMERGENCY CLEANUP MODE ⚠️")
    print_info("This will bypass normal safety checks!")

    if challenge_id:
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            print_info(f"Target challenge: {challenge.title}")
        except Challenge.DoesNotExist:
            print_error(f"Challenge {challenge_id} does not exist")
            return
    else:
        print_info("Target: ALL challenges")

    if not force:
        confirm_input = input(
            "\nAre you absolutely sure you want to proceed? Type 'EMERGENCY' to confirm: "
        )
        if confirm_input != "EMERGENCY":
            print_info("Emergency cleanup cancelled.")
            return

    # Perform emergency cleanup
    if challenge_id:
        submissions = Submission.objects.filter(
            challenge_phase__challenge_id=challenge_id,
            is_artifact_deleted=False,
        )
    else:
        submissions = Submission.objects.filter(
            is_artifact_deleted=False,
        )

    print_info(
        f"Found {submissions.count()} submissions for emergency cleanup"
    )

    # Mark all as deleted (this is the emergency bypass)
    deleted_count = submissions.update(is_artifact_deleted=True)

    if challenge_id:
        print_success(
            f"✅ EMERGENCY CLEANUP COMPLETED: Marked {deleted_count} submissions as deleted for challenge '{challenge.title}' (ID: {challenge_id})"
        )
    else:
        print_success(
            f"✅ EMERGENCY CLEANUP COMPLETED: Marked {deleted_count} submissions as deleted across all challenges"
        )


def handle_find_submissions(
    challenge_id=None, phase_id=None, status=None, deleted=False, limit=50
):
    """Find submissions by various criteria"""
    # Build query
    query = Q()

    if challenge_id:
        query &= Q(challenge_phase__challenge_id=challenge_id)

    if phase_id:
        query &= Q(challenge_phase_id=phase_id)

    if status:
        status_map = {
            "pending": "SUBMITTED",
            "running": "RUNNING",
            "completed": "FINISHED",
            "failed": "FAILED",
            "cancelled": "CANCELLED",
        }
        query &= Q(status=status_map.get(status, status))

    if not deleted:
        query &= Q(is_artifact_deleted=False)

    submissions = Submission.objects.filter(query).select_related(
        "challenge_phase__challenge", "participant_team"
    )[:limit]

    print_info(f"Found {submissions.count()} submissions:")
    print_info("-" * 80)

    for submission in submissions:
        challenge_name = submission.challenge_phase.challenge.title
        phase_name = submission.challenge_phase.name
        team_name = (
            submission.participant_team.team_name
            if submission.participant_team
            else "N/A"
        )

        print_info(
            f"ID: {submission.pk:<6} | Challenge: {challenge_name[:30]:<30} | Phase: {phase_name[:15]:<15} | Team: {team_name[:20]:<20} | Status: {submission.status:<10} | Deleted: {submission.is_artifact_deleted}"
        )

    print_success(
        f"✅ SUBMISSION SEARCH COMPLETED: Found {submissions.count()} submissions matching criteria"
    )


def handle_check_consent(challenge_id=None):
    """Check consent status for challenges"""
    if challenge_id:
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            print_info(
                f"Consent status for challenge {challenge_id} ({challenge.title}):"
            )
            print_info(
                f"  Host consent required: {challenge.retention_policy_consent}"
            )
            print_info(
                f"  Host consent given: {challenge.retention_policy_consent}"
            )
            print_info(
                f"  Consent date: {challenge.retention_policy_consent_date}"
            )
            print_success(
                f"✅ CONSENT CHECK COMPLETED: Analyzed consent status for challenge '{challenge.title}' (ID: {challenge_id})"
            )
        except Challenge.DoesNotExist:
            print_error(f"Challenge {challenge_id} does not exist")
    else:
        print_info("Checking retention policy consent status:")
        print_info("=" * 50)

        challenges = Challenge.objects.all().order_by("id")
        consent_stats = {"total": 0, "with_consent": 0, "without_consent": 0}

        for challenge in challenges:
            consent_stats["total"] += 1
            if challenge.retention_policy_consent:
                consent_stats["with_consent"] += 1
                status = "✅ CONSENTED (30-day retention allowed)"
            else:
                consent_stats["without_consent"] += 1
                status = "❌ NO CONSENT (indefinite retention for safety)"

            print_info(
                f"Challenge {challenge.pk}: {challenge.title[:40]:<40} | {status}"
            )

        # Summary
        print_info("\n" + "=" * 50)
        print_info("SUMMARY:")
        print_info(f"Total challenges: {consent_stats['total']}")
        print_info(
            f"With consent (30-day retention allowed): {consent_stats['with_consent']}"
        )
        print_info(
            f"Without consent (indefinite retention for safety): {consent_stats['without_consent']}"
        )

        if consent_stats["without_consent"] > 0:
            print_warning(
                f"⚠️  {consent_stats['without_consent']} challenges need consent for 30-day retention policy!"
            )

        print_success(
            f"✅ CONSENT CHECK COMPLETED: Analyzed consent status for {consent_stats['total']} challenges"
        )


def handle_bulk_consent(challenge_ids, require_consent=True):
    """Bulk consent operations"""
    if not challenge_ids:
        print_error("Must specify challenge IDs for bulk consent operations")
        return

    if require_consent:
        print_info(f"Requiring consent for {len(challenge_ids)} challenges...")
        bulk_require_consent(challenge_ids)
    else:
        print_info(f"Checking consent for {len(challenge_ids)} challenges...")
        bulk_check_consent(challenge_ids)


def bulk_check_consent(challenge_ids):
    """Bulk check consent for multiple challenges"""
    print_info(f"Checking consent status for {len(challenge_ids)} challenges:")
    print_info("=" * 60)

    challenges_needing_consent = []

    for challenge_id in challenge_ids:
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            if challenge.retention_policy_consent:
                status = "✅ CONSENTED"
            else:
                status = "❌ NO CONSENT"
                challenges_needing_consent.append(challenge_id)

            print_info(
                f"Challenge {challenge_id}: {challenge.title[:50]:<50} | {status}"
            )
        except Challenge.DoesNotExist:
            print_info(f"Challenge {challenge_id}: NOT FOUND")

    # Summary
    print_info("\n" + "=" * 60)
    print_info(f"Total checked: {len(challenge_ids)}")
    print_info(f"Need consent: {len(challenges_needing_consent)}")

    if challenges_needing_consent:
        print_warning(
            f"Challenges needing consent: {', '.join(map(str, challenges_needing_consent))}"
        )

    print_success(
        f"✅ BULK CONSENT CHECK COMPLETED: Analyzed consent status for {len(challenge_ids)} challenges"
    )


def bulk_require_consent(challenge_ids):
    """Bulk require consent (show which challenges need consent)"""
    print_warning(
        f"⚠️  BULK CONSENT REQUIREMENT CHECK for {len(challenge_ids)} challenges"
    )
    print_info("=" * 60)

    challenges_needing_consent = []

    for challenge_id in challenge_ids:
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            if not challenge.retention_policy_consent:
                challenges_needing_consent.append(challenge_id)
                print_info(
                    f"❌ Challenge {challenge_id}: {challenge.title} - NEEDS CONSENT"
                )
            else:
                print_info(
                    f"✅ Challenge {challenge_id}: {challenge.title} - HAS CONSENT"
                )
        except Challenge.DoesNotExist:
            print_info(f"Challenge {challenge_id}: NOT FOUND")

    # Summary
    print_info("\n" + "=" * 60)
    print_info(f"Total challenges: {len(challenge_ids)}")
    print_info(f"Need consent: {len(challenges_needing_consent)}")

    if challenges_needing_consent:
        print_error(
            f"⚠️  URGENT: {len(challenges_needing_consent)} challenges require consent!"
        )
        print_info(
            "Use 'docker-compose exec django python manage.py shell < scripts/manage_retention.py record-consent <challenge_id> --username <host_username>' to record consent for each challenge."
        )
    else:
        print_success("🎉 All challenges have consent!")

    print_success(
        f"✅ BULK CONSENT REQUIREMENT CHECK COMPLETED: Analyzed {len(challenge_ids)} challenges"
    )


def handle_recent_consent_changes():
    """Show recent consent changes"""
    print_info("Recent retention consent changes:")
    print_info("=" * 50)

    # Get challenges with consent changes in the last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)

    recent_consents = Challenge.objects.filter(
        retention_policy_consent=True,
        retention_policy_consent_date__gte=thirty_days_ago,
    ).order_by("-retention_policy_consent_date")

    if not recent_consents.exists():
        print_warning("No recent consent changes found in the last 30 days.")
        print_success(
            "✅ RECENT CONSENT CHANGES CHECK COMPLETED: No consent changes found in the last 30 days"
        )
        return

    print_info(
        f"Found {recent_consents.count()} consent changes in the last 30 days:"
    )
    print_info("")

    for challenge in recent_consents:
        consent_date = challenge.retention_policy_consent_date.strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        consent_by = (
            challenge.retention_policy_consent_by.username
            if challenge.retention_policy_consent_by
            else "Unknown"
        )

        print_info(
            f"✅ {consent_date} | Challenge {challenge.pk}: {challenge.title[:50]}"
        )
        print_info(f"   Consent by: {consent_by}")
        if challenge.retention_policy_notes:
            print_info(f"   Notes: {challenge.retention_policy_notes}")
        print_info("")

    # Show summary
    print_info("=" * 50)
    print_info("SUMMARY:")
    print_info(f"Total recent consents: {recent_consents.count()}")

    # Show by user
    user_consents = {}
    for challenge in recent_consents:
        user = (
            challenge.retention_policy_consent_by.username
            if challenge.retention_policy_consent_by
            else "Unknown"
        )
        if user not in user_consents:
            user_consents[user] = 0
        user_consents[user] += 1

    if user_consents:
        print_info("Consents by user:")
        for user, count in sorted(
            user_consents.items(), key=lambda x: x[1], reverse=True
        ):
            print_info(f"  {user}: {count} consent(s)")

    print_success(
        f"✅ RECENT CONSENT CHANGES CHECK COMPLETED: Found {recent_consents.count()} consent changes in the last 30 days"
    )


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print_error(
            "Usage: docker-compose exec django python scripts/manage_retention.py <action> [options]"
        )
        print_info("Available actions:")
        print_info("  cleanup [--dry-run]")
        print_info("  update-dates")
        print_info("  send-warnings")
        print_info("  set-log-retention <challenge_id> [--days <days>]")
        print_info("  force-delete <submission_id> [--confirm]")
        print_info("  status [--challenge-id <challenge_id>]")
        print_info(
            "  bulk-set-log-retention [--challenge-ids <ids>] [--all-active] [--days <days>] [--dry-run]"
        )
        print_info(
            "  generate-report [--format json|csv] [--output <file>] [--challenge-id <challenge_id>]"
        )
        print_info(
            "  storage-usage [--challenge-id <challenge_id>] [--top <n>]"
        )
        print_info("  check-health [--verbose]")
        print_info(
            "  extend-retention <challenge_id> --days <days> [--confirm]"
        )
        print_info(
            "  emergency-cleanup [--challenge-id <challenge_id>] [--force]"
        )
        print_info(
            "  find-submissions [--challenge-id <challenge_id>] [--phase-id <phase_id>] [--status <status>] [--deleted] [--limit <n>]"
        )
        print_info("  check-consent [--challenge-id <challenge_id>]")
        print_info(
            "  bulk-consent [--challenge-ids <ids>] [--require-consent]"
        )
        print_info("  recent-consent-changes")
        return

    action = sys.argv[1]

    try:
        if action == "cleanup":
            dry_run = "--dry-run" in sys.argv
            handle_cleanup(dry_run)

        elif action == "update-dates":
            handle_update_dates()

        elif action == "send-warnings":
            handle_send_warnings()

        elif action == "set-log-retention":
            if len(sys.argv) < 3:
                print_error("Challenge ID required for set-log-retention")
                return
            challenge_id = int(sys.argv[2])
            days = None
            if "--days" in sys.argv:
                days_index = sys.argv.index("--days")
                if days_index + 1 < len(sys.argv):
                    days = int(sys.argv[days_index + 1])
            handle_set_log_retention(challenge_id, days)

        elif action == "force-delete":
            if len(sys.argv) < 3:
                print_error("Submission ID required for force-delete")
                return
            submission_id = int(sys.argv[2])
            confirm = "--confirm" in sys.argv
            handle_force_delete(submission_id, confirm)

        elif action == "status":
            challenge_id = None
            if "--challenge-id" in sys.argv:
                challenge_id_index = sys.argv.index("--challenge-id")
                if challenge_id_index + 1 < len(sys.argv):
                    challenge_id = int(sys.argv[challenge_id_index + 1])
            handle_status(challenge_id)

        elif action == "bulk-set-log-retention":
            challenge_ids = None
            all_active = "--all-active" in sys.argv
            days = None
            dry_run = "--dry-run" in sys.argv

            if "--challenge-ids" in sys.argv:
                challenge_ids_index = sys.argv.index("--challenge-ids")
                challenge_ids = []
                i = challenge_ids_index + 1
                while i < len(sys.argv) and sys.argv[i].isdigit():
                    challenge_ids.append(int(sys.argv[i]))
                    i += 1

            if "--days" in sys.argv:
                days_index = sys.argv.index("--days")
                if days_index + 1 < len(sys.argv):
                    days = int(sys.argv[days_index + 1])

            handle_bulk_set_log_retention(
                challenge_ids, all_active, days, dry_run
            )

        elif action == "generate-report":
            format_type = "json"
            output = None
            challenge_id = None

            if "--format" in sys.argv:
                format_index = sys.argv.index("--format")
                if format_index + 1 < len(sys.argv):
                    format_type = sys.argv[format_index + 1]

            if "--output" in sys.argv:
                output_index = sys.argv.index("--output")
                if output_index + 1 < len(sys.argv):
                    output = sys.argv[output_index + 1]

            if "--challenge-id" in sys.argv:
                challenge_id_index = sys.argv.index("--challenge-id")
                if challenge_id_index + 1 < len(sys.argv):
                    challenge_id = int(sys.argv[challenge_id_index + 1])

            handle_generate_report(format_type, output, challenge_id)

        elif action == "storage-usage":
            challenge_id = None
            top = 10

            if "--challenge-id" in sys.argv:
                challenge_id_index = sys.argv.index("--challenge-id")
                if challenge_id_index + 1 < len(sys.argv):
                    challenge_id = int(sys.argv[challenge_id_index + 1])

            if "--top" in sys.argv:
                top_index = sys.argv.index("--top")
                if top_index + 1 < len(sys.argv):
                    top = int(sys.argv[top_index + 1])

            handle_storage_usage(challenge_id, top)

        elif action == "check-health":
            verbose = "--verbose" in sys.argv
            handle_check_health(verbose)

        elif action == "extend-retention":
            if len(sys.argv) < 3:
                print_error("Challenge ID required for extend-retention")
                return
            challenge_id = int(sys.argv[2])
            days = None
            confirm = "--confirm" in sys.argv

            if "--days" in sys.argv:
                days_index = sys.argv.index("--days")
                if days_index + 1 < len(sys.argv):
                    days = int(sys.argv[days_index + 1])

            if days is None:
                print_error("Days required for extend-retention")
                return

            handle_extend_retention(challenge_id, days, confirm)

        elif action == "emergency-cleanup":
            challenge_id = None
            force = "--force" in sys.argv

            if "--challenge-id" in sys.argv:
                challenge_id_index = sys.argv.index("--challenge-id")
                if challenge_id_index + 1 < len(sys.argv):
                    challenge_id = int(sys.argv[challenge_id_index + 1])

            handle_emergency_cleanup(challenge_id, force)

        elif action == "find-submissions":
            challenge_id = None
            phase_id = None
            status = None
            deleted = "--deleted" in sys.argv
            limit = 50

            if "--challenge-id" in sys.argv:
                challenge_id_index = sys.argv.index("--challenge-id")
                if challenge_id_index + 1 < len(sys.argv):
                    challenge_id = int(sys.argv[challenge_id_index + 1])

            if "--phase-id" in sys.argv:
                phase_id_index = sys.argv.index("--phase-id")
                if phase_id_index + 1 < len(sys.argv):
                    phase_id = int(sys.argv[phase_id_index + 1])

            if "--status" in sys.argv:
                status_index = sys.argv.index("--status")
                if status_index + 1 < len(sys.argv):
                    status = sys.argv[status_index + 1]

            if "--limit" in sys.argv:
                limit_index = sys.argv.index("--limit")
                if limit_index + 1 < len(sys.argv):
                    limit = int(sys.argv[limit_index + 1])

            handle_find_submissions(
                challenge_id, phase_id, status, deleted, limit
            )

        elif action == "check-consent":
            challenge_id = None
            if "--challenge-id" in sys.argv:
                challenge_id_index = sys.argv.index("--challenge-id")
                if challenge_id_index + 1 < len(sys.argv):
                    challenge_id = int(sys.argv[challenge_id_index + 1])
            handle_check_consent(challenge_id)

        elif action == "bulk-consent":
            challenge_ids = []
            require_consent = "--require-consent" in sys.argv

            if "--challenge-ids" in sys.argv:
                challenge_ids_index = sys.argv.index("--challenge-ids")
                i = challenge_ids_index + 1
                while i < len(sys.argv) and sys.argv[i].isdigit():
                    challenge_ids.append(int(sys.argv[i]))
                    i += 1

            if not challenge_ids:
                print_error("Challenge IDs required for bulk-consent")
                return

            handle_bulk_consent(challenge_ids, require_consent)

        elif action == "recent-consent-changes":
            handle_recent_consent_changes()

        else:
            print_error(f"Unknown action: {action}")
            print_info("Run without arguments to see available actions")

    except Exception as e:
        print_error(f"Error executing action '{action}': {str(e)}")
        logger.exception(f"Error executing action '{action}'")


if __name__ == "__main__":
    main()
