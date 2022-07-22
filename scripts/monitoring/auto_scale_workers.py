import os
import re
import time
import uuid
import pytz
import requests

import boto3

from django.conf import settings
import botocore

# from auto_stop_workers import start_worker, stop_worker

utc = pytz.UTC


# Eval AI related credentials
evalai_endpoint = os.environ.get("API_HOST_URL")
authorization_header = {
    "Authorization": "Bearer {}".format(os.environ.get("AUTH_TOKEN"))
}


def execute_get_request(url):
    response = requests.get(url, headers=authorization_header)
    return response.json()


def get_challenges():
    all_challenge_endpoint = (
        "{}/api/challenges/challenge/all/unapproved/all".format(
            evalai_endpoint  # Gets all unapproved challenges
        )
    )
    response = execute_get_request(all_challenge_endpoint)

    return response.json()


# TODO: Check if we can use challenge["queue"] directly to get queue name.
# TODO: Understand if all the attributes are exposed in the API calls, or are they done selectively.
def get_sqs_queue_by_name(queue_name):
    """
    Returns:
        Returns the SQS Queue object
    """

    sqs = boto3.resource(
        "sqs",
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    )
    if queue_name == "":
        raise ValueError("Queue Name cannot be empty")

    try:
        queue = sqs.get_queue_by_name(QueueName=queue_name)
    except botocore.exceptions.ClientError as ex:
        if (
            ex.response["Error"]["Code"]
            != "AWS.SimpleQueueService.NonExistentQueue"
        ):
            raise Exception("Cannot get queue: {}".format(queue_name))
    return queue


def get_queue_name(param, challenge_pk):
    """
    Generate unique SQS queue name of max length 80 for a challenge

    Arguments:
        param {string} -- challenge title
        challenge_pk {int} -- challenge primary key

    Returns:
        {string} -- unique queue name
    """
    # The max-length for queue-name is 80 in SQS
    max_len = 80
    max_challenge_title_len = 50

    env = settings.ENVIRONMENT
    queue_name = param.replace(" ", "-").lower()[:max_challenge_title_len]
    queue_name = re.sub(r"\W+", "-", queue_name)

    queue_name = "{}-{}-{}-{}".format(
        queue_name, challenge_pk, env, uuid.uuid4()
    )[:max_len]
    return queue_name


def get_queue_length(queue):
    # TODO: Check if we should use approximate number of messages
    # https://github.com/boto/boto3/issues/599
    # Ref: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/sqs.html#using-an-existing-queue
    count = 0
    for message in queue.receive_messages():
        count += 1


def get_queue_length_by_challenge(challenge):
    queue_name = challenge["queue"]
    queue = get_sqs_queue_by_name(queue_name)
    return get_queue_length(queue)


def get_aws_credentials_for_challenge(challenge):
    """
    Return the AWS credentials for a challenge using challenge pk
    Arguments:
        challenge {dict} -- challenge json for which credentials are to be fetched
    Returns:
        aws_key {dict} -- Dict containing aws keys for a challenge
    """
    if not challenge["use_host_credentials"]:
        aws_keys = {
            "AWS_ACCOUNT_ID": settings.AWS_ACCOUNT_ID,
            "AWS_ACCESS_KEY_ID": settings.AWS_ACCESS_KEY_ID,
            "AWS_SECRET_ACCESS_KEY": settings.AWS_SECRET_ACCESS_KEY,
            "AWS_REGION": settings.AWS_REGION,
            "AWS_STORAGE_BUCKET_NAME": settings.AWS_STORAGE_BUCKET_NAME,
        }
    return aws_keys


def get_boto3_client(resource, aws_keys):
    """
    Returns the boto3 client for a resource in AWS
    Arguments:
        resource {str} -- Name of the resource for which client is to be created
        aws_keys {dict} -- AWS keys which are to be used
    Returns:
        Boto3 client object for the resource
    """
    try:
        client = boto3.client(
            resource,
            region_name=aws_keys["AWS_REGION"],
            aws_access_key_id=aws_keys["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=aws_keys["AWS_SECRET_ACCESS_KEY"],
        )
        return client
    except Exception as e:
        raise e


def increase_or_decrease_workers(challenge):
    # challenge_aws_keys = get_aws_credentials_for_challenge(challenge)
    queue_length = get_queue_length_by_challenge(challenge)
    if queue_length > 0:
        # set instances to 1
        # print statement
        pass
    else:
        # set instances to 0
        # print statement
        pass


# TODO: Factor in limits for the APIs
def increase_or_decrease_workers_for_challenges(response):
    for challenge in response["results"]:
        if not challenge["use_host_credentials"]:
            increase_or_decrease_workers(challenge)
            time.sleep(2)


# Cron Job
def start_job():
    response = get_challenges()
    increase_or_decrease_workers(response)
    next_page = response["next"]
    while next_page is not None:
        response = execute_get_request(next_page)
        increase_or_decrease_workers(response)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting worker auto scaling script")
    start_job()
    print("Quitting worker auto scaling script!")
