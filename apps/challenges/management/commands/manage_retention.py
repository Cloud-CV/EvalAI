import logging
from datetime import timedelta

from challenges.aws_utils import (
    cleanup_expired_submission_artifacts,
    delete_submission_files_from_storage,
    send_retention_warning_notifications,
    set_cloudwatch_log_retention,
)
from challenges.models import Challenge, ChallengePhase
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from jobs.models import Submission

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Manage retention policies for submissions and logs"

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
