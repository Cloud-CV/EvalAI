from __future__ import absolute_import

import boto3
import botocore
import json
import logging
import os

from django.conf import settings

from base.utils import send_slack_notification
from challenges.models import Challenge
from .utils import get_submission_model
from .metrics import push_metrics_to_pushgateway, num_submissions_in_queue

logger = logging.getLogger(__name__)


def get_or_create_sqs_queue(queue_name):
    """
    Args:
        queue_name: Name of the SQS Queue
    Returns:
        Returns the SQS Queue object
    """
    if settings.DEBUG or settings.TEST:
        sqs = boto3.resource(
            "sqs",
            endpoint_url=os.environ.get("AWS_SQS_ENDPOINT", "http://sqs:9324"),
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "x"),
        )
        # Use default queue name in dev and test environment
        queue_name = "evalai_submission_queue"
    else:
        sqs = boto3.resource(
            "sqs",
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        )

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


def publish_submission_message(message):
    """
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
    queue = get_or_create_sqs_queue(queue_name)
    # increase counter for submission pushed into queue
    submission_pk = message["submission_pk"]
    num_submissions_in_queue.labels(submission_pk, queue_name).inc()
    # push metrics to pushgateway as a submission is pushed into queue
    job_id = "submission_{}".format(submission_pk)
    push_metrics_to_pushgateway(job_id)
    response = queue.send_message(MessageBody=json.dumps(message))
    # send slack notification
    if slack_url:
        challenge_name = challenge.title
        submission = get_submission_model(message["submission_pk"])
        participant_team_name = submission.participant_team.team_name
        phase_name = submission.challenge_phase.name
        message = {
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
        send_slack_notification(slack_url, message)
    return response
