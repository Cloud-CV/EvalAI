import json
import os

import boto3


def publish_submission_message(challenge_id, phase_id, submission_id):
    """
    Args:
        challenge_id: Challenge Id
        phase_id: Challenge Phase Id
        submission_id: Submission Id

    Returns:
        Returns SQS response
    """
    sqs = boto3.resource('sqs')
    AWS_SQS_QUEUE_NAME = os.environ.get('AWS_SQS_QUEUE_NAME')
    AWS_SQS_MESSAGE_GROUP_ID = os.environ.get('AWS_SQS_MESSAGE_GROUP_ID')
    queue = sqs.get_queue_by_name(QueueName=AWS_SQS_QUEUE_NAME)

    message = {
        'challenge_id': challenge_id,
        'phase_id': phase_id,
        'submission_id': submission_id,
    }

    response = queue.send_message(
        MessageBody=json.dumps(message),
        MessageGroupId=AWS_SQS_MESSAGE_GROUP_ID,
    )

    # TODO: Replace print statements with logging
    print(response.get('MessageId'))
    print(response.get('MD5OfMessageBody'))
    return response
