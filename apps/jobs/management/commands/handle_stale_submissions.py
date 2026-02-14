"""
Management command to detect and handle stale submissions.

This command identifies submissions that have been stuck in intermediate states
(submitted, running, submitting, resuming, queued) for longer than a specified
timeout period and provides options to requeue or fail them.

Usage:
    python manage.py handle_stale_submissions --timeout-hours 24 --action requeue
    python manage.py handle_stale_submissions --timeout-hours 48 --action fail
    python manage.py handle_stale_submissions --dry-run
"""

import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from jobs.models import Submission
from jobs.sender import publish_submission_message

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Detect and handle submissions stuck in intermediate states"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout-hours",
            type=int,
            default=24,
            help="Number of hours after which a submission is considered stale (default: 24)",
        )
        parser.add_argument(
            "--action",
            type=str,
            choices=["requeue", "fail", "report"],
            default="report",
            help="Action to take: requeue (republish to queue), fail (mark as failed), report (just list)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show what would be done without making changes",
        )
        parser.add_argument(
            "--challenge-id",
            type=int,
            help="Only process submissions for a specific challenge",
        )
        parser.add_argument(
            "--submission-id",
            type=int,
            help="Only process a specific submission by ID",
        )

    def handle(self, *args, **options):
        timeout_hours = options["timeout_hours"]
        action = options["action"]
        dry_run = options["dry_run"]
        challenge_id = options.get("challenge_id")
        submission_id = options.get("submission_id")

        cutoff_time = timezone.now() - timedelta(hours=timeout_hours)

        # Define stale states - submissions should not stay in these states for too long
        stale_states = [
            Submission.SUBMITTED,
            Submission.RUNNING,
            Submission.SUBMITTING,
            Submission.RESUMING,
            Submission.QUEUED,
        ]

        # Build queryset for stale submissions
        queryset = Submission.objects.filter(
            status__in=stale_states,
            submitted_at__lt=cutoff_time,
        )

        if challenge_id:
            queryset = queryset.filter(challenge_phase__challenge_id=challenge_id)

        if submission_id:
            queryset = queryset.filter(id=submission_id)

        stale_submissions = queryset.select_related(
            "challenge_phase",
            "challenge_phase__challenge",
            "participant_team",
        ).order_by("-submitted_at")

        total_count = stale_submissions.count()

        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f"No stale submissions found (timeout: {timeout_hours} hours)"
                )
            )
            return

        self.stdout.write(
            self.style.WARNING(
                f"Found {total_count} stale submission(s) (older than {timeout_hours} hours)"
            )
        )

        # Group by status for reporting
        status_counts = {}
        for submission in stale_submissions:
            status = submission.status
            if status not in status_counts:
                status_counts[status] = 0
            status_counts[status] += 1

        self.stdout.write("\nBreakdown by status:")
        for status, count in status_counts.items():
            self.stdout.write(f"  - {status}: {count}")

        if action == "report":
            self.stdout.write("\nStale submissions:")
            for submission in stale_submissions[:50]:  # Limit output
                hours_stale = (
                    timezone.now() - submission.submitted_at
                ).total_seconds() / 3600
                self.stdout.write(
                    f"  ID: {submission.id}, "
                    f"Status: {submission.status}, "
                    f"Challenge: {submission.challenge_phase.challenge.title}, "
                    f"Phase: {submission.challenge_phase.name}, "
                    f"Team: {submission.participant_team.team_name}, "
                    f"Hours stale: {hours_stale:.1f}"
                )
            if total_count > 50:
                self.stdout.write(f"  ... and {total_count - 50} more")
            return

        # Process submissions based on action
        success_count = 0
        error_count = 0

        for submission in stale_submissions:
            try:
                if dry_run:
                    self.stdout.write(
                        f"[DRY RUN] Would {action} submission {submission.id} "
                        f"(status: {submission.status})"
                    )
                    success_count += 1
                    continue

                if action == "requeue":
                    self._requeue_submission(submission)
                elif action == "fail":
                    self._fail_submission(submission)

                success_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully {action}d submission {submission.id}"
                    )
                )

            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f"Error processing submission {submission.id}: {str(e)}"
                    )
                )
                logger.exception(
                    f"Error handling stale submission {submission.id}"
                )

        self.stdout.write(
            f"\nProcessed {success_count + error_count} submissions: "
            f"{success_count} successful, {error_count} errors"
        )

    def _requeue_submission(self, submission):
        """Requeue a stale submission by republishing to the message queue."""
        # Reset submission status to SUBMITTED
        submission.status = Submission.SUBMITTED
        submission.started_at = None
        submission.save()

        # Publish message to queue
        message = {
            "challenge_pk": submission.challenge_phase.challenge.pk,
            "phase_pk": submission.challenge_phase.pk,
            "submission_pk": submission.pk,
        }
        publish_submission_message(message)

        logger.info(
            f"Requeued stale submission {submission.id} for challenge "
            f"{submission.challenge_phase.challenge.title}"
        )

    def _fail_submission(self, submission):
        """Mark a stale submission as failed."""
        submission.status = Submission.FAILED
        submission.completed_at = timezone.now()
        submission.output = (
            "Submission failed due to timeout. The submission was stuck in "
            f"'{submission.status}' status for too long. Please try resubmitting."
        )
        submission.save()

        logger.info(
            f"Marked stale submission {submission.id} as failed for challenge "
            f"{submission.challenge_phase.challenge.title}"
        )
