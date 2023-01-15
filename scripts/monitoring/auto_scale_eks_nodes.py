import os
import time
import warnings
from datetime import datetime

import boto3
import pytz
import requests
from dateutil.parser import parse
from prometheus_api_client import PrometheusConnect

from scripts.workers.worker_utils import EvalAI_Interface

warnings.filterwarnings("ignore")

utc = pytz.UTC
NUM_PROCESSED_SUBMISSIONS = "num_processed_submissions"
NUM_SUBMISSIONS_IN_QUEUE = "num_submissions_in_queue"
PROMETHEUS_URL = os.environ.get(
    "MONITORING_API_URL", "https://monitoring-staging.eval.ai/prometheus/"
)

PROD_INCLUDED_CHALLENGE_QUEUES = [
    "habitat-rearrangement-challenge-2022-1820-production-e900ef02-eeb1-439a-b4a4-833",
    "habitat-challenge-2022-1615-production-be08fce5-72a7-40bc-aa2e-4df7b3380a8a",
]
DEV_INCLUDED_CHALLENGE_QUEUES = [
    "habitat-challenge-2022-696-staging-2e5f7385-a6a8-43d6-a1b5-5f7b9948d97a"
]

ENV = os.environ.get("ENV", "dev")

DOWN_SCALING_CONFIG = {"minSize": 0, "maxSize": 0, "desiredSize": 0}

evalai_endpoint = os.environ.get("API_HOST_URL")
authorization_header = {
    "Authorization": "Bearer {}".format(os.environ.get("AUTH_TOKEN"))
}

prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

# TODO: Currently, I am assuming we have environment variables for the AWS keys.
# Need to check if we want to consider the `use_host_credentials` case.
# Or if we can provide just environment variables for this.
aws_keys = {
    "AWS_ACCOUNT_ID": os.environ.get("AWS_ACCOUNT_ID"),
    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY"),
    "AWS_REGION": os.environ.get("AWS_REGION"),
    "AWS_STORAGE_BUCKET_NAME": os.environ.get("AWS_STORAGE_BUCKET_NAME"),
}


