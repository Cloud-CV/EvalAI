import os
import time
import pytz
import requests
import warnings

from datetime import datetime
from auto_stop_workers import start_worker, stop_worker
from prometheus_api_client import PrometheusConnect

warnings.filterwarnings("ignore")

utc = pytz.UTC
NUM_PROCESSED_SUBMISSIONS = "num_processed_submissions"
NUM_SUBMISSIONS_IN_QUEUE = "num_submissions_in_queue"
PROMETHEUS_URL = os.environ.get(
    "MONITORING_API_URL", "https://monitoring-staging.eval.ai/prometheus/"
)
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
]

ENV = os.environ.get("ENV", "dev")

evalai_endpoint = os.environ.get("API_HOST_URL")
authorization_header = {
    "Authorization": "Bearer {}".format(os.environ.get("AUTH_TOKEN"))
}

prom = PrometheusConnect(url=PROMETHEUS_URL, disable_ssl=True)


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
            "No workers and queue messages found for Challenge ID: {}, Title: {}. Skipping.".format(
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

    num_workers = (
        0 if challenge["workers"] is None else int(challenge["workers"])
    )

    print(
        "Num Workers: {}, Queue Length: {}".format(num_workers, queue_length)
    )

    if (
        queue_length == 0
        or datetime.fromisoformat(challenge["end_date"][:-1])
        < datetime.utcnow()
    ):
        scale_down_workers(challenge, num_workers)
    else:
        scale_up_workers(challenge, num_workers)


# TODO: Factor in limits for the APIs
def scale_up_or_down_workers_for_challenges(response):
    for challenge in response["results"]:
        if (
            not challenge["is_docker_based"]
            and not challenge["remote_evaluation"]
        ):
            if ENV == "prod":
                if challenge["queue"] not in PROD_EXCLUDED_CHALLENGE_QUEUES:
                    scale_up_or_down_workers(challenge)
            else:
                scale_up_or_down_workers(challenge)
            time.sleep(1)

        else:
            print(
                "Challenge ID: {}, Title: {} is either docker-based or remote-evaluation. Skipping.".format(
                    challenge["id"], challenge["title"]
                )
            )


# Cron Job
def start_job():
    response = get_challenges()
    scale_up_or_down_workers_for_challenges(response)
    next_page = response["next"]
    while next_page is not None:
        response = execute_get_request(next_page)
        scale_up_or_down_workers_for_challenges(response)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting worker auto scaling script")
    start_job()
    print("Quitting worker auto scaling script!")
