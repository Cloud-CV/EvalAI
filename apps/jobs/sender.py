from __future__ import absolute_import

import boto3
import botocore
import json
import logging
import os

from django.conf import settings

from challenges.models import Challenge

logger = logging.getLogger(__name__)


def get_or_create_sqs_queue(queue_name):
    """
    Args:
        queue_name: Name of the SQS Queue
    Returns:
        Returns the SQS Queue object
    """
    if settings.DEBUG or settings.TEST:
        sqs = boto3.resource('sqs',
                             endpoint_url=os.environ.get('AWS_SQS_ENDPOINT', 'http://sqs:9324'),
                             region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                             aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY', 'x'),
                             aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID', 'x'),)
        # Use default queue name in dev and test environment
        queue_name = 'evalai_submission_queue'
    else:
        sqs = boto3.resource('sqs',
                             region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                             aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                             aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),)

    if queue_name == '':
        queue_name = 'evalai_submission_queue'

    # Check if the queue exists. If not, then create one.
    try:
        queue = sqs.get_queue_by_name(QueueName=queue_name)
    except botocore.exceptions.ClientError as ex:
        if ex.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            queue = sqs.create_queue(QueueName=queue_name)
        else:
            logger.exception('Cannot get or create Queue')
    return queue


def publish_submission_message(challenge_id, phase_id, submission_id):
    """
    Args:
        challenge_id: Challenge Id
        phase_id: Challenge Phase Id
        submission_id: Submission Id

    Returns:
        Returns SQS response
    """
    message = {
        'challenge_id': challenge_id,
        'phase_id': phase_id,
        'submission_id': submission_id,
    }

    try:
        challenge = Challenge.objects.get(pk=challenge_id)
    except Challenge.DoesNotExist:
        logger.exception('Challenge does not exist for the given id {}'.format(challenge_id))
        return

    queue_name = challenge.queue
    queue = get_or_create_sqs_queue(queue_name)
    response = queue.send_message(MessageBody=json.dumps(message))
    return response
