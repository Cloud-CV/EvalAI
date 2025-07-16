# Command to run: python manage.py shell < scripts/manage_retention.py
# 
# Usage examples:
#   python manage.py shell < scripts/manage_retention.py cleanup --dry-run
#   python manage.py shell < scripts/manage_retention.py status
#   python manage.py shell < scripts/manage_retention.py status --challenge-id 123
#   python manage.py shell < scripts/manage_retention.py set-log-retention 123 --days 30
#   python manage.py shell < scripts/manage_retention.py generate-report --format csv --output report.csv
#   python manage.py shell < scripts/manage_retention.py check-health --verbose
#
import csv
import json
import logging
import sys
from datetime import timedelta
from io import StringIO

from challenges.aws_utils import (
    calculate_retention_period_days,
    cleanup_expired_submission_artifacts,
    delete_submission_files_from_storage,
    is_user_a_host_of_challenge,
    map_retention_days_to_aws_values,
    record_host_retention_consent,
    set_cloudwatch_log_retention,
    weekly_retention_notifications_and_consent_log,
)
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.utils import timezone
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
    print_info("Starting cleanup of expired submission artifacts...")
    
    if dry_run:
        print_info("DRY RUN MODE - No actual deletions will be performed")
    
    try:
        deleted_count = cleanup_expired_submission_artifacts(dry_run=dry_run)
        if dry_run:
            print_info(f"Would delete {deleted_count} expired artifacts")
        else:
            print_success(f"Successfully deleted {deleted_count} expired artifacts")
    except Exception as e:
        print_error(f"Error during cleanup: {str(e)}")
        logger.exception("Error during cleanup")


def handle_update_dates():
    """Update retention eligible dates for submissions"""
    print_info("Updating retention eligible dates for submissions...")
    
    try:
        # Get submissions that need retention date updates
        submissions = Submission.objects.filter(
            retention_eligible_date__isnull=True,
            status__in=['finished', 'failed', 'cancelled']
        )
        
        updated_count = 0
        for submission in submissions:
            # Calculate retention period based on challenge settings
            challenge = submission.challenge_phase.challenge
            retention_days = calculate_retention_period_days(challenge)
            
            if retention_days > 0:
                submission.retention_eligible_date = submission.completed_at + timedelta(days=retention_days)
                submission.save()
                updated_count += 1
        
        print_success(f"Updated retention dates for {updated_count} submissions")
    except Exception as e:
        print_error(f"Error updating retention dates: {str(e)}")
        logger.exception("Error updating retention dates")


def handle_send_warnings():
    """Send retention warning notifications to challenge hosts"""
    print_info("Sending retention warning notifications...")
    
    try:
        notification_count = weekly_retention_notifications_and_consent_log()
        print_success(f"Sent {notification_count} retention notifications")
    except Exception as e:
        print_error(f"Error sending warnings: {str(e)}")
        logger.exception("Error sending warnings")


def handle_set_log_retention(challenge_id, days=None):
    """Set CloudWatch log retention for a specific challenge"""
    print_info(f"Setting log retention for challenge {challenge_id}...")
    
    try:
        challenge = Challenge.objects.get(id=challenge_id)
        
        if days is None:
            days = calculate_retention_period_days(challenge)
        
        set_cloudwatch_log_retention(challenge, days)
        print_success(f"Set log retention to {days} days for challenge {challenge_id}")
    except Challenge.DoesNotExist:
        print_error(f"Challenge {challenge_id} does not exist")
    except Exception as e:
        print_error(f"Error setting log retention: {str(e)}")
        logger.exception("Error setting log retention")


