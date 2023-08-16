import os
import pytz
import warnings
import boto3
from datetime import datetime
from dateutil.parser import parse
from evalai_interface import EvalAI_Interface

warnings.filterwarnings("ignore")

utc = pytz.UTC

ENV = os.environ.get("ENV", "dev")
evalai_endpoint = os.environ.get("API_HOST_URL", "http://localhost:8000")
auth_token = os.environ.get(
    "AUTH_TOKEN",
)
CHALLENGE_EXCLUDE = [
    356,
    830,
]

aws_keys = {
    "AWS_ACCOUNT_ID": os.environ.get("AWS_ACCOUNT_ID", "x"),
    "AWS_ACCESS_KEY_ID": os.environ.get("AWS_ACCESS_KEY_ID", "x"),
    "AWS_SECRET_ACCESS_KEY": os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
    "AWS_REGION": os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
    "AWS_STORAGE_BUCKET_NAME": os.environ.get(
        "AWS_STORAGE_BUCKET_NAME", "evalai-s3-bucket"
    ),
}


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


def stop_instance(challenge, evalai_interface):
    instance_details = evalai_interface.get_ec2_instance_details(challenge["id"])
    instance = instance_details["message"]
    if instance["State"]["Name"] == "running":
        response = evalai_interface.stop_challenge_ec2_instance(challenge["id"])
        print("AWS API Response: {}".format(response))
        print(
            "Stopped EC2 instance for Challenge ID: {}, Title: {}".format(
                challenge["id"], challenge["title"]
            )
        )
    else:
        print(
            "No running EC2 instance and pending messages found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def start_instance(challenge, evalai_interface):
    instance_details = evalai_interface.get_ec2_instance_details(challenge["id"])
    instance = instance_details["message"]
    if instance["State"]["Name"] == "stopped":
        response = evalai_interface.start_challenge_ec2_instance(challenge["id"])
        print("AWS API Response: {}".format(response))
        print(
            "Started EC2 instance for Challenge ID: {}, Title: {}.".format(
                challenge["id"], challenge["title"]
            )
        )
    else:
        print(
            "Existing running EC2 instance and pending messages found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def start_or_stop_workers(challenge, challenge_metrics, evalai_interface):
    try:
        pending_submissions = get_pending_submission_count(challenge_metrics)
    except Exception:  # noqa: F841
        print(
            "Unable to get the pending submissions for challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )
        return

    print("Pending Submissions: {}, Challenge PK: {}, Title: {}".format(pending_submissions, challenge["id"], challenge["title"]))

    if (challenge["id"] in CHALLENGE_EXCLUDE):
        if pending_submissions == 0 or parse(
            challenge["end_date"]
        ) < pytz.UTC.localize(datetime.utcnow()):
            custom__instance_interface(challenge, "stop")
        else:
            custom__instance_interface(challenge, "start")

    if pending_submissions == 0 or parse(
        challenge["end_date"]
    ) < pytz.UTC.localize(datetime.utcnow()):
        stop_instance(challenge, evalai_interface)
    else:
        start_instance(challenge, evalai_interface)


# TODO: Factor in limits for the APIs
def start_or_stop_workers_for_challenges(response, metrics, evalai_interface):
    for challenge in response["results"]:
        if challenge["uses_ec2_worker"] or (challenge["id"] in CHALLENGE_EXCLUDE):
            start_or_stop_workers(challenge, metrics[str(challenge["id"])], evalai_interface)


def custom__instance_interface(challenge, action):
    client = get_boto3_client("ec2", aws_keys)
    instance_name = "Worker-Instance-production-{}".format(challenge["id"])
    ec2 = client.describe_instances(
        Filters=[{"Name": instance_name }]
    )
    state = ec2["Reservations"]["Instances"]["State"]["Name"]
    id = ec2["Reservations"]["Instances"]["InstanceId"]

    if action == "start" and (state == "stopped"):
        client.start_instances(InstanceIds=[id])
        print("Started EC2 instance for Challenge ID: {}, Title: {}.".format(
            challenge["id"], challenge["title"]))
    elif action == "stop" and (state == "running"):
        client.stop_instances(InstanceIds=[id])
        print("Stopped EC2 instance for Challenge ID: {}, Title: {}.".format(
            challenge["id"], challenge["title"]))
    else:
        print("Instance is already in the desired state. Skipping.")


def create_evalai_interface(auth_token, evalai_endpoint):
    evalai_interface = EvalAI_Interface(auth_token, evalai_endpoint)
    return evalai_interface


# Cron Job
def start_job():
    evalai_interface = create_evalai_interface(auth_token, evalai_endpoint)
    response = evalai_interface.get_challenges()
    metrics = evalai_interface.get_challenges_submission_metrics()
    start_or_stop_workers_for_challenges(response, metrics, evalai_interface)
    next_page = response["next"]
    while next_page is not None:
        response = evalai_interface.make_request(next_page, "GET")
        start_or_stop_workers_for_challenges(response, metrics, evalai_interface)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting EC2 workers auto scaling script")
    start_job()
    print("Quitting EC2 workers auto scaling script!")
