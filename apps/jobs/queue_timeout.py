import logging
from datetime import timedelta

from challenges.aws_utils import trigger_eks_node_autoscale
from django.core.files.base import ContentFile
from django.db.models.functions import Coalesce
from django.utils import timezone

from .models import Submission

logger = logging.getLogger(__name__)

STUCK_QUEUE_STATUSES = (
    Submission.SUBMITTED,
    Submission.SUBMITTING,
    Submission.QUEUED,
    Submission.RESUMING,
)

QUEUE_TIMEOUT_STDERR = (
    "Submission exceeded the queue time limit and was not picked up for "
    "evaluation."
)


def get_stuck_submission_queryset(challenge_pk=None):
    """Return submissions in pre-running states that may be queue-stuck."""
    queryset = (
        Submission.objects.filter(
            status__in=STUCK_QUEUE_STATUSES,
            ignore_submission=False,
            challenge_phase__challenge__submission_queue_time_limit__gt=0,
        )
        .select_related("challenge_phase__challenge")
        .annotate(queue_started_at=Coalesce("rerun_resumed_at", "submitted_at"))
    )
    if challenge_pk is not None:
        queryset = queryset.filter(challenge_phase__challenge__pk=challenge_pk)
    return queryset


def is_submission_queue_timed_out(submission, now=None):
    """Return True when a submission has exceeded its challenge queue limit."""
    now = now or timezone.now()
    challenge = submission.challenge_phase.challenge
    queue_time_limit = challenge.submission_queue_time_limit
    if not queue_time_limit:
        return False

    queue_started_at = submission.rerun_resumed_at or submission.submitted_at
    return queue_started_at <= now - timedelta(seconds=queue_time_limit)


def fail_submission_due_to_queue_timeout(submission, dry_run=False):
    """Mark a queue-stuck submission as failed."""
    if dry_run:
        return True

    previous_status = submission.status
    submission.status = Submission.FAILED
    submission.completed_at = timezone.now()
    submission.stderr_file.save(
        "stderr.txt",
        ContentFile(QUEUE_TIMEOUT_STDERR.encode("utf-8")),
    )
    submission.save()

    challenge = submission.challenge_phase.challenge
    trigger_eks_node_autoscale(
        challenge.pk,
        trigger_source="submission_queue_timeout",
        submission_pk=submission.pk,
        submission_status=Submission.FAILED,
        previous_submission_status=previous_status,
    )
    return True


def fail_stuck_submissions(challenge_pk=None, dry_run=False):
    """
    Fail submissions that exceeded their challenge queue time limit.

    Returns the number of submissions that were (or would be) failed.
    """
    now = timezone.now()
    failed_count = 0

    for submission in get_stuck_submission_queryset(challenge_pk):
        if not is_submission_queue_timed_out(submission, now=now):
            continue

        previous_status = submission.status
        queue_started_at = submission.rerun_resumed_at or submission.submitted_at
        challenge = submission.challenge_phase.challenge

        if fail_submission_due_to_queue_timeout(submission, dry_run=dry_run):
            failed_count += 1
            action = "Would fail" if dry_run else "Failed"
            logger.warning(
                "%s queue-stuck submission pk=%s challenge_pk=%s status=%s "
                "queue_started_at=%s queue_time_limit=%ss",
                action,
                submission.pk,
                challenge.pk,
                previous_status,
                queue_started_at,
                challenge.submission_queue_time_limit,
            )

    if failed_count:
        logger.info(
            "fail_stuck_submissions: %s %d submission(s).",
            "would fail" if dry_run else "failed",
            failed_count,
        )
    return failed_count
