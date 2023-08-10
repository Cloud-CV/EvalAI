import os
import pytz
import warnings
import boto3
from datetime import datetime
from dateutil.parser import parse
from evalai_interface import EvalAI_Interface

warnings.filterwarnings("ignore")

utc = pytz.UTC

aws_keys = {
    "AWS_ACCOUNT_ID": os.environ.get("AWS_ACCOUNT_ID", "x"),
    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "x"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
    "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    "AWS_STORAGE_BUCKET_NAME": os.environ.get(
        "AWS_STORAGE_BUCKET_NAME", "evalai-s3-bucket"
    ),
}


ENV = os.environ.get("ENV", "dev")

evalai_endpoint = os.environ.get("API_HOST_URL", "http://localhost:8000")
auth_token = os.environ.get(
    "AUTH_TOKEN",
)


def get_boto3_client(resource, aws_keys):
    client = boto3.client(
        resource,
        region_name=aws_keys["AWS_REGION"],
        aws_access_key_id=aws_keys["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=aws_keys["AWS_SECRET_ACCESS_KEY"],
    )
    return client


def get_pending_submission_count(challenge_metrics):
    pending_submissions = 0
    for status in ["running", "submitted", "queued", "resuming"]:
        pending_submissions += challenge_metrics.get(status, 0)
    return pending_submissions


def stop_workers(challenge):
    target_instance_name = "Worker-Instance-{}-{}".format(
        ENV, challenge["id"]
    )

    ec2 = get_boto3_client("ec2", aws_keys)
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [target_instance_name]},
            {"Name": "instance-state-name", "Values": ["running"]},
        ]
    )

    instances = [
        instance
        for reservation in response["Reservations"]
        for instance in reservation["Instances"]
    ]

    if instances:
        for instance in instances:
            instance_id = instance["InstanceId"]
            response = ec2.stop_instances(InstanceIds=[instance_id])
            print("AWS API Response: {}".format(response))
            print(
                "Stopped worker for Challenge ID: {}, Title: {}".format(
                    challenge["id"], challenge["title"]
                )
            )
    else:
        print(
            "No running instances with the specified name found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def start_workers(challenge):
    target_instance_name = "Worker-Instance-{}-{}".format(
        ENV, challenge["id"]
    )

    ec2 = get_boto3_client("ec2", aws_keys)
    response = ec2.describe_instances(
        Filters=[
            {"Name": "tag:Name", "Values": [target_instance_name]},
            {"Name": "instance-state-name", "Values": ["stopped"]},
        ]
    )

    instances = [
        instance
        for reservation in response["Reservations"]
        for instance in reservation["Instances"]
    ]

    if instances:
        for instance in instances:
            instance_id = instance["InstanceId"]
            response = ec2.start_instances(InstanceIds=[instance_id])
            print("AWS API Response: {}".format(response))
            print(
                "Started worker for Challenge ID: {}, Title: {}.".format(
                    challenge["id"], challenge["title"]
                )
            )
    else:
        print(
            "No stopped instances with the specified name found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def start_or_stop_workers(challenge, challenge_metrics):
    try:
        pending_submissions = get_pending_submission_count(challenge_metrics)
    except Exception:  # noqa: F841
        print(
            "Unable to get the pending submissions for challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )
        return

    print("Pending Submissions: {}".format(pending_submissions))

    if pending_submissions == 0 or parse(
        challenge["end_date"]
    ) < pytz.UTC.localize(datetime.utcnow()):
        stop_workers(challenge)
    else:
        start_workers(challenge)


# TODO: Factor in limits for the APIs
def start_or_stop_workers_for_challenges(response, metrics):
    for challenge in response["results"]:
        if challenge["uses_ec2_worker"]:
            start_or_stop_workers(challenge, metrics[str(challenge["id"])])


def create_evalai_interface(auth_token, evalai_endpoint):
    evalai_interface = EvalAI_Interface(auth_token, evalai_endpoint)
    return evalai_interface


# Cron Job
def start_job():
    evalai_interface = create_evalai_interface(auth_token, evalai_endpoint)
    response = evalai_interface.get_challenges()
    metrics = evalai_interface.get_challenges_submission_metrics()
    start_or_stop_workers_for_challenges(response, metrics)
    next_page = response["next"]
    while next_page is not None:
        response = evalai_interface.make_request(next_page, "GET")
        start_or_stop_workers_for_challenges(response, metrics)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting worker auto scaling script")
    start_job()
    print("Quitting worker auto scaling script!")
