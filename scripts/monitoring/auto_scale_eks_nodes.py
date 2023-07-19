import json
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

DEFAULT_AWS_EKS_KEYS = {  # NOTE: These are habitat challenge keys as most challenges are habitat
    "AWS_ACCOUNT_ID": os.environ.get("EKS_AWS_ACCOUNT_ID"),
    "AWS_ACCESS_KEY_ID": os.environ.get("EKS_AWS_ACCESS_KEY_ID"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("EKS_AWS_SECRET_ACCESS_KEY"),
    "AWS_REGION": os.environ.get("EKS_AWS_REGION"),
    "AWS_STORAGE_BUCKET_NAME": os.environ.get("EKS_AWS_STORAGE_BUCKET_NAME"),
}

# Env Variables
ENV = os.environ.get("ENV", "production")
# AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
EVALAI_ENDPOINT = os.environ.get("API_HOST_URL", "https://eval.ai")
PROMETHEUS_URL = os.environ.get(
    "MONITORING_API_URL", "https://monitoring.eval.ai/prometheus/"
)

json_path = os.environ.get("JSON_PATH", "~/prod_eks_auth_tokens.json")
# QUEUES
with open(json_path, "r") as f:
    # Load the JSON data into a Python dictionary
    INCLUDED_CHALLENGE_PKS = json.load(f)

NUM_PROCESSED_SUBMISSIONS = "num_processed_submissions"
NUM_SUBMISSIONS_IN_QUEUE = "num_submissions_in_queue"


def create_evalai_interface(auth_token):
    evalai_interface = EvalAI_Interface(auth_token, EVALAI_ENDPOINT)
    return evalai_interface


prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)


def get_boto3_client(resource, aws_keys):
    client = boto3.client(
        resource,
        region_name=aws_keys["AWS_REGION"],
        aws_access_key_id=aws_keys["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=aws_keys["AWS_SECRET_ACCESS_KEY"],
    )
    return client


def get_nodegroup_name(eks_client, cluster_name):
    nodegroup_list = eks_client.list_nodegroups(clusterName=cluster_name)
    return nodegroup_list["nodegroups"][0]


def get_eks_meta(challenge, evalai_interface, aws_keys):
    # TODO: Check if eks_client should be a global thing. Clients must have an expiry/timeout.
    eks_client = get_boto3_client("eks", aws_keys)
    cluster_name = evalai_interface.get_aws_eks_cluster_details(
        challenge["id"]
    )["name"]
    nodegroup_name = get_nodegroup_name(eks_client, cluster_name)
    return eks_client, cluster_name, nodegroup_name


def get_scaling_config(eks_client, cluster_name, nodegroup_name):
    nodegroup_desc = eks_client.describe_nodegroup(
        clusterName=cluster_name, nodegroupName=nodegroup_name
    )
    scaling_config = nodegroup_desc["nodegroup"]["scalingConfig"]
    return scaling_config


def start_eks_worker(challenge, queue_length, evalai_interface, aws_keys):
    eks_client, cluster_name, nodegroup_name = get_eks_meta(
        challenge, evalai_interface, aws_keys
    )
    scaling_config = {
        "minSize": 1,
        "maxSize": max(1, queue_length),
        "desiredSize": min(1, queue_length),
    }
    response = eks_client.update_nodegroup_config(
        clusterName=cluster_name,
        nodegroupName=nodegroup_name,
        scalingConfig=scaling_config,
    )
    return response


def stop_eks_worker(challenge, evalai_interface, aws_keys):
    eks_client, cluster_name, nodegroup_name = get_eks_meta(
        challenge, evalai_interface, aws_keys
    )
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


def scale_down_workers(challenge, desired_size, evalai_interface, aws_keys):
    if desired_size > 0:
        response = stop_eks_worker(challenge, evalai_interface, aws_keys)
        print("AWS API Response: {}".format(response))
        print(
            "Decreased nodegroup sizes for Challenge ID: {}, Title: {}.".format(
                challenge["id"], challenge["title"]
            )
        )
    else:
        print(
            "No workers and queue messages found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def scale_up_workers(challenge, desired_size, queue_length, evalai_interface, aws_keys):
    if desired_size == 0:
        response = start_eks_worker(challenge, queue_length, evalai_interface, aws_keys)
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


def scale_up_or_down_workers(challenge, evalai_interface, aws_keys):
    try:
        queue_length = get_queue_length_by_challenge(challenge)
    except Exception:  # noqa: F841
        print(
            "Unable to get the queue length for challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )
        return

    eks_client, cluster_name, nodegroup_name = get_eks_meta(
        challenge, evalai_interface, aws_keys
    )
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
        scale_down_workers(challenge, desired_size, evalai_interface, aws_keys)
    else:
        scale_up_workers(
            challenge, desired_size, queue_length, evalai_interface, aws_keys
        )


# Cron Job
def start_job():

    for challenge_id, details in INCLUDED_CHALLENGE_PKS.items():
        if "auth_token" not in details:
            raise NotImplementedError("auth_token is needed for all challenges")
        evalai_interface = create_evalai_interface(details["auth_token"])
        challenge = evalai_interface.get_challenge_by_pk(challenge_id)
        if "aws_keys" in details:
            aws_keys = details["aws_keys"]
        else:
            aws_keys = DEFAULT_AWS_EKS_KEYS
        assert (
            challenge["is_docker_based"] and not challenge["remote_evaluation"]
        ), "Challenge ID: {}, Title: {} is either not docker-based or remote-evaluation. Skipping.".format(
            challenge["id"], challenge["title"]
        )
        scale_up_or_down_workers(challenge, evalai_interface, aws_keys)
        time.sleep(1)


if __name__ == "__main__":
    print("Starting EKS nodegroup auto scaling script")
    start_job()
    print("Quitting EKS nodegroup auto scaling script!")
