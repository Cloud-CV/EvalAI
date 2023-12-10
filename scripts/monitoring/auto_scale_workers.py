import os
import pytz
import warnings

from datetime import datetime
from dateutil.parser import parse
from auto_stop_workers import start_worker, stop_worker
from evalai_interface import EvalAI_Interface

warnings.filterwarnings("ignore")

utc = pytz.UTC

ENV = os.environ.get("ENV", "dev")

evalai_endpoint = os.environ.get("API_HOST_URL")
auth_token = os.environ.get("AUTH_TOKEN")


def get_pending_submission_count(challenge_metrics):
    pending_submissions = 0
    for status in ["running", "submitted", "queued", "resuming"]:
        pending_submissions += challenge_metrics.get(status, 0)
    return pending_submissions


def scale_down_workers(challenge, num_workers):
    if num_workers > 0:
        response = stop_worker(challenge["id"])
        print("AWS API Response: {}".format(response))
        print(
            "Stopped worker for Challenge ID: {}, Title: {}".format(
                challenge["id"], challenge["title"]
            )
        )
    else:
        print(
            "No workers and pending messages found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def scale_up_workers(challenge, num_workers):
    if num_workers == 0:
        response = start_worker(challenge["id"])
        print("AWS API Response: {}".format(response))
        print(
            "Started worker for Challenge ID: {}, Title: {}.".format(
                challenge["id"], challenge["title"]
            )
        )
    else:
        print(
            "Existing workers and pending messages found for Challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )


def scale_up_or_down_workers(challenge, challenge_metrics):
    try:
        pending_submissions = get_pending_submission_count(challenge_metrics)
    except Exception:  # noqa: F841
        print(
            "Unable to get the pending submissions for challenge ID: {}, Title: {}. Skipping.".format(
                challenge["id"], challenge["title"]
            )
        )
        return

    num_workers = (
        0 if challenge["workers"] is None else int(challenge["workers"])
    )

    print(
        "Num Workers: {}, Pending Submissions: {}".format(num_workers, pending_submissions)
    )

    if (
        pending_submissions == 0
        or parse(challenge["end_date"])
        < pytz.UTC.localize(datetime.utcnow())
    ):
        scale_down_workers(challenge, num_workers)
    else:
        scale_up_workers(challenge, num_workers)


# TODO: Factor in limits for the APIs
def scale_up_or_down_workers_for_challenges(response, metrics):
    for challenge in response["results"]:
        if ENV == "prod":
            try:
                if challenge["remote_evaluation"] is False:
                    scale_up_or_down_workers(challenge, metrics[str(challenge["id"])])
            except Exception as e:
                print(e)
        else:
            try:
                scale_up_or_down_workers(challenge, metrics[str(challenge["id"])])
            except Exception as e:
                print(e)


def create_evalai_interface(auth_token, evalai_endpoint):
    evalai_interface = EvalAI_Interface(auth_token, evalai_endpoint)
    return evalai_interface


# Cron Job
def start_job():
    evalai_interface = create_evalai_interface(auth_token, evalai_endpoint)
    response = evalai_interface.get_challenges()
    metrics = evalai_interface.get_challenges_submission_metrics()
    scale_up_or_down_workers_for_challenges(response, metrics)
    next_page = response["next"]
    while next_page is not None:
        response = evalai_interface.make_request(next_page, "GET")
        scale_up_or_down_workers_for_challenges(response, metrics)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting worker auto scaling script")
    start_job()
    print("Quitting worker auto scaling script!")