def handle_force_delete(submission_id, confirm=False):
    """Force delete submission files for a specific submission"""
    print_info(f"Force deleting submission files for submission {submission_id}...")
    
    if not confirm:
        print_warning("Use --confirm to actually perform the deletion")
        return
    
    try:
        submission = Submission.objects.get(id=submission_id)
        delete_submission_files_from_storage(submission)
        print_success(f"Force deleted files for submission {submission_id}")
    except Submission.DoesNotExist:
        print_error(f"Submission {submission_id} does not exist")
    except Exception as e:
        print_error(f"Error force deleting submission: {str(e)}")
        logger.exception("Error force deleting submission")


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
        print_info(f"Retention status for challenge: {challenge.title} (ID: {challenge_id})")
        
        # Get submission counts by status
        submissions = Submission.objects.filter(challenge_phase__challenge=challenge)
        status_counts = submissions.values('status').annotate(count=Count('id'))
        
        print_info("Submission counts by status:")
        for status_count in status_counts:
            print_info(f"  {status_count['status']}: {status_count['count']}")
        
        # Get retention eligible submissions
        retention_eligible = submissions.filter(
            retention_eligible_date__lte=timezone.now(),
            status__in=['finished', 'failed', 'cancelled']
        ).count()
        
        print_info(f"Submissions eligible for deletion: {retention_eligible}")
        
    except Challenge.DoesNotExist:
        print_error(f"Challenge {challenge_id} does not exist")


def show_overall_status():
    """Show overall retention status"""
    print_info("Overall retention status:")
    
    # Total challenges
    total_challenges = Challenge.objects.count()
    print_info(f"Total challenges: {total_challenges}")
    
    # Total submissions
    total_submissions = Submission.objects.count()
    print_info(f"Total submissions: {total_submissions}")
    
    # Submissions by status
    status_counts = Submission.objects.values('status').annotate(count=Count('id'))
    print_info("Submissions by status:")
    for status_count in status_counts:
        print_info(f"  {status_count['status']}: {status_count['count']}")
    
    # Retention eligible submissions
    retention_eligible = Submission.objects.filter(
        retention_eligible_date__lte=timezone.now(),
        status__in=['finished', 'failed', 'cancelled']
    ).count()
    
    print_info(f"Submissions eligible for deletion: {retention_eligible}")


def handle_bulk_set_log_retention(challenge_ids=None, all_active=False, days=None, dry_run=False):
    """Set CloudWatch log retention for multiple challenges"""
    if dry_run:
        print_info("DRY RUN MODE - No actual changes will be made")
    
    if all_active:
        challenges = Challenge.objects.filter(end_date__gt=timezone.now())
        print_info(f"Setting log retention for all active challenges ({challenges.count()} challenges)")
    elif challenge_ids:
        challenges = Challenge.objects.filter(id__in=challenge_ids)
        print_info(f"Setting log retention for {len(challenge_ids)} specified challenges")
    else:
        print_error("Must specify either --challenge-ids or --all-active")
        return
    
    success_count = 0
    error_count = 0
    
    for challenge in challenges:
        try:
            if days is None:
                retention_days = calculate_retention_period_days(challenge)
            else:
                retention_days = days
            
            if not dry_run:
                set_cloudwatch_log_retention(challenge, retention_days)
            
            print_info(f"{'Would set' if dry_run else 'Set'} log retention to {retention_days} days for challenge {challenge.id} ({challenge.title})")
            success_count += 1
        except Exception as e:
            print_error(f"Error setting log retention for challenge {challenge.id}: {str(e)}")
            error_count += 1
    
    print_success(f"Completed: {success_count} successful, {error_count} errors")


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
            with open(output, 'w') as f:
                f.write(report_content)
            print_success(f"Report saved to {output}")
        else:
            print(report_content)
            
    except Exception as e:
        print_error(f"Error generating report: {str(e)}")
        logger.exception("Error generating report")


def build_retention_report(challenge_id=None):
    """Build retention report data"""
    if challenge_id:
        challenges = Challenge.objects.filter(id=challenge_id)
    else:
        challenges = Challenge.objects.all()
    
    report_data = {
        "generated_at": timezone.now().isoformat(),
        "challenges": []
    }
    
    for challenge in challenges:
        challenge_data = {
            "id": challenge.id,
            "title": challenge.title,
            "end_date": challenge.end_date.isoformat() if challenge.end_date else None,
            "retention_period_days": calculate_retention_period_days(challenge),
            "submissions": {}
        }
        
        # Get submission counts by status
        submissions = Submission.objects.filter(challenge_phase__challenge=challenge)
        status_counts = submissions.values('status').annotate(count=Count('id'))
        
        for status_count in status_counts:
            challenge_data["submissions"][status_count['status']] = status_count['count']
        
        # Get retention eligible submissions
        retention_eligible = submissions.filter(
            retention_eligible_date__lte=timezone.now(),
            status__in=['finished', 'failed', 'cancelled']
        ).count()
        
        challenge_data["submissions"]["retention_eligible"] = retention_eligible
        report_data["challenges"].append(challenge_data)
    
    return report_data


