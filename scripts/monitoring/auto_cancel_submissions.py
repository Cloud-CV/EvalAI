from datetime import datetime, timedelta
import time
import pytz  # Use this to handle timezones if needed
import os
from evalai_interface import EvalAI_Interface


def get_submission_time(submission):
    # Get the submission time based on the presence of "rerun_resumed_at"
    if "rerun_resumed_at" in submission and submission["rerun_resumed_at"]:
        return datetime.strptime(submission["rerun_resumed_at"], "%Y-%m-%dT%H:%M:%S.%fZ")

    else:
        return datetime.strptime(submission["submitted_at"], "%Y-%m-%dT%H:%M:%S.%fZ")


def auto_cancel_submissions(challenge_pk, days_threshold=14):
    """
    Auto-cancels submissions that have statuses "submitted" or "running" for more than `days_threshold` days,
    considering the "rerun_resumed_at" time if available, otherwise using the "submitted_at" time.
    :param challenge_pk: The challenge primary key for which submissions should be checked.
    :param days_threshold: The number of days after which submissions should be canceled (default is 14).
    """
    try:
        evalai = EvalAI_Interface(AUTH_TOKEN, EVALAI_API_SERVER)

        submissions = evalai.get_submissions_for_challenge(
            challenge_pk, "submitted"
        )
        submissions += evalai.get_submissions_for_challenge(
            challenge_pk, "running"
        )
        submissions += evalai.get_submissions_for_challenge(
            challenge_pk, "resuming"
        )

        current_time = datetime.now(pytz.utc)
        for submission in submissions:
            status = submission["status"]
            submission_time = get_submission_time(submission)
            submission_time = pytz.utc.localize(submission_time)

            time_difference = current_time - submission_time
            if time_difference > timedelta(days=days_threshold):
                data = {
                    "submission": submission["id"],
                    "submission_status": "cancelled",
                }
                evalai.update_submission_data(data, challenge_pk)
                print(
                    f"Cancelled submission with PK {submission['id']}. Previous status: {status}. Time Lapsed: {time_difference}"
                )
                time.sleep(1)
    except Exception as e:
        raise (f"Error in auto-cancel script: {str(e)}")


# Example usage:
if __name__ == "__main__":
    # Provide your AUTH_TOKEN and EVALAI_API_SERVER
    AUTH_TOKEN = os.environ.get("AUTH_TOKEN")
    EVALAI_API_SERVER = os.environ.get("API_HOST_URL")

    # Initialize the EvalAI_Interface
    evalai = EvalAI_Interface(AUTH_TOKEN, EVALAI_API_SERVER)

    all_challenge_endpoint = "{}/api/challenges/challenge/all/all/all".format(
        EVALAI_API_SERVER
    )

    # Get all challenges
    challenges = []
    next_page = all_challenge_endpoint
    while next_page:
        response = evalai.make_request(next_page, "GET")
        challenges.extend(response["results"])
        next_page = response["next"]

    # Loop through all challenges and run the auto-cancel script for each challenge
    for challenge in challenges:
        challenge_pk = challenge["id"]
        print(f"Running auto-cancel script for challenge {challenge_pk}")
        auto_cancel_submissions(challenge_pk)
        time.sleep(5)
