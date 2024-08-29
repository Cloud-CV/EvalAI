import json
import os
import warnings
from datetime import datetime

import pytz
from auto_stop_workers import delete_worker, start_worker, stop_worker
from dateutil.parser import parse
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


def empty_challenge_workers(challenge_id, evalai_interface):
    data = {
        "challenge_pk": challenge_id,
        "workers": None,
        "task_def_arn": None,
    }
    payload = json.dumps(data)
    response = evalai_interface.update_challenge_attributes(payload)


def scale_down_workers(challenge, num_workers, evalai_interface):
    if num_workers > 0:
        try:
            response = stop_worker(challenge["id"])
            response_json = response.json()
            print(f"AWS API Response: {response_json}")

            action = response_json.get("action", None)
            if action:
                error = response_json.get("error", {})
                error_message = error.get("Message", "")
                error_code = error.get("Code", "")
            else:
                error = response_json.get("error", "")

            if action == "Failure":
                if error_code == "ServiceNotFoundException":
                    print(f"AWS API Response: {response_json}")
                    print(
                        f"Service not found for Challenge ID: {challenge['id']}."
                    )

                elif error_message == "TaskDefinition not found.":
                    print(f"AWS API Response: {response_json}")
                    print(
                        f"Task Definition not found for Challenge ID: {challenge['id']}."
                    )
                print("Emptying challenge workers at backend.")
                empty_challenge_workers(challenge["id"], evalai_interface)

            elif (
                "error" in response_json
                and "Action stop worker is not supported for an inactive challenge."
                in response_json["error"]
            ):
                print(
                    f"Challenge has ended for Challenge ID: {challenge['id']}. Deleting workers."
                )
                delete_response = delete_worker(challenge["id"])
                print(f"Delete response: {delete_response.json()}")
                empty_challenge_workers(challenge["id"], evalai_interface)

            else:
                print(
                    f"Stopped worker for Challenge ID: {challenge['id']}, Title: {challenge['title']}"
                )

        except Exception as e:
            print(
                f"Error handling response for Challenge ID: {challenge['id']}, Title: {challenge['title']}."
            )
            print(f"Error Details: {str(e)}")

    else:
        print(
            f"No workers and pending messages found for Challenge ID: {challenge['id']}, Title: {challenge['title']}. Skipping."
        )


def scale_up_workers(challenge, num_workers, evalai_interface):
    if num_workers == 0:
        response = start_worker(challenge["id"])
        print("AWS API Response: {}".format(response.json()))
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


def scale_up_or_down_workers(challenge, challenge_metrics, evalai_interface):
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
        "Num Workers: {}, Pending Submissions: {}".format(
            num_workers, pending_submissions
        )
    )

    if (
        pending_submissions == 0
        or parse(challenge["end_date"]) < pytz.UTC.localize(datetime.utcnow())
        or challenge["remote_evaluation"]
        or challenge["uses_ec2_worker"]
    ):
        scale_down_workers(challenge, num_workers, evalai_interface)
    else:
        scale_up_workers(challenge, num_workers, evalai_interface)


# TODO: Factor in limits for the APIs
def scale_up_or_down_workers_for_challenge(
    challenge, challenge_metrics, evalai_interface
):
    if ENV == "prod":
        try:
            scale_up_or_down_workers(
                challenge, challenge_metrics, evalai_interface
            )
        except Exception as e:
            print(e)
    else:
        try:
            scale_up_or_down_workers(
                challenge, challenge_metrics, evalai_interface
            )
        except Exception as e:
            print(e)


def scale_up_or_down_workers_for_challenges(response, evalai_interface):
    for challenge in response["results"]:
        try:
            challenge_metrics = (
                evalai_interface.get_challenge_submission_metrics_by_pk(
                    challenge["id"]
                )
            )
            scale_up_or_down_workers_for_challenge(
                challenge, challenge_metrics, evalai_interface
            )
        except Exception as e:
            print(e)


def create_evalai_interface(auth_token, evalai_endpoint):
    evalai_interface = EvalAI_Interface(auth_token, evalai_endpoint)
    return evalai_interface


# Cron Job
def start_job():
    evalai_interface = create_evalai_interface(auth_token, evalai_endpoint)
    response = evalai_interface.get_challenges()
    scale_up_or_down_workers_for_challenges(response, evalai_interface)
    next_page = response["next"]
    while next_page is not None:
        response = evalai_interface.make_request(next_page, "GET")
        scale_up_or_down_workers_for_challenges(response, evalai_interface)
        next_page = response["next"]


if __name__ == "__main__":
    print("Starting worker auto scaling script")
    start_job()
    print("Quitting worker auto scaling script!")