def convert_report_to_csv(report_data):
    """Convert report data to CSV format"""
    output = StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow([
        "Challenge ID", "Title", "End Date", "Retention Period (Days)",
        "Finished", "Failed", "Cancelled", "Running", "Submitted", "Retention Eligible"
    ])
    
    # Write data rows
    for challenge in report_data["challenges"]:
        writer.writerow([
            challenge["id"],
            challenge["title"],
            challenge["end_date"],
            challenge["retention_period_days"],
            challenge["submissions"].get("finished", 0),
            challenge["submissions"].get("failed", 0),
            challenge["submissions"].get("cancelled", 0),
            challenge["submissions"].get("running", 0),
            challenge["submissions"].get("submitted", 0),
            challenge["submissions"].get("retention_eligible", 0)
        ])
    
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
        print_info(f"Storage usage for challenge: {challenge.title} (ID: {challenge_id})")
        
        # Calculate total storage for this challenge
        submissions = Submission.objects.filter(challenge_phase__challenge=challenge)
        total_size = sum(submission.input_file.size for submission in submissions if submission.input_file)
        
        print_info(f"Total storage: {format_bytes(total_size)}")
        
        # Show by phase
        phases = ChallengePhase.objects.filter(challenge=challenge)
        for phase in phases:
            phase_submissions = submissions.filter(challenge_phase=phase)
            phase_size = sum(sub.input_file.size for sub in phase_submissions if sub.input_file)
            print_info(f"  Phase {phase.name}: {format_bytes(phase_size)}")
            
    except Challenge.DoesNotExist:
        print_error(f"Challenge {challenge_id} does not exist")


def show_top_storage_usage(top_n):
    """Show top N challenges by storage usage"""
    print_info(f"Top {top_n} challenges by storage usage:")
    
    challenges = Challenge.objects.all()
    challenge_sizes = []
    
    for challenge in challenges:
        submissions = Submission.objects.filter(challenge_phase__challenge=challenge)
        total_size = sum(submission.input_file.size for submission in submissions if submission.input_file)
        challenge_sizes.append((challenge, total_size))
    
    # Sort by size (descending) and take top N
    challenge_sizes.sort(key=lambda x: x[1], reverse=True)
    
    for i, (challenge, size) in enumerate(challenge_sizes[:top_n], 1):
        print_info(f"{i}. Challenge {challenge.id} ({challenge.title}): {format_bytes(size)}")


def format_bytes(bytes_value):
    """Format bytes in human readable format"""
    if bytes_value == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(bytes_value, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_value / p, 2)
    return f"{s} {size_names[i]}"


def handle_check_health(verbose=False):
    """Check retention system health"""
    print_info("Checking retention system health...")
    
    health_issues = []
    
    # Check for challenges without retention settings
    challenges_without_retention = Challenge.objects.filter(
        retention_period_days__isnull=True
    ).count()
    
    if challenges_without_retention > 0:
        health_issues.append(f"{challenges_without_retention} challenges without retention settings")
    
    # Check for submissions with missing retention dates
    submissions_without_retention_date = Submission.objects.filter(
        retention_eligible_date__isnull=True,
        status__in=['finished', 'failed', 'cancelled']
    ).count()
    
    if submissions_without_retention_date > 0:
        health_issues.append(f"{submissions_without_retention_date} submissions without retention dates")
    
    # Check for expired submissions that haven't been cleaned up
    expired_submissions = Submission.objects.filter(
        retention_eligible_date__lte=timezone.now(),
        status__in=['finished', 'failed', 'cancelled']
    ).count()
    
    if expired_submissions > 0:
        health_issues.append(f"{expired_submissions} expired submissions need cleanup")
    
    if health_issues:
        print_warning("Health issues found:")
        for issue in health_issues:
            print_warning(f"  - {issue}")
    else:
        print_success("No health issues found")
    
    if verbose:
        print_info("Detailed health information:")
        print_info(f"  Total challenges: {Challenge.objects.count()}")
        print_info(f"  Total submissions: {Submission.objects.count()}")
        print_info(f"  Active challenges: {Challenge.objects.filter(end_date__gt=timezone.now()).count()}")


