from __future__ import absolute_import

import botocore
import json
import logging

from challenges.models import Challenge

from base.utils import get_sqs_service_resource

logger = logging.getLogger(__name__)


def get_or_create_sqs_queue(queue_name):
    """
    Args:
        queue_name: Name of the SQS Queue
    Returns:
        Returns the SQS Queue object
    """
    sqs = get_sqs_service_resource(queue_name)

    if queue_name == "":
        queue_name = "evalai_submission_queue"

    # Check if the queue exists. If not, then create one.
    try:
        queue = sqs.get_queue_by_name(QueueName=queue_name)
    except botocore.exceptions.ClientError as ex:
        if (
            ex.response["Error"]["Code"]
            == "AWS.SimpleQueueService.NonExistentQueue"
        ):
            queue = sqs.create_queue(QueueName=queue_name)
        else:
            logger.exception("Cannot get or create Queue")
    return queue


def publish_submission_message(challenge_pk, phase_pk, submission_pk):
    """
    Args:
        challenge_pk: Challenge Id
        phase_pk: Challenge Phase Id
        submission_pk: Submission Id

    Returns:
        Returns SQS response
    """
    message = {
        "challenge_pk": challenge_pk,
        "phase_pk": phase_pk,
        "submission_pk": submission_pk,
    }

    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        logger.exception(
            "Challenge does not exist for the given id {}".format(challenge_pk)
        )
        return
    queue_name = challenge.queue
    queue = get_or_create_sqs_queue(queue_name)
    response = queue.send_message(MessageBody=json.dumps(message))
    return response
