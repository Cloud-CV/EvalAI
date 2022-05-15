import os
import pytz
import requests
import time

from datetime import datetime
from dateutil import parser

utc = pytz.UTC
evalai_endpoint = os.environ.get("API_HOST_URL")
authorization_header = {
    "Authorization": "Bearer {}".format(os.environ.get("AUTH_TOKEN"))
}


def execute_get_request(url):
    response = requests.get(url, headers=authorization_header)
    return response.json()


def start_worker(challenge_id):
    start_worker_endpoint = "{}/api/challenges/{}/manage_worker/start/".format(
        evalai_endpoint, challenge_id
    )
    response = requests.put(
        start_worker_endpoint, headers=authorization_header
    )
    return response


def stop_worker(challenge_id):
    stop_worker_endpoint = "{}/api/challenges/{}/manage_worker/stop/".format(
        evalai_endpoint, challenge_id
    )
    response = requests.put(stop_worker_endpoint, headers=authorization_header)
    return response


def delete_worker(challenge_id):
    delete_worker_endpoint = (
        "{}/api/challenges/{}/manage_worker/delete/".format(
            evalai_endpoint, challenge_id
        )
    )
    response = requests.put(
        delete_worker_endpoint, headers=authorization_header
    )
    return response


def get_challenges():
    all_challenge_endpoint = "{}/api/challenges/challenge/all/unapproved/all".format(
        evalai_endpoint
    )
    response = requests.get(
        all_challenge_endpoint, headers=authorization_header
    )
    return response.json()


def is_unapproved_challenge(workers, approved_by_admin, created_at):
    current_date = utc.localize(datetime.now())
    return (
        workers is not None
        and not approved_by_admin
        and (current_date - created_at).days >= 2
    )


def stop_workers_for_challenges(response):
    for challenge in response["results"]:
        challenge_id = challenge["id"]
        workers = challenge["workers"]
        approved_by_admin = challenge["approved_by_admin"]
        is_docker_based = challenge["is_docker_based"]
        challenge_end_date = parser.parse(challenge["end_date"])
        created_at = parser.parse(challenge["created_at"])
        current_date = utc.localize(datetime.now())

        print(
            "Start/Stop submission worker for challenge id {}".format(
                challenge_id
            )
        )
        if not is_docker_based:
            # Delete workers for challenges uploaded in last 3 days that are unapproved or inactive challenges
            if (
                workers is not None and challenge_end_date < current_date
            ) or is_unapproved_challenge(
                workers, approved_by_admin, created_at
            ):
                response = delete_worker(challenge_id)
                if not response.ok:
                    print(
                        "ERROR: Delete worker failed for challenge id {}!".format(
                            challenge_id
                        )
                    )
        # Add 2 second delay after every request to avoid throttling the backend server
        time.sleep(2)


def start_job():
    response = get_challenges()
    stop_workers_for_challenges(response)

    next_page = response["next"]
    while next_page is not None:
        response = execute_get_request(next_page)
        stop_workers_for_challenges(response)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting worker auto start/stop script")
    start_job()
    print("Quitting worker auto start/stop script!")