def handle_extend_retention(challenge_id, days, confirm=False):
    """Extend retention for specific challenges"""
    print_info(f"Extending retention for challenge {challenge_id} by {days} days...")
    
    if not confirm:
        print_warning("Use --confirm to actually perform the extension")
        return
    
    try:
        challenge = Challenge.objects.get(id=challenge_id)
        
        # Update retention period
        if challenge.retention_period_days is None:
            challenge.retention_period_days = days
        else:
            challenge.retention_period_days += days
        
        challenge.save()
        
        # Update existing submissions
        submissions = Submission.objects.filter(
            challenge_phase__challenge=challenge,
            retention_eligible_date__isnull=False
        )
        
        updated_count = 0
        for submission in submissions:
            submission.retention_eligible_date += timedelta(days=days)
            submission.save()
            updated_count += 1
        
        print_success(f"Extended retention by {days} days for challenge {challenge_id}")
        print_success(f"Updated {updated_count} existing submissions")
        
    except Challenge.DoesNotExist:
        print_error(f"Challenge {challenge_id} does not exist")
    except Exception as e:
        print_error(f"Error extending retention: {str(e)}")
        logger.exception("Error extending retention")


def handle_emergency_cleanup(challenge_id=None, force=False):
    """Emergency cleanup with bypass of safety checks"""
    print_warning("EMERGENCY CLEANUP MODE - This will bypass safety checks!")
    
    if not force:
        print_warning("Use --force to actually perform emergency cleanup")
        return
    
    try:
        if challenge_id:
            submissions = Submission.objects.filter(
                challenge_phase__challenge_id=challenge_id,
                status__in=['finished', 'failed', 'cancelled']
            )
            print_info(f"Emergency cleanup for challenge {challenge_id}")
        else:
            submissions = Submission.objects.filter(
                status__in=['finished', 'failed', 'cancelled']
            )
            print_info("Emergency cleanup for all challenges")
        
        deleted_count = 0
        for submission in submissions:
            try:
                delete_submission_files_from_storage(submission)
                deleted_count += 1
            except Exception as e:
                print_error(f"Error deleting submission {submission.id}: {str(e)}")
        
        print_success(f"Emergency cleanup completed: {deleted_count} submissions processed")
        
    except Exception as e:
        print_error(f"Error during emergency cleanup: {str(e)}")
        logger.exception("Error during emergency cleanup")


def handle_find_submissions(challenge_id=None, phase_id=None, status=None, deleted=False, limit=50):
    """Find submissions by various criteria"""
    print_info("Finding submissions...")
    
    submissions = Submission.objects.all()
    
    if challenge_id:
        submissions = submissions.filter(challenge_phase__challenge_id=challenge_id)
    
    if phase_id:
        submissions = submissions.filter(challenge_phase_id=phase_id)
    
    if status:
        submissions = submissions.filter(status=status)
    
    if not deleted:
        submissions = submissions.exclude(status='deleted')
    
    submissions = submissions[:limit]
    
    print_info(f"Found {submissions.count()} submissions:")
    for submission in submissions:
        print_info(f"  Submission {submission.id}: {submission.status} (Challenge: {submission.challenge_phase.challenge.title})")


