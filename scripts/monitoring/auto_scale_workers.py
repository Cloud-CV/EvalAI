import os
import time
import pytz
import requests

import boto3

import botocore

from auto_stop_workers import start_worker, stop_worker

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
    all_challenge_endpoint = "{}/api/challenges/challenge/all/all/all".format(
        evalai_endpoint  # Gets all challenges
    )
    response = execute_get_request(all_challenge_endpoint)

    return response


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
    queue = None
    try:
        queue = sqs.get_queue_by_name(QueueName=queue_name)
    except botocore.exceptions.ClientError as ex:
        if (
            ex.response["Error"]["Code"]
            != "AWS.SimpleQueueService.NonExistentQueue"
        ):
            raise Exception(
                "Unable to fetch {} queue details.".format(queue_name)
            )
    return queue


def get_queue_length(queue):
    # TODO: Check if we should use approximate number of messages
    # https://github.com/boto/boto3/issues/599
    # Ref: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/sqs.html#using-an-existing-queue
    # Ref: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sqs.html#SQS.Queue.attributes
    return int(queue.attributes["ApproximateNumberOfMessages"]) + int(
        queue.attributes["ApproximateNumberOfMessagesNotVisible"]
    )


def get_queue_length_by_challenge(challenge):
    queue_name = challenge["queue"]
    try:
        queue = get_sqs_queue_by_name(queue_name)
    except Exception as _e:  # noqa: F841
        raise Exception(
            "Unable to fetch queue with name: {}. Skipping.".format(queue_name)
        )
    return get_queue_length(queue)


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
    try:
        queue_length = get_queue_length_by_challenge(challenge)
    except Exception as _e:  # noqa: F841
        print(
            "Unable to get the queue length for challenge ID: {}. Skipping.".format(
                challenge["id"]
            )
        )
        return

    if queue_length == 0:
        if int(challenge["workers"]) > 0:
            # Worker > 0 and Queue = 0 - Stop
            # stop worker
            stop_worker(challenge["id"])
            print("Stopped worker for challenge: {}".format(challenge["id"]))
        else:
            # Worker = 0 and Queue = 0
            print(
                "No workers and queue messages found for challenge: {}. Skipping.".format(
                    challenge["id"]
                )
            )

    else:
        # Worker = 0, Queue > 0
        if challenge["workers"] is None or int(challenge["workers"]) == 0:
            # start worker
            start_worker(challenge["id"])
            print("Started worker for challenge: {}".format(challenge["id"]))
        else:
            # Worker > 0 and Queue > 0
            print(
                "Existing workers and pending queue messages found for challenge: {}. Skipping.".format(
                    challenge["id"]
                )
            )


# TODO: Factor in limits for the APIs
def increase_or_decrease_workers_for_challenges(response):
    for challenge in response["results"]:
        if (
            not challenge["is_docker_based"]
            and not challenge["remote_evaluation"]
        ):
            increase_or_decrease_workers(challenge)
            time.sleep(2)


# Cron Job
def start_job():
    response = get_challenges()
    increase_or_decrease_workers_for_challenges(response)
    next_page = response["next"]
    while next_page is not None:
        response = execute_get_request(next_page)
        increase_or_decrease_workers_for_challenges(response)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting worker auto scaling script")
    start_job()
    print("Quitting worker auto scaling script!")
