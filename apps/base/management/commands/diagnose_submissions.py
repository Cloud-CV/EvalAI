"""
Django management command to diagnose submission issues.

This command helps diagnose why submissions might be stuck in "submitted" status
by checking:
- Queue status and message counts
- Submission status distribution
- Challenge queue configuration
- Worker connectivity issues
"""

from __future__ import absolute_import

import os
from collections import defaultdict
from datetime import timedelta

import boto3
import botocore
from django.core.management.base import BaseCommand
from django.db.models import Count, Q
from django.utils import timezone

from challenges.models import Challenge, ChallengePhase
from jobs.models import Submission


class Command(BaseCommand):
    help = "Diagnose submission processing issues by checking queues and submission statuses"

    def add_arguments(self, parser):
        parser.add_argument(
            "--challenge-id",
            type=int,
            help="Specific challenge ID to diagnose (optional)",
        )
        parser.add_argument(
            "--check-queues",
            action="store_true",
            help="Check SQS queue status and message counts",
        )
        parser.add_argument(
            "--verbose",
            action="store_true",
            help="Show detailed information",
        )

    def handle(self, *args, **options):
        challenge_id = options.get("challenge_id")
        check_queues = options.get("check_queues", False)
        verbose = options.get("verbose", False)

        self.stdout.write(
            self.style.SUCCESS("\n=== EvalAI Submission Diagnostics ===\n")
        )

        # Get challenges to check
        if challenge_id:
            try:
                challenges = [Challenge.objects.get(pk=challenge_id)]
            except Challenge.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f"Challenge with ID {challenge_id} not found")
                )
                return
        else:
            # Get active challenges
            challenges = Challenge.objects.filter(
                end_date__gt=timezone.now(), published=True
            )

        if not challenges.exists():
            self.stdout.write(
                self.style.WARNING("No active challenges found to diagnose")
            )
            return

        for challenge in challenges:
            self.stdout.write(
                self.style.SUCCESS(f"\n--- Challenge: {challenge.title} (ID: {challenge.pk}) ---")
            )

            # Check queue configuration
            queue_name = challenge.queue
            self.stdout.write(f"Queue Name: {queue_name}")

            # Check submission statuses
            self._check_submission_statuses(challenge, verbose)

            # Check queue if requested
            if check_queues:
                self._check_queue_status(queue_name, challenge, verbose)

    def _check_submission_statuses(self, challenge, verbose):
        """Check distribution of submission statuses for a challenge"""
        phases = ChallengePhase.objects.filter(challenge=challenge)

        if not phases.exists():
            self.stdout.write(self.style.WARNING("  No phases found for this challenge"))
            return

        total_submissions = Submission.objects.filter(
            challenge_phase__challenge=challenge
        ).count()

        if total_submissions == 0:
            self.stdout.write(self.style.WARNING("  No submissions found"))
            return

        # Get status distribution
        status_counts = (
            Submission.objects.filter(challenge_phase__challenge=challenge)
            .values("status")
            .annotate(count=Count("id"))
            .order_by("-count")
        )

        self.stdout.write(f"\n  Total Submissions: {total_submissions}")
        self.stdout.write("  Status Distribution:")

        for status_info in status_counts:
            status = status_info["status"]
            count = status_info["count"]
            percentage = (count / total_submissions) * 100

            # Highlight stuck submissions
            if status == "submitted":
                style = self.style.WARNING
                icon = "⚠️ "
            elif status == "running":
                style = self.style.SUCCESS
                icon = "▶️ "
            elif status == "finished":
                style = self.style.SUCCESS
                icon = "✅ "
            elif status == "failed":
                style = self.style.ERROR
                icon = "❌ "
            else:
                style = self.style.NOTICE
                icon = "ℹ️ "

            self.stdout.write(
                style(f"    {icon}{status.upper()}: {count} ({percentage:.1f}%)")
            )

        # Check for stuck submissions (submitted for more than 1 hour)
        stuck_threshold = timezone.now() - timedelta(hours=1)
        stuck_submissions = Submission.objects.filter(
            challenge_phase__challenge=challenge,
            status="submitted",
            submitted_at__lt=stuck_threshold,
        ).count()

        if stuck_submissions > 0:
            self.stdout.write(
                self.style.ERROR(
                    f"\n  ⚠️  WARNING: {stuck_submissions} submission(s) stuck in 'submitted' status for >1 hour"
                )
            )

            if verbose:
                stuck_list = Submission.objects.filter(
                    challenge_phase__challenge=challenge,
                    status="submitted",
                    submitted_at__lt=stuck_threshold,
                ).select_related("challenge_phase", "participant_team")[:10]

                self.stdout.write("  Stuck Submissions (showing first 10):")
                for sub in stuck_list:
                    hours_stuck = (timezone.now() - sub.submitted_at).total_seconds() / 3600
                    self.stdout.write(
                        f"    - Submission #{sub.id} (Phase: {sub.challenge_phase.name}, "
                        f"Team: {sub.participant_team.team_name}, "
                        f"Stuck for {hours_stuck:.1f} hours)"
                    )

        # Check per-phase breakdown
        if verbose:
            self.stdout.write("\n  Per-Phase Breakdown:")
            for phase in phases:
                phase_submissions = Submission.objects.filter(
                    challenge_phase=phase
                ).count()
                phase_stuck = Submission.objects.filter(
                    challenge_phase=phase,
                    status="submitted",
                    submitted_at__lt=stuck_threshold,
                ).count()

                if phase_submissions > 0:
                    self.stdout.write(
                        f"    {phase.name}: {phase_submissions} submissions"
                    )
                    if phase_stuck > 0:
                        self.stdout.write(
                            self.style.ERROR(f"      ⚠️  {phase_stuck} stuck")
                        )

    def _check_queue_status(self, queue_name, challenge, verbose):
        """Check SQS queue status and message counts"""
        self.stdout.write(f"\n  Checking Queue: {queue_name}")

        try:
            # Get SQS client
            if challenge.use_host_sqs:
                sqs = boto3.resource(
                    "sqs",
                    region_name=challenge.queue_aws_region,
                    aws_secret_access_key=challenge.aws_secret_access_key,
                    aws_access_key_id=challenge.aws_access_key_id,
                )
            else:
                from django.conf import settings

                if settings.DEBUG or settings.TEST:
                    sqs = boto3.resource(
                        "sqs",
                        endpoint_url=os.environ.get(
                            "AWS_SQS_ENDPOINT", "http://sqs:9324"
                        ),
                        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                        aws_secret_access_key=os.environ.get(
                            "AWS_SECRET_ACCESS_KEY", "x"
                        ),
                        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "x"),
                    )
                    # Use default queue in dev/test
                    queue_name = "evalai_submission_queue"
                else:
                    sqs = boto3.resource(
                        "sqs",
                        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
                        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
                        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
                    )

            # Try to get queue
            try:
                queue = sqs.get_queue_by_name(QueueName=queue_name)
            except botocore.exceptions.ClientError as ex:
                if (
                    ex.response["Error"]["Code"]
                    == "AWS.SimpleQueueService.NonExistentQueue"
                ):
                    self.stdout.write(
                        self.style.ERROR(f"  ❌ Queue '{queue_name}' does not exist!")
                    )
                    self.stdout.write(
                        self.style.WARNING(
                            "  This is likely why submissions are stuck. "
                            "Workers cannot process messages from a non-existent queue."
                        )
                    )
                    return
                else:
                    raise

            # Get queue attributes
            attributes = queue.attributes
            approximate_messages = int(attributes.get("ApproximateNumberOfMessages", 0))
            approximate_messages_in_flight = int(
                attributes.get("ApproximateNumberOfMessagesNotVisible", 0)
            )

            self.stdout.write(
                self.style.SUCCESS(f"  ✅ Queue exists and is accessible")
            )
            self.stdout.write(f"  Messages in queue: {approximate_messages}")
            self.stdout.write(
                f"  Messages being processed: {approximate_messages_in_flight}"
            )

            if approximate_messages > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"  ⚠️  {approximate_messages} message(s) waiting in queue. "
                        "This suggests workers may not be running or processing slowly."
                    )
                )

            if approximate_messages_in_flight > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  ✅ {approximate_messages_in_flight} message(s) currently being processed"
                    )
                )

            if approximate_messages == 0 and approximate_messages_in_flight == 0:
                self.stdout.write(
                    self.style.SUCCESS("  ✅ Queue is empty - no pending messages")
                )

            if verbose:
                retention_period = attributes.get("MessageRetentionPeriod", "N/A")
                visibility_timeout = attributes.get("VisibilityTimeout", "N/A")
                self.stdout.write(f"\n  Queue Details:")
                self.stdout.write(f"    Retention Period: {retention_period} seconds")
                self.stdout.write(f"    Visibility Timeout: {visibility_timeout} seconds")

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"  ❌ Error checking queue: {str(e)}")
            )
            if verbose:
                import traceback

                self.stdout.write(traceback.format_exc())

        # Provide recommendations
        self.stdout.write("\n  Recommendations:")
        stuck_count = Submission.objects.filter(
            challenge_phase__challenge=challenge,
            status="submitted",
            submitted_at__lt=timezone.now() - timedelta(hours=1),
        ).count()

        if stuck_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    "    1. Check if workers are running for this queue:"
                )
            )
            self.stdout.write(
                f"       docker ps | grep {queue_name}  # or check AWS ECS/Fargate tasks"
            )
            self.stdout.write(
                self.style.WARNING("    2. Verify CHALLENGE_QUEUE environment variable:")
            )
            self.stdout.write(f"       Should be set to: {queue_name}")
            self.stdout.write(
                self.style.WARNING("    3. Check worker logs for errors:")
            )
            self.stdout.write(
                "       Look for errors during challenge loading or queue connection"
            )
            self.stdout.write(
                self.style.WARNING("    4. Restart workers if needed:")
            )
            self.stdout.write(
                f"       docker-compose run -e CHALLENGE_QUEUE={queue_name} worker_py3_9"
            )