def handle_check_consent(challenge_id=None):
    """Check consent status"""
    if challenge_id:
        try:
            challenge = Challenge.objects.get(id=challenge_id)
            print_info(f"Consent status for challenge {challenge_id} ({challenge.title}):")
            print_info(f"  Host consent required: {challenge.host_retention_consent_required}")
            print_info(f"  Host consent given: {challenge.host_retention_consent_given}")
            print_info(f"  Consent date: {challenge.host_retention_consent_date}")
        except Challenge.DoesNotExist:
            print_error(f"Challenge {challenge_id} does not exist")
    else:
        print_info("Overall consent status:")
        total_challenges = Challenge.objects.count()
        consent_required = Challenge.objects.filter(host_retention_consent_required=True).count()
        consent_given = Challenge.objects.filter(host_retention_consent_given=True).count()
        
        print_info(f"  Total challenges: {total_challenges}")
        print_info(f"  Requiring consent: {consent_required}")
        print_info(f"  Consent given: {consent_given}")


def handle_bulk_consent(challenge_ids, require_consent=True):
    """Bulk consent operations"""
    if require_consent:
        print_info(f"Requiring consent for {len(challenge_ids)} challenges...")
        bulk_require_consent(challenge_ids)
    else:
        print_info(f"Checking consent for {len(challenge_ids)} challenges...")
        bulk_check_consent(challenge_ids)


def bulk_check_consent(challenge_ids):
    """Bulk check consent for multiple challenges"""
    challenges = Challenge.objects.filter(id__in=challenge_ids)
    
    for challenge in challenges:
        print_info(f"Challenge {challenge.id} ({challenge.title}):")
        print_info(f"  Consent required: {challenge.host_retention_consent_required}")
        print_info(f"  Consent given: {challenge.host_retention_consent_given}")


def bulk_require_consent(challenge_ids):
    """Bulk require consent for multiple challenges"""
    challenges = Challenge.objects.filter(id__in=challenge_ids)
    
    updated_count = 0
    for challenge in challenges:
        if not challenge.host_retention_consent_required:
            challenge.host_retention_consent_required = True
            challenge.save()
            updated_count += 1
            print_info(f"Updated challenge {challenge.id} to require consent")
    
    print_success(f"Updated {updated_count} challenges to require consent")


def handle_recent_consent_changes():
    """Show recent consent changes"""
    print_info("Recent consent changes:")
    
    # This would need to be implemented based on your audit trail system
    # For now, just show challenges with recent consent dates
    recent_consents = Challenge.objects.filter(
        host_retention_consent_date__isnull=False
    ).order_by('-host_retention_consent_date')[:10]
    
    for challenge in recent_consents:
        print_info(f"Challenge {challenge.id} ({challenge.title}): {challenge.host_retention_consent_date}")


def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) < 2:
        print_error("Usage: python manage.py shell < scripts/manage_retention.py <action> [options]")
        print_info("Available actions:")
        print_info("  cleanup [--dry-run]")
        print_info("  update-dates")
        print_info("  send-warnings")
        print_info("  set-log-retention <challenge_id> [--days <days>]")
        print_info("  force-delete <submission_id> [--confirm]")
        print_info("  status [--challenge-id <challenge_id>]")
        print_info("  bulk-set-log-retention [--challenge-ids <ids>] [--all-active] [--days <days>] [--dry-run]")
        print_info("  generate-report [--format json|csv] [--output <file>] [--challenge-id <challenge_id>]")
        print_info("  storage-usage [--challenge-id <challenge_id>] [--top <n>]")
        print_info("  check-health [--verbose]")
        print_info("  extend-retention <challenge_id> --days <days> [--confirm]")
        print_info("  emergency-cleanup [--challenge-id <challenge_id>] [--force]")
        print_info("  find-submissions [--challenge-id <challenge_id>] [--phase-id <phase_id>] [--status <status>] [--deleted] [--limit <n>]")
        print_info("  check-consent [--challenge-id <challenge_id>]")
        print_info("  bulk-consent [--challenge-ids <ids>] [--require-consent]")
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
            
            handle_bulk_set_log_retention(challenge_ids, all_active, days, dry_run)
        
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
            
            handle_find_submissions(challenge_id, phase_id, status, deleted, limit)
        
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