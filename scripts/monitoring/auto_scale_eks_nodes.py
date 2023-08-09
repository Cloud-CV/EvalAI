import json
import os
import time
import warnings
from datetime import datetime

import boto3
import pytz
from dateutil.parser import parse
from evalai_interface import EvalAI_Interface

warnings.filterwarnings("ignore")

utc = pytz.UTC

DEFAULT_AWS_EKS_KEYS = {  # NOTE: These are habitat challenge keys as most challenges are habitat
    "AWS_ACCOUNT_ID": os.environ.get("EKS_AWS_ACCOUNT_ID"),
    "AWS_ACCESS_KEY_ID": os.environ.get("EKS_AWS_ACCESS_KEY_ID"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("EKS_AWS_SECRET_ACCESS_KEY"),
    "AWS_REGION": os.environ.get("EKS_AWS_REGION"),
    "AWS_STORAGE_BUCKET_NAME": os.environ.get("EKS_AWS_STORAGE_BUCKET_NAME"),
}

SCALE_UP_DESIRED_SIZE = 1

# Env Variables
ENV = os.environ.get("ENV", "production")
AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
EVALAI_ENDPOINT = os.environ.get("API_HOST_URL", "https://eval.ai")

json_path = os.environ.get("JSON_PATH", "~/prod_eks_auth_tokens.json")
# QUEUES
with open(json_path, "r") as f:
    # Load the JSON data into a Python dictionary
    INCLUDED_CHALLENGE_PKS = json.load(f)


def create_evalai_interface(auth_token):
    evalai_interface = EvalAI_Interface(auth_token, EVALAI_ENDPOINT)
    return evalai_interface


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


def start_eks_worker(challenge, pending_submissions, evalai_interface, aws_keys, new_desired_size):
    eks_client, cluster_name, nodegroup_name = get_eks_meta(
        challenge, evalai_interface, aws_keys
    )
    scaling_config = {
        "minSize": 1,
        "maxSize": max(new_desired_size, pending_submissions),
        "desiredSize": new_desired_size,
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


def get_pending_submission_count_by_pk(metrics, challenge_pk):
    challenge_metrics = metrics[str(challenge_pk)]
    pending_submissions = 0
    for status in ["running", "submitted", "queued", "resuming"]:
        pending_submissions += challenge_metrics.get(status, 0)
    return pending_submissions


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
            "No workers and pending submissions found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def scale_up_workers(challenge, original_desired_size, pending_submissions, evalai_interface, aws_keys, new_desired_size):
    if original_desired_size < new_desired_size:
        response = start_eks_worker(
            challenge, pending_submissions, evalai_interface, aws_keys, new_desired_size
        )
        print("AWS API Response: {}".format(response))
        print(
            "Increased nodegroup sizes for Challenge ID: {}, Title: {}.".format(
                challenge["id"], challenge["title"]
            )
        )
    else:
        print(
            "Existing workers and pending submissions found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def scale_up_or_down_workers(challenge, metrics, evalai_interface, aws_keys, scale_up_desired_size):
    try:
        pending_submissions = get_pending_submission_count_by_pk(metrics, challenge["id"])
    except Exception:  # noqa: F841
        print(
            "Unable to get the pending submissions for challenge ID: {}, Title: {}. Skipping.".format(
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
    original_desired_size = scaling_config["desiredSize"]
    print(
        "Challenge ID : {}, Title: {}".format(
            challenge["id"], challenge["title"]
        )
    )
    print(
        "Min Size: {}, Desired Size: {}, Pending Submissions: {}".format(
            min_size, original_desired_size, pending_submissions
        )
    )

    if pending_submissions == 0 or parse(challenge["end_date"]) < pytz.UTC.localize(
        datetime.utcnow()
    ):
        scale_down_workers(challenge, original_desired_size, evalai_interface, aws_keys)
    else:
        if pending_submissions > original_desired_size:
            # Scale up again if needed, up to the maximum allowed scale_up_desired_size (if provided)
            new_desired_size = min(pending_submissions, scale_up_desired_size)
            scale_up_workers(
                challenge,
                original_desired_size,
                pending_submissions,
                evalai_interface,
                aws_keys,
                new_desired_size,
            )
        else:
            print(
                "Existing workers and pending submissions found for Challenge ID: {}, Title: {}. Skipping.".format(
                    challenge["id"], challenge["title"]
                )
            )


# Cron Job
def start_job():

    # Get metrics
    evalai_interface = create_evalai_interface(AUTH_TOKEN)
    metrics = evalai_interface.get_challenges_submission_metrics()

    for challenge_id, details in INCLUDED_CHALLENGE_PKS.items():
        # Auth Token
        if "auth_token" not in details:
            raise NotImplementedError("auth_token is needed for all challenges")

        # Desired Scale Up Size
        if "scale_up_desired_size" not in details:
            scale_up_desired_size = SCALE_UP_DESIRED_SIZE
        else:
            scale_up_desired_size = details["scale_up_desired_size"]

        # AWS Keys
        if "aws_keys" in details:
            aws_keys = details["aws_keys"]
        else:
            aws_keys = DEFAULT_AWS_EKS_KEYS

        evalai_interface = create_evalai_interface(details["auth_token"])
        challenge = evalai_interface.get_challenge_by_pk(challenge_id)

        assert (
            challenge["is_docker_based"] and not challenge["remote_evaluation"]
        ), "Challenge ID: {}, Title: {} is either not docker-based or remote-evaluation. Skipping.".format(
            challenge["id"], challenge["title"]
        )
        scale_up_or_down_workers(challenge, metrics, evalai_interface, aws_keys, scale_up_desired_size)
        time.sleep(1)


if __name__ == "__main__":
    print("Starting EKS nodegroup auto scaling script")
    start_job()
    print("Quitting EKS nodegroup auto scaling script!")
