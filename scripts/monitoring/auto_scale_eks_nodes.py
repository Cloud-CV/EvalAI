import os
import time
import warnings
from datetime import datetime

import boto3
import pytz
from dateutil.parser import parse
from evalai_interface import EvalAI_Interface
from prometheus_api_client import PrometheusConnect

warnings.filterwarnings("ignore")

utc = pytz.UTC

# # TODO: Currently, I am assuming we have environment variables for the AWS keys.
# Need to check if we want to consider the `use_host_credentials` case.
# Or if we can provide just environment variables for this.
AWS_EKS_KEYS = {
    "AWS_ACCOUNT_ID": os.environ.get("EKS_AWS_ACCOUNT_ID"),
    "AWS_ACCESS_KEY_ID": os.environ.get("EKS_AWS_ACCESS_KEY_ID"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("EKS_AWS_SECRET_ACCESS_KEY"),
    "AWS_REGION": os.environ.get("EKS_AWS_REGION"),
    "AWS_STORAGE_BUCKET_NAME": os.environ.get("EKS_AWS_STORAGE_BUCKET_NAME"),
}

# Env Variables
ENV = os.environ.get("ENV", "production")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
EVALAI_ENDPOINT = os.environ.get("API_HOST_URL", "https://eval.ai")
PROMETHEUS_URL = os.environ.get(
    "MONITORING_API_URL", "https://monitoring.eval.ai/prometheus/"
)

# QUEUES
PROD_INCLUDED_CHALLENGE_PKS = [802, 1820, 1615]
DEV_INCLUDED_CHALLENGE_PKS = []

NUM_PROCESSED_SUBMISSIONS = "num_processed_submissions"
NUM_SUBMISSIONS_IN_QUEUE = "num_submissions_in_queue"

authorization_header = {"Authorization": "Bearer {}".format(AUTH_TOKEN)}

prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)

evalai_interface = EvalAI_Interface(AUTH_TOKEN, EVALAI_ENDPOINT)


def get_boto3_client(resource, aws_keys):
    client = boto3.client(
        resource,
        region_name=aws_keys["AWS_REGION"],
        aws_access_key_id=aws_keys["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=aws_keys["AWS_SECRET_ACCESS_KEY"],
    )
    return client


def get_nodegroup_name(challenge):
    environment_suffix = "{}-{}".format(challenge["id"], ENV)
    nodegroup_name = "{}-{}-nodegroup".format(
        challenge["title"].replace(" ", "-")[:20], environment_suffix
    )
    return nodegroup_name


def get_eks_meta(challenge):
    # TODO: Check if eks_client should be a global thing. Clients must have an expiry/timeout.
    # Maybe it is better to re-create for every challenge. Not sure about this.
    eks_client = get_boto3_client("eks", AWS_EKS_KEYS)
    cluster_name = evalai_interface.get_aws_eks_cluster_details(
        challenge["id"]
    )["name"]
    nodegroup_name = get_nodegroup_name(challenge)
    return eks_client, cluster_name, nodegroup_name


def get_scaling_config(eks_client, cluster_name, nodegroup_name):
    nodegroup_desc = eks_client.describe_nodegroup(
        clusterName=cluster_name, nodegroupName=nodegroup_name
    )
    scaling_config = nodegroup_desc["nodegroup"]["scalingConfig"]
    return scaling_config


def start_eks_worker(challenge, queue_length):
    eks_client, cluster_name, nodegroup_name = get_eks_meta(challenge)
    scaling_config = {
        "minSize": 1,
        "maxSize": max(5, queue_length),
        "desiredSize": min(5, queue_length),
    }
    response = eks_client.update_nodegroup_config(
        clusterName=cluster_name,
        nodegroupName=nodegroup_name,
        scalingConfig=scaling_config,
    )
    return response


def stop_eks_worker(challenge):
    eks_client, cluster_name, nodegroup_name = get_eks_meta(challenge)
    scaling_config = {
        "minSize": 0,
        "maxSize": 1,
        "desiredSize": 0,
    }
    response = eks_client.update_nodegroup_config(
        clusterName=cluster_name,
        nodegroupName=nodegroup_name,
        scalingConfig=scaling_config,
    )
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


def scale_down_workers(challenge, desired_size):
    if desired_size > 0:
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


def scale_up_workers(challenge, desired_size, queue_length):
    if desired_size == 0:
        response = start_eks_worker(challenge, queue_length)
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
    desired_size = scaling_config["desiredSize"]
    print(
        "Challenge ID : {}, Title: {}".format(
            challenge["id"], challenge["title"]
        )
    )
    print(
        "Min Size: {}, Desired Size: {}, Queue Length: {}".format(
            min_size, desired_size, queue_length
        )
    )

    if queue_length == 0 or parse(challenge["end_date"]) < pytz.UTC.localize(
        datetime.utcnow()
    ):
        scale_down_workers(challenge, desired_size)
    else:
        scale_up_workers(challenge, desired_size, queue_length)


# Cron Job
def start_job():
    if ENV == "production":
        pks = PROD_INCLUDED_CHALLENGE_PKS
    else:
        pks = DEV_INCLUDED_CHALLENGE_PKS

    for challenge_id in pks:
        challenge = evalai_interface.get_challenge_by_pk(challenge_id)
        assert (
            challenge["is_docker_based"] and not challenge["remote_evaluation"]
        ), "Challenge ID: {}, Title: {} is either not docker-based or remote-evaluation. Skipping.".format(
            challenge["id"], challenge["title"]
        )
        scale_up_or_down_workers(challenge)
        time.sleep(1)


if __name__ == "__main__":
    print("Starting EKS nodegroup auto scaling script")
    start_job()
    print("Quitting EKS nodegroup auto scaling script!")
