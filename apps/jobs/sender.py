from __future__ import absolute_import

from django.conf import settings

import json
import logging
import os

import botocore
import boto3


logger = logging.getLogger(__name__)


def get_or_create_sqs_queue():
    """
    Returns:
        Returns the SQS Queue object
    """
    if settings.DEBUG or settings.TEST:
        sqs = boto3.resource('sqs',
                             endpoint_url=os.environ.get('AWS_SQS_ENDPOINT', 'http://sqs:9324'),
                             region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                             aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                             aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),)
    else:
        sqs = boto3.resource('sqs',
                             region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'),
                             aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY'),
                             aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),)

    AWS_SQS_QUEUE_NAME = os.environ.get('AWS_SQS_QUEUE_NAME', 'evalai_submission_queue')
    # Check if the queue exists. If no, then create one
    try:
        queue = sqs.get_queue_by_name(QueueName=AWS_SQS_QUEUE_NAME)
    except botocore.exceptions.ClientError as ex:
        if ex.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            queue = sqs.create_queue(QueueName=AWS_SQS_QUEUE_NAME)
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

    queue = get_or_create_sqs_queue()
    response = queue.send_message(MessageBody=json.dumps(message))
    return response
