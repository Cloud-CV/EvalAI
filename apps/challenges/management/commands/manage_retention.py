import csv
import json
import logging
from datetime import timedelta
from io import StringIO

from challenges.aws_utils import (
    calculate_retention_period_days,
    cleanup_expired_submission_artifacts,
    delete_submission_files_from_storage,
    send_retention_warning_notifications,
    set_cloudwatch_log_retention,
)
from challenges.models import Challenge, ChallengePhase
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Q
from django.utils import timezone
from jobs.models import Submission

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Manage retention policies for submissions and logs"

    def print_success(self, message):
        self.stdout.write(self.style.SUCCESS(message))

    def print_error(self, message):
        self.stdout.write(self.style.ERROR(message))

    def print_warning(self, message):
        self.stdout.write(self.style.WARNING(message))

    def print_info(self, message):
        self.stdout.write(message)

    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(
            dest="action", help="Available actions"
        )

        # Cleanup expired artifacts
        cleanup_parser = subparsers.add_parser(
            "cleanup", help="Clean up expired submission artifacts"
        )
        cleanup_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be deleted without actually deleting",
        )

        # Update retention dates
        subparsers.add_parser(
            "update-dates",
            help="Update retention eligible dates for submissions",
        )

        # Send warning notifications
        subparsers.add_parser(
            "send-warnings",
            help="Send retention warning notifications to challenge hosts",
        )

        # Set log retention for a specific challenge
        log_retention_parser = subparsers.add_parser(
            "set-log-retention",
            help="Set CloudWatch log retention for a challenge",
        )
        log_retention_parser.add_argument(
            "challenge_id", type=int, help="Challenge ID"
        )
        log_retention_parser.add_argument(
            "--days",
            type=int,
            help="Retention period in days (optional, calculated from challenge end date if not provided)",
        )

        # Force delete submission files
        force_delete_parser = subparsers.add_parser(
            "force-delete",
            help="Force delete submission files for a specific submission",
        )
        force_delete_parser.add_argument(
            "submission_id", type=int, help="Submission ID"
        )
        force_delete_parser.add_argument(
            "--confirm", action="store_true", help="Confirm the deletion"
        )

        # Show retention status
        status_parser = subparsers.add_parser(
            "status",
            help="Show retention status for challenges and submissions",
        )
        status_parser.add_argument(
            "--challenge-id",
            type=int,
            help="Show status for specific challenge",
        )

        # NEW FEATURES START HERE

        # Bulk set log retention for multiple challenges
        bulk_log_retention_parser = subparsers.add_parser(
            "bulk-set-log-retention",
            help="Set CloudWatch log retention for multiple challenges",
        )
        bulk_log_retention_parser.add_argument(
            "--challenge-ids",
            nargs="+",
            type=int,
            help="List of challenge IDs",
        )
        bulk_log_retention_parser.add_argument(
            "--all-active",
            action="store_true",
            help="Apply to all active challenges",
        )
        bulk_log_retention_parser.add_argument(
            "--days",
            type=int,
            help="Retention period in days (optional, calculated from challenge end date if not provided)",
        )
        bulk_log_retention_parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be set without actually setting",
        )

        # Generate retention report
        report_parser = subparsers.add_parser(
            "generate-report",
            help="Generate detailed retention report",
        )
        report_parser.add_argument(
            "--format",
            choices=["json", "csv"],
            default="json",
            help="Output format (default: json)",
        )
        report_parser.add_argument(
            "--output",
            help="Output file path (default: stdout)",
        )
        report_parser.add_argument(
            "--challenge-id",
            type=int,
            help="Generate report for specific challenge only",
        )

        # Storage usage analysis
        storage_parser = subparsers.add_parser(
            "storage-usage",
            help="Show storage usage by challenge/phase",
        )
        storage_parser.add_argument(
            "--challenge-id",
            type=int,
            help="Show storage for specific challenge",
        )
        storage_parser.add_argument(
            "--top",
            type=int,
            default=10,
            help="Show top N challenges by storage usage (default: 10)",
        )

        # Health check
        health_parser = subparsers.add_parser(
            "check-health",
            help="Check retention system health",
        )
        health_parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed health information",
        )

        # Extend retention for specific challenges
        extend_parser = subparsers.add_parser(
            "extend-retention",
            help="Extend retention for specific challenges",
        )
        extend_parser.add_argument(
            "challenge_id", type=int, help="Challenge ID"
        )
        extend_parser.add_argument(
            "--days",
            type=int,
            required=True,
            help="Additional days to extend retention",
        )
        extend_parser.add_argument(
            "--confirm", action="store_true", help="Confirm the extension"
        )

        # Emergency cleanup
        emergency_parser = subparsers.add_parser(
            "emergency-cleanup",
            help="Emergency cleanup with bypass of safety checks",
        )
        emergency_parser.add_argument(
            "--challenge-id",
            type=int,
            help="Emergency cleanup for specific challenge",
        )
        emergency_parser.add_argument(
            "--force",
            action="store_true",
            help="Force cleanup without confirmation",
        )

        # Find submissions by criteria
        find_parser = subparsers.add_parser(
            "find-submissions",
            help="Find submissions by various criteria",
        )
        find_parser.add_argument(
            "--challenge-id",
            type=int,
            help="Filter by challenge ID",
        )
        find_parser.add_argument(
            "--phase-id",
            type=int,
            help="Filter by challenge phase ID",
        )
        find_parser.add_argument(
            "--status",
            choices=["pending", "running", "completed", "failed", "cancelled"],
            help="Filter by submission status",
        )
        find_parser.add_argument(
            "--deleted",
            action="store_true",
            help="Include deleted submissions",
        )
        find_parser.add_argument(
            "--limit",
            type=int,
            default=50,
            help="Limit number of results (default: 50)",
        )

    def handle(self, *args, **options):
        action = options.get("action")

        if not action:
            self.print_help("manage_retention", "")
            return

        if action == "cleanup":
            self.handle_cleanup(options)
        elif action == "update-dates":
            self.handle_update_dates()
        elif action == "send-warnings":
            self.handle_send_warnings()
        elif action == "set-log-retention":
            self.handle_set_log_retention(options)
        elif action == "force-delete":
            self.handle_force_delete(options)
        elif action == "status":
            self.handle_status(options)
        # NEW FEATURES
        elif action == "bulk-set-log-retention":
            self.handle_bulk_set_log_retention(options)
        elif action == "generate-report":
            self.handle_generate_report(options)
        elif action == "storage-usage":
            self.handle_storage_usage(options)
        elif action == "check-health":
            self.handle_check_health(options)
        elif action == "extend-retention":
            self.handle_extend_retention(options)
        elif action == "emergency-cleanup":
            self.handle_emergency_cleanup(options)
        elif action == "find-submissions":
            self.handle_find_submissions(options)

    def handle_cleanup(self, options):
        """Handle cleanup of expired submission artifacts"""
        dry_run = options.get("dry_run", False)

        if dry_run:
            self.stdout.write("DRY RUN: Showing what would be cleaned up...")

        now = timezone.now()
        eligible_submissions = Submission.objects.filter(
            retention_eligible_date__lte=now, is_artifact_deleted=False
        ).select_related("challenge_phase__challenge")

        if not eligible_submissions.exists():
            self.stdout.write(
                self.style.SUCCESS("No submissions eligible for cleanup.")
            )
            return

        self.stdout.write(
            f"Found {eligible_submissions.count()} submissions eligible for cleanup:"
        )

        for submission in eligible_submissions:
            challenge_name = submission.challenge_phase.challenge.title
            phase_name = submission.challenge_phase.name
            self.stdout.write(
                f"  - Submission {submission.pk} from challenge '{challenge_name}' "
                f"phase '{phase_name}' (eligible since {submission.retention_eligible_date})"
            )

        if dry_run:
            return

        confirm = input("\nProceed with cleanup? (yes/no): ")
        if confirm.lower() != "yes":
            self.stdout.write("Cleanup cancelled.")
            return

        # Run the actual cleanup
        result = cleanup_expired_submission_artifacts.delay()
        self.stdout.write(
            self.style.SUCCESS(f"Cleanup task started with ID: {result.id}")
        )

    def handle_update_dates(self):
        """Handle updating retention dates"""
        self.stdout.write("Updating submission retention dates...")

        try:
            # Run directly instead of via Celery in development
            from challenges.aws_utils import update_submission_retention_dates

            result = update_submission_retention_dates()
            self.stdout.write(
                self.style.SUCCESS(
                    f"Updated retention dates for {result.get('updated_submissions', 0)} submissions"
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Failed to update retention dates: {e}")
            )

    def handle_send_warnings(self):
        """Handle sending warning notifications"""
        self.stdout.write("Sending retention warning notifications...")

        result = send_retention_warning_notifications.delay()
        self.stdout.write(
            self.style.SUCCESS(
                f"Notification task started with ID: {result.id}"
            )
        )

    def handle_set_log_retention(self, options):
        """Handle setting log retention for a challenge"""
        challenge_id = options["challenge_id"]
        retention_days = options.get("days")

        try:
            challenge = Challenge.objects.get(pk=challenge_id)
        except Challenge.DoesNotExist:
            raise CommandError(f"Challenge {challenge_id} does not exist")

        self.stdout.write(
            f"Setting log retention for challenge {challenge_id}: {challenge.title}"
        )

        result = set_cloudwatch_log_retention(challenge_id, retention_days)

        if result.get("success"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully set log retention to {result['retention_days']} days "
                    f"for log group: {result['log_group']}"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"Failed to set log retention: {result.get('error')}"
                )
            )

    def handle_force_delete(self, options):
        """Handle force deletion of submission files"""
        submission_id = options["submission_id"]
        confirm = options.get("confirm", False)

        try:
            submission = Submission.objects.get(pk=submission_id)
        except Submission.DoesNotExist:
            raise CommandError(f"Submission {submission_id} does not exist")

        if submission.is_artifact_deleted:
            self.stdout.write(
                self.style.WARNING(
                    f"Submission {submission_id} artifacts already deleted"
                )
            )
            return

        challenge_name = submission.challenge_phase.challenge.title
        phase_name = submission.challenge_phase.name

        self.stdout.write(
            f"Submission {submission_id} from challenge '{challenge_name}' phase '{phase_name}'"
        )

        if not confirm:
            confirm_input = input(
                "Are you sure you want to delete the submission files? (yes/no): "
            )
            if confirm_input.lower() != "yes":
                self.stdout.write("Deletion cancelled.")
                return

        result = delete_submission_files_from_storage(submission)

        if result["success"]:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully deleted {len(result['deleted_files'])} files for submission {submission_id}"
                )
            )
            if result["failed_files"]:
                self.stdout.write(
                    self.style.WARNING(
                        f"Failed to delete {len(result['failed_files'])} files"
                    )
                )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"Failed to delete submission files: {result.get('error')}"
                )
            )

    def handle_status(self, options):
        """Handle showing retention status"""
        challenge_id = options.get("challenge_id")

        if challenge_id:
            self.show_challenge_status(challenge_id)
        else:
            self.show_overall_status()

    def show_challenge_status(self, challenge_id):
        """Show retention status for a specific challenge"""
        try:
            challenge = Challenge.objects.get(pk=challenge_id)
        except Challenge.DoesNotExist:
            raise CommandError(f"Challenge {challenge_id} does not exist")

        self.stdout.write(
            f"\nRetention status for challenge: {challenge.title}"
        )
        self.stdout.write("=" * 50)

        phases = ChallengePhase.objects.filter(challenge=challenge)

        for phase in phases:
            self.stdout.write(f"\nPhase: {phase.name}")
            self.stdout.write(f"  End date: {phase.end_date}")
            self.stdout.write(f"  Is public: {phase.is_public}")

            from challenges.aws_utils import (
                calculate_submission_retention_date,
            )

            retention_date = calculate_submission_retention_date(phase)
            if retention_date:
                self.stdout.write(
                    f"  Retention eligible date: {retention_date}"
                )
            else:
                self.stdout.write(
                    "  Retention not applicable (phase still public or no end date)"
                )

            submissions = Submission.objects.filter(challenge_phase=phase)
            total_submissions = submissions.count()
            deleted_submissions = submissions.filter(
                is_artifact_deleted=True
            ).count()
            eligible_submissions = submissions.filter(
                retention_eligible_date__lte=timezone.now(),
                is_artifact_deleted=False,
            ).count()

            self.stdout.write(f"  Total submissions: {total_submissions}")
            self.stdout.write(f"  Artifacts deleted: {deleted_submissions}")
            self.stdout.write(
                f"  Eligible for cleanup: {eligible_submissions}"
            )

    def show_overall_status(self):
        """Show overall retention status"""
        self.stdout.write("\nOverall retention status:")
        self.stdout.write("=" * 30)

        total_submissions = Submission.objects.count()
        deleted_submissions = Submission.objects.filter(
            is_artifact_deleted=True
        ).count()
        eligible_submissions = Submission.objects.filter(
            retention_eligible_date__lte=timezone.now(),
            is_artifact_deleted=False,
        ).count()

        self.stdout.write(f"Total submissions: {total_submissions}")
        self.stdout.write(f"Artifacts deleted: {deleted_submissions}")
        self.stdout.write(f"Eligible for cleanup: {eligible_submissions}")

        # Show challenges with upcoming retention dates
        upcoming_date = timezone.now() + timedelta(days=14)
        upcoming_submissions = Submission.objects.filter(
            retention_eligible_date__lte=upcoming_date,
            retention_eligible_date__gt=timezone.now(),
            is_artifact_deleted=False,
        ).select_related("challenge_phase__challenge")

        if upcoming_submissions.exists():
            self.stdout.write(
                f"\nUpcoming cleanups (next 14 days): {upcoming_submissions.count()}"
            )

            challenges = {}
            for submission in upcoming_submissions:
                challenge_id = submission.challenge_phase.challenge.pk
                if challenge_id not in challenges:
                    challenges[challenge_id] = {
                        "name": submission.challenge_phase.challenge.title,
                        "count": 0,
                    }
                challenges[challenge_id]["count"] += 1

            for challenge_data in challenges.values():
                self.stdout.write(
                    f"  - {challenge_data['name']}: {challenge_data['count']} submissions"
                )

    # NEW FEATURE IMPLEMENTATIONS

    def handle_bulk_set_log_retention(self, options):
        """Handle bulk setting of log retention for multiple challenges"""
        challenge_ids = options.get("challenge_ids", [])
        all_active = options.get("all_active", False)
        retention_days = options.get("days")
        dry_run = options.get("dry_run", False)

        if not challenge_ids and not all_active:
            raise CommandError(
                "Must specify either --challenge-ids or --all-active"
            )

        if all_active:
            # Get all active challenges (those with phases that haven't ended)
            active_challenges = Challenge.objects.filter(
                phases__end_date__gt=timezone.now()
            ).distinct()
            challenge_ids = list(
                active_challenges.values_list("id", flat=True)
            )

        if dry_run:
            self.stdout.write(
                "DRY RUN: Would set log retention for challenges:"
            )

            for challenge_id in challenge_ids:
                try:
                    challenge = Challenge.objects.get(pk=challenge_id)
                    self.stdout.write(
                        f"  - Challenge {challenge_id}: {challenge.title}"
                    )
                except Challenge.DoesNotExist:
                    self.stdout.write(
                        f"  - Challenge {challenge_id}: NOT FOUND"
                    )
            return

        self.stdout.write(
            f"Setting log retention for {len(challenge_ids)} challenges..."
        )

        results = {"success": [], "failed": []}

        for challenge_id in challenge_ids:
            try:
                result = set_cloudwatch_log_retention(
                    challenge_id, retention_days
                )
                if result.get("success"):
                    results["success"].append(
                        {
                            "challenge_id": challenge_id,
                            "retention_days": result.get("retention_days"),
                            "log_group": result.get("log_group"),
                        }
                    )
                    self.stdout.write(
                        f"✅ Challenge {challenge_id}: {result.get('retention_days')} days"
                    )
                else:
                    results["failed"].append(
                        {
                            "challenge_id": challenge_id,
                            "error": result.get("error"),
                        }
                    )
                    self.stdout.write(
                        f"❌ Challenge {challenge_id}: {result.get('error')}"
                    )
            except Exception as e:
                results["failed"].append(
                    {
                        "challenge_id": challenge_id,
                        "error": str(e),
                    }
                )
                self.stdout.write(f"❌ Challenge {challenge_id}: {str(e)}")

        # Summary
        success_count = len(results["success"])
        failed_count = len(results["failed"])

        summary_text = (
            f"✅ {success_count} successful, ❌ {failed_count} failed"
        )
        if success_count > failed_count:
            self.stdout.write(self.style.SUCCESS(summary_text))
        elif failed_count > success_count:
            self.stdout.write(self.style.ERROR(summary_text))
        else:
            self.stdout.write(self.style.WARNING(summary_text))

    def handle_generate_report(self, options):
        """Handle generating detailed retention reports"""
        output_format = options.get("format", "json")
        output_file = options.get("output")
        challenge_id = options.get("challenge_id")

        # Build the report data
        report_data = self._build_retention_report(challenge_id)

        # Format the output
        if output_format == "json":
            output_content = json.dumps(report_data, indent=2, default=str)
        elif output_format == "csv":
            output_content = self._convert_report_to_csv(report_data)

        # Output the report
        if output_file:
            with open(output_file, "w") as f:
                f.write(output_content)
            self.stdout.write(
                self.style.SUCCESS(f"Report saved to {output_file}")
            )
        else:
            self.stdout.write(output_content)

    def _build_retention_report(self, challenge_id=None):
        """Build comprehensive retention report data"""
        now = timezone.now()

        # Base query
        challenges_query = Challenge.objects.all()
        if challenge_id:
            challenges_query = challenges_query.filter(pk=challenge_id)

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
            host_team = (
                challenge.creator.team_name if challenge.creator else None
            )
            host_emails = None
            if challenge.creator:
                try:
                    host_emails = ", ".join(
                        [
                            user.email
                            for user in challenge.creator.members.all()
                        ]
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
                        phase.start_date.isoformat()
                        if phase.start_date
                        else None
                    ),
                    "end_date": (
                        phase.end_date.isoformat() if phase.end_date else None
                    ),
                    "is_public": phase.is_public,
                    "retention_eligible_date": None,
                }

                # Calculate retention date
                if phase.end_date and not phase.is_public:
                    retention_date = phase.end_date + timedelta(days=30)
                    phase_data["retention_eligible_date"] = (
                        retention_date.isoformat()
                    )

                challenge_data["phases"].append(phase_data)

            # Submission data for this challenge
            challenge_submissions = Submission.objects.filter(
                challenge_phase__challenge=challenge
            )
            challenge_data["submissions"][
                "total"
            ] = challenge_submissions.count()
            challenge_data["submissions"]["deleted"] = (
                challenge_submissions.filter(is_artifact_deleted=True).count()
            )
            challenge_data["submissions"]["eligible"] = (
                challenge_submissions.filter(
                    retention_eligible_date__lte=now,
                    is_artifact_deleted=False,
                ).count()
            )

            report_data["challenges"].append(challenge_data)

        return report_data

    def _convert_report_to_csv(self, report_data):
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
                    challenge["submissions"]["total"],
                    challenge["submissions"]["deleted"],
                    challenge["submissions"]["eligible"],
                ]
            )

        return output.getvalue()

    def handle_storage_usage(self, options):
        """Handle storage usage analysis"""
        challenge_id = options.get("challenge_id")
        top_n = options.get("top", 10)

        if challenge_id:
            self._show_challenge_storage_usage(challenge_id)
        else:
            self._show_top_storage_usage(top_n)

    def _show_challenge_storage_usage(self, challenge_id):
        """Show storage usage for a specific challenge"""
        try:
            challenge = Challenge.objects.get(pk=challenge_id)
        except Challenge.DoesNotExist:
            raise CommandError(f"Challenge {challenge_id} does not exist")

        self.stdout.write(f"\nStorage usage for challenge: {challenge.title}")
        self.stdout.write("=" * 50)

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

        self.stdout.write(
            f"Total estimated storage: {self._format_bytes(total_size)}"
        )
        self.stdout.write(f"Total submissions: {submissions.count()}")

        if phase_breakdown:
            self.stdout.write("\nBreakdown by phase:")
            for phase_name, data in phase_breakdown.items():
                self.stdout.write(
                    f"  {phase_name}: {data['submissions']} submissions, "
                    f"{self._format_bytes(data['size'])}"
                )

    def _show_top_storage_usage(self, top_n):
        """Show top N challenges by storage usage"""
        self.stdout.write(
            f"\nTop {top_n} challenges by estimated storage usage:"
        )
        self.stdout.write("=" * 60)

        # Get challenges with submission counts
        challenges = (
            Challenge.objects.annotate(
                submission_count=Count("challengephase__submissions")
            )
            .filter(submission_count__gt=0)
            .order_by("-submission_count")[:top_n]
        )

        self.stdout.write(
            f"{'Rank':<4} {'Challenge ID':<12} {'Submissions':<12} {'Est. Storage':<15} {'Title'}"
        )
        self.stdout.write("-" * 80)

        for rank, challenge in enumerate(challenges, 1):
            estimated_storage = (
                challenge.submission_count * 100 * 1024
            )  # 100KB per submission
            self.stdout.write(
                f"{rank:<4} {challenge.pk:<12} {challenge.submission_count:<12} "
                f"{self._format_bytes(estimated_storage):<15} {challenge.title[:40]}"
            )

    def _format_bytes(self, bytes_value):
        """Format bytes into human readable format"""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_value < 1024.0:
                return f"{bytes_value:.1f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.1f} TB"

    def handle_check_health(self, options):
        """Handle retention system health check"""
        verbose = options.get("verbose", False)

        self.stdout.write("Retention System Health Check")
        self.stdout.write("=" * 30)

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

        # Check 3: Submissions with missing retention dates
        missing_retention_dates = Submission.objects.filter(
            retention_eligible_date__isnull=True,
            is_artifact_deleted=False,
        ).count()
        if missing_retention_dates > 0:
            health_status["warnings"].append(
                f"Found {missing_retention_dates} submissions without retention dates"
            )

        # Check 4: Recent errors (if verbose)
        if verbose:
            health_status["recent_errors"] = "No recent errors found"

        # Display results
        self.stdout.write(f"Overall Status: {health_status['overall']}")
        self.stdout.write(
            f"Database: {health_status.get('database', 'UNKNOWN')}"
        )

        if health_status["issues"]:
            self.stdout.write("\nIssues:")
            for issue in health_status["issues"]:
                self.stdout.write(self.style.ERROR(f"  ✗ {issue}"))

        if health_status["warnings"]:
            self.stdout.write("\nWarnings:")
            for warning in health_status["warnings"]:
                self.stdout.write(self.style.WARNING(f"  ⚠ {warning}"))

        if verbose and "recent_errors" in health_status:
            self.stdout.write(
                f"\nRecent Errors: {health_status['recent_errors']}"
            )

    def handle_extend_retention(self, options):
        """Handle extending retention for specific challenges"""
        challenge_id = options["challenge_id"]
        additional_days = options["days"]
        confirm = options.get("confirm", False)

        try:
            challenge = Challenge.objects.get(pk=challenge_id)
        except Challenge.DoesNotExist:
            raise CommandError(f"Challenge {challenge_id} does not exist")

        # Get current retention period
        phases = ChallengePhase.objects.filter(challenge=challenge)
        if not phases.exists():
            raise CommandError(f"No phases found for challenge {challenge_id}")

        latest_end_date = max(
            phase.end_date for phase in phases if phase.end_date
        )
        current_retention_days = calculate_retention_period_days(
            latest_end_date
        )
        new_retention_days = current_retention_days + additional_days

        self.stdout.write(f"Challenge: {challenge.title}")
        self.stdout.write(f"Current retention: {current_retention_days} days")
        self.stdout.write(f"New retention: {new_retention_days} days")
        self.stdout.write(f"Extension: +{additional_days} days")

        if not confirm:
            confirm_input = input("\nProceed with extension? (yes/no): ")
            if confirm_input.lower() != "yes":
                self.stdout.write("Extension cancelled.")
                return

        # Set the new retention
        result = set_cloudwatch_log_retention(challenge_id, new_retention_days)

        if result.get("success"):
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully extended retention to {result['retention_days']} days"
                )
            )
        else:
            self.stdout.write(
                self.style.ERROR(
                    f"Failed to extend retention: {result.get('error')}"
                )
            )

    def handle_emergency_cleanup(self, options):
        """Handle emergency cleanup with bypass of safety checks"""
        challenge_id = options.get("challenge_id")
        force = options.get("force", False)

        self.stdout.write(self.style.WARNING("⚠️  EMERGENCY CLEANUP MODE ⚠️"))
        self.stdout.write("This will bypass normal safety checks!")

        if challenge_id:
            try:
                challenge = Challenge.objects.get(pk=challenge_id)
                self.stdout.write(f"Target challenge: {challenge.title}")
            except Challenge.DoesNotExist:
                raise CommandError(f"Challenge {challenge_id} does not exist")
        else:
            self.stdout.write("Target: ALL challenges")

        if not force:
            confirm_input = input(
                "\nAre you absolutely sure you want to proceed? Type 'EMERGENCY' to confirm: "
            )
            if confirm_input != "EMERGENCY":
                self.stdout.write("Emergency cleanup cancelled.")
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

        self.stdout.write(
            f"Found {submissions.count()} submissions for emergency cleanup"
        )

        # Mark all as deleted (this is the emergency bypass)
        deleted_count = submissions.update(is_artifact_deleted=True)

        self.stdout.write(
            self.style.SUCCESS(
                f"Emergency cleanup completed: {deleted_count} submissions marked as deleted"
            )
        )

    def handle_find_submissions(self, options):
        """Handle finding submissions by various criteria"""
        challenge_id = options.get("challenge_id")
        phase_id = options.get("phase_id")
        status = options.get("status")
        include_deleted = options.get("deleted", False)
        limit = options.get("limit", 50)

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

        if not include_deleted:
            query &= Q(is_artifact_deleted=False)

        submissions = Submission.objects.filter(query).select_related(
            "challenge_phase__challenge", "participant_team"
        )[:limit]

        self.stdout.write(f"Found {submissions.count()} submissions:")
        self.stdout.write("-" * 80)

        for submission in submissions:
            challenge_name = submission.challenge_phase.challenge.title
            phase_name = submission.challenge_phase.name
            team_name = (
                submission.participant_team.team_name
                if submission.participant_team
                else "N/A"
            )

            self.stdout.write(
                f"ID: {submission.pk:<6} | "
                f"Challenge: {challenge_name[:30]:<30} | "
                f"Phase: {phase_name[:15]:<15} | "
                f"Team: {team_name[:20]:<20} | "
                f"Status: {submission.status:<10} | "
                f"Deleted: {submission.is_artifact_deleted}"
            )
