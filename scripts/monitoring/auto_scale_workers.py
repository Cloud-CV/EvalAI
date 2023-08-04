import os
import pytz
import warnings

from datetime import datetime
from dateutil.parser import parse
from auto_stop_workers import start_worker, stop_worker
from evalai_interface import EvalAI_Interface

warnings.filterwarnings("ignore")

utc = pytz.UTC
PROD_EXCLUDED_CHALLENGE_QUEUES = [
    "textvqa-challenge-2021-874-production-41966973-4d99-4326-a402-b749b1d89aad",
    "vqa-challenge-2021-830-production-6343db53-af82-4618-8c51-0e294611315a",
    "ego4d-state-change-object-detection-challenge-1632",
    "argoverse-3d-tracking-competition-52b36364-110d-47f1-8fa7-8873aa2d9965",
    "argoverse-motion-forecasting-competition-81d1a3c6-f7b3-4830-9dcf-3ccc9f29d3a6",
    "argoverse-3d-detection-competition-725-71837a72-afb0-4403-9cfc-bb3e80d733ab",
    "argoverse-stereo-competition-917-production-884becea-a882-43bd-8ac7-0561bd705c4e",
    "nuscenes-prediction-challenge-448a7b5e-6b08-4587-9293-ac07a530b426",
    "nuscenes-detection-challenge-510c8c6d-a0d2-40bd-95dd-b7c8ea593d03",
    "gqa-real-world-visual-reasoning-challenge-2019-2e1c901b-5d86-4516-b82d-8d98",
    "nocaps-xd-9f4bead9-b3d6-4207-8e68-a6807d786c3c",
    "nocaps-18b403b5-8946-4319-9fc1-758981f7f724",
    "nuscenes-tracking-challenge-b1ea8e46-cee9-4591-856a-7c31947d74ed",
    "ego4d-poc-your-challenge-name--1637-production-bfb81565-71fd-4b7b-949d-2560dd523",
    "ego4d-poc-your-challenge-name--1624-production-6e1419b9-f909-4428-951d-6e927676f",
    "dialoglue-708-d2225333-1ade-41c5-bb0c-c02c15d43e05",
    "vizwiz-caption-challenge-2021-739-production-a6420029-bf1c-4339-9c55-36a8913cca8",
    "textcaps-challenge-2020-906-production-fcc74455-ce3e-4622-b6fe-0340bcc3d228",
    "vizwiz-vqa-challenge-2021-743-production-862e0cf8-0611-4aa5-a05a-14e07576a513",
    "cvpr2023-bdd100k-multiple-object-tracking-challeng-1989-production-cdba4595-fb13",
]

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
            if challenge["queue"] not in PROD_EXCLUDED_CHALLENGE_QUEUES:
                scale_up_or_down_workers(challenge, metrics[str(challenge["id"])])
        else:
            scale_up_or_down_workers(challenge, metrics[str(challenge["id"])])


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
