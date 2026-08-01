from __future__ import absolute_import

import json
import logging
import uuid

from base.utils import get_or_create_sqs_queue, send_slack_notification
from challenges.models import Challenge

from .utils import get_submission_model

logger = logging.getLogger(__name__)


def publish_submission_message(message):
    """
    Publish a submission evaluation message to the challenge SQS queue.

    For FIFO queues (queue name ends with ``.fifo``), sets:
    - ``MessageGroupId`` to ``{phase_pk}-{participant_team_pk}`` so
      submissions from the same team stay ordered within a phase while
      different teams can be processed in parallel by ECS workers.
    - ``MessageDeduplicationId`` to ``{submission_pk}-{uuid4}`` so each
      intentional enqueue (including resume/republish) is unique. SQS only
      deduplicates matching ids within a five-minute window.

    Deploy note: changing MessageGroupId strategy while producers are
    still enqueueing can leave legacy and new group ids on the queue
    together (same submission under two groups). Pause enqueueing,
    deploy, purge/drain (``purge_challenge_sqs_queue``; purge deletes
    pending work), requeue submitted/queued submissions that still need
    evaluation, then resume producers only after the queue is empty
    under the new strategy.

    Args:
        message: A Dict with following keys
            - "challenge_pk": int
            - "phase_pk": int
            - "submission_pk": int
            - "submitted_image_uri": str, (only available when the challenge is a code upload challenge)
            - "is_static_dataset_code_upload_submission": bool

    Returns:
        Returns SQS response
    """

    try:
        challenge = Challenge.objects.get(pk=message["challenge_pk"])
    except Challenge.DoesNotExist:
        logger.exception(
            "Challenge does not exist for the given id {}".format(
                message["challenge_pk"]
            )
        )
        return
    queue_name = challenge.queue
    slack_url = challenge.slack_webhook_url
    queue = get_or_create_sqs_queue(queue_name, challenge)
    # FIFO grouping and Slack both need the submission; load once.
    submission = None
    if queue_name.endswith(".fifo") or slack_url:
        submission = get_submission_model(message["submission_pk"])
    send_kwargs = {"MessageBody": json.dumps(message)}
    if queue_name.endswith(".fifo"):
        # Group by phase + participant team so:
        # - submissions from the same team stay ordered within a phase
        # - different teams can be evaluated in parallel by ECS workers
        # SQS FIFO allows only one in-flight message per MessageGroupId;
        # phase_pk alone serialized an entire phase to a single worker.
        team_pk = submission.participant_team_id
        send_kwargs["MessageGroupId"] = "{}-{}".format(
            message["phase_pk"], team_pk
        )
        # FIFO deduplicates on MessageDeduplicationId for 5 minutes. Using
        # only submission_pk silently drops resume/republish of the same
        # submission. Include a UUID so each intentional enqueue is unique.
        send_kwargs["MessageDeduplicationId"] = "{}-{}".format(
            message["submission_pk"], uuid.uuid4()
        )
    response = queue.send_message(**send_kwargs)
    # send slack notification
    if slack_url:
        challenge_name = challenge.title
        participant_team_name = submission.participant_team.team_name
        phase_name = submission.challenge_phase.name
        slack_message = {
            "text": "A *new submission* has been uploaded to {}".format(
                challenge_name
            ),
            "fields": [
                {
                    "title": "Challenge Phase",
                    "value": phase_name,
                    "short": True,
                },
                {
                    "title": "Participant Team Name",
                    "value": participant_team_name,
                    "short": True,
                },
                {
                    "title": "Submission Id",
                    "value": message["submission_pk"],
                    "short": True,
                },
            ],
        }
        send_slack_notification(slack_url, slack_message)
    return response