def get_boto3_client(resource, aws_keys):
    client = boto3.client(
        resource,
        region_name=aws_keys["AWS_REGION"],
        aws_access_key_id=aws_keys["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=aws_keys["AWS_SECRET_ACCESS_KEY"],
    )
    return client


def get_challenge_evaluation_cluster_details(challenge):
    evalai_interface = EvalAI_Interface(
        os.environ.get("AUTH_TOKEN"), evalai_endpoint, challenge["queue"]
    )
    challenge_evaluation_cluster = (
        evalai_interface.get_aws_eks_cluster_details(challenge["id"])
    )
    return challenge_evaluation_cluster


def get_cluster_name(challenge):
    challenge_evaluation_cluster = get_challenge_evaluation_cluster_details(
        challenge
    )
    cluster_name = challenge_evaluation_cluster["name"]
    return cluster_name


def get_nodegroup_name(challenge):
    environment_suffix = "{}-{}".format(challenge["id"], ENV)
    nodegroup_name = "{}-{}-nodegroup".format(
        challenge["title"].replace(" ", "-")[:20], environment_suffix
    )
    return nodegroup_name


def get_eks_meta(challenge):
    # TODO: Check if eks_client should be a global thing. Clients must have an expiry/timeout.
    # Maybe it is better to re-create for every challenge. Not sure about this.
    eks_client = get_boto3_client("eks", aws_keys)
    cluster_name = get_cluster_name(challenge)
    nodegroup_name = get_nodegroup_name(challenge)
    return eks_client, cluster_name, nodegroup_name


def get_scaling_config(eks_client, cluster_name, nodegroup_name):
    nodegroup_desc = eks_client.describe_nodegroup(
        clusterName=cluster_name, nodegroupName=nodegroup_name
    )
    scaling_config = nodegroup_desc["nodegroup"]["scalingConfig"]
    return scaling_config


def start_eks_worker(challenge):
    eks_client, cluster_name, nodegroup_name = get_eks_meta(challenge)
    scaling_config = {
        "minSize": challenge["min_worker_instance"],
        "maxSize": challenge["max_worker_instance"],
        "desiredSize": challenge["desired_worker_instance"],
    }
    response = eks_client.update_nodegroup_config(
        clusterName=cluster_name,
        nodegroupName=nodegroup_name,
        scalingConfig=scaling_config,
    )
    return response


def stop_eks_worker(challenge):
    eks_client, cluster_name, nodegroup_name, _ = get_eks_meta(challenge)
    response = eks_client.update_nodegroup_config(
        clusterName=cluster_name,
        nodegroupName=nodegroup_name,
        scalingConfig=DOWN_SCALING_CONFIG,
    )
    return response


def execute_get_request(url):
    response = requests.get(url, headers=authorization_header)
    return response.json()


def get_challenges():
    all_challenge_endpoint = "{}/api/challenges/challenge/all/all/all".format(
        evalai_endpoint
    )
    response = execute_get_request(all_challenge_endpoint)

    return response


def get_queue_length(queue_name):
    try:
        num_processed_submissions = int(
            prom.custom_query(
                f"num_processed_submissions{{queue_name='{queue_name}'}}"
            )[0]["value"][1]
        )
    except Exception:  # noqa: F841
        num_processed_submissions = 0

    try:
        num_submissions_in_queue = int(
            prom.custom_query(
                f"num_submissions_in_queue{{queue_name='{queue_name}'}}"
            )[0]["value"][1]
        )
    except Exception:  # noqa: F841
        num_submissions_in_queue = 0

    return num_submissions_in_queue - num_processed_submissions


def get_queue_length_by_challenge(challenge):
    queue_name = challenge["queue"]
    return get_queue_length(queue_name)


def scale_down_workers(challenge, min_size):
    if min_size > 0:
        response = stop_eks_worker(challenge)
        print("AWS API Response: {}".format(response))
        print(
            "Stopped EKS worker for Challenge ID: {}, Title: {}".format(
                challenge["id"], challenge["title"]
            )
        )
    else:
        print(
            "No workers and queue messages found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def scale_up_workers(challenge, min_size):
    if min_size == 0:
        response = start_eks_worker(challenge)
        print("AWS API Response: {}".format(response))
        print(
            "Increased nodegroup sizes for Challenge ID: {}, Title: {}.".format(
                challenge["id"], challenge["title"]
            )
        )
    else:
        print(
            "Existing workers and pending queue messages found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def scale_up_or_down_workers(challenge):
    try:
        queue_length = get_queue_length_by_challenge(challenge)
    except Exception:  # noqa: F841
        print(
            "Unable to get the queue length for challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )
        return

    eks_client, cluster_name, nodegroup_name = get_eks_meta(challenge)
    scaling_config = get_scaling_config(
        eks_client, cluster_name, nodegroup_name
    )
    min_size = scaling_config["minSize"]

    print("Min Size: {}, Queue Length: {}".format(min_size, queue_length))

    if queue_length == 0 or parse(challenge["end_date"]) < pytz.UTC.localize(
        datetime.utcnow()
    ):
        scale_down_workers(challenge, min_size)
    else:
        scale_up_workers(challenge, min_size)


# TODO: Factor in limits for the APIs
def scale_up_or_down_nodes_for_eks_challenges(response):
    for challenge in response["results"]:
        if challenge["is_docker_based"] and not challenge["remote_evaluation"]:
            if ENV == "prod":
                if challenge["queue"] in PROD_INCLUDED_CHALLENGE_QUEUES:
                    scale_up_or_down_workers(challenge)
            else:
                if challenge["queue"] in PROD_INCLUDED_CHALLENGE_QUEUES:
                    scale_up_or_down_workers(challenge)
            time.sleep(1)

        else:
            print(
                "Challenge ID: {}, Title: {} is either not docker-based or remote-evaluation. Skipping.".format(
                    challenge["id"], challenge["title"]
                )
            )


# Cron Job
def start_job():
    response = get_challenges()
    scale_up_or_down_nodes_for_eks_challenges(response)
    next_page = response["next"]
    while next_page is not None:
        response = execute_get_request(next_page)
        scale_up_or_down_nodes_for_eks_challenges(response)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting EKS nodegroup auto scaling script")
    start_job()
    print("Quitting EKS nodegroup auto scaling script!")
