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
    sqs = boto3.resource('sqs',
                         endpoint_url=os.environ.get('AWS_SQS_ENDPOINT', 'http://sqs:9324'),
                         region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))

    AWS_SQS_QUEUE_NAME = os.environ.get('AWS_SQS_QUEUE_NAME', 'evalai_submission_queue')
    # Check if the FIFO queue exists. If no, then create one
    try:
        queue = sqs.get_queue_by_name(QueueName=AWS_SQS_QUEUE_NAME)
    except botocore.exceptions.ClientError as ex:
        if ex.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            if settings.DEBUG:
                queue = sqs.create_queue(QueueName=AWS_SQS_QUEUE_NAME)
            else:
                # create a FIFO queue in the production environment
                name = AWS_SQS_QUEUE_NAME + '.fifo'
                queue = sqs.create_queue(
                    QueueName=name,
                    Attributes={
                        'FifoQueue': 'true',
                        'ContentBasedDeduplication': 'true'
                    }
                )
        else:
            logger.info("Cannot get or create Queue")
    return queue


def publish_add_challenge_message(challenge_id):
    """
    Args:
        challenge_id: Challenge Id

    Returns:
        Returns SQS response
    """
    message = {
        'challenge_id': challenge_id,
    }

    queue = get_or_create_sqs_queue()
    AWS_SQS_MESSAGE_GROUP_ID = os.environ.get('AWS_SQS_MESSAGE_GROUP_ID', 'evalai_msg_group')
    response = queue.send_message(
        MessageBody=json.dumps(message),
        MessageGroupId=AWS_SQS_MESSAGE_GROUP_ID,
    )
    return response
