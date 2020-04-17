import datetime
import logging
import os
import requests
import tempfile
import urllib.request

from base.utils import get_model_object
from challenges.utils import get_challenge_model, get_challenge_phase_model
from django.utils import timezone
from participants.utils import get_participant_team_id_of_user_for_a_challenge
from rest_framework import status
from .constants import submission_status_to_exclude
from .models import Submission
from .serializers import SubmissionSerializer

get_submission_model = get_model_object(Submission)

logger = logging.getLogger(__name__)


def get_remaining_submission_for_a_phase(
    user, challenge_phase_pk, challenge_pk
):
    """
    Returns the number of remaining submissions that a participant can
    do daily, monthly and in total to a particular challenge phase of a
    challenge.
    """

    get_challenge_model(challenge_pk)
    challenge_phase = get_challenge_phase_model(challenge_phase_pk)
    participant_team_pk = get_participant_team_id_of_user_for_a_challenge(
        user, challenge_pk
    )

    # Conditional check for the existence of participant team of the user.
    if not participant_team_pk:
        response_data = {"error": "You haven't participated in the challenge"}
        return response_data, status.HTTP_403_FORBIDDEN

    max_submissions_count = challenge_phase.max_submissions
    max_submissions_per_month_count = challenge_phase.max_submissions_per_month
    max_submissions_per_day_count = challenge_phase.max_submissions_per_day

    submissions_done = Submission.objects.filter(
        challenge_phase__challenge=challenge_pk,
        challenge_phase=challenge_phase_pk,
        participant_team=participant_team_pk,
    ).exclude(status__in=submission_status_to_exclude)

    submissions_done_this_month = submissions_done.filter(
        submitted_at__gte=timezone.now().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
    )

    # Get the submissions_done_today by midnight time of the day
    submissions_done_today = submissions_done.filter(
        submitted_at__gte=timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    )

    submissions_done_count = submissions_done.count()
    submissions_done_this_month_count = submissions_done_this_month.count()
    submissions_done_today_count = submissions_done_today.count()

    # Check for maximum submission limit
    if submissions_done_count >= max_submissions_count:
        response_data = {
            "message": "You have exhausted maximum submission limit!",
            "submission_limit_exceeded": True,
        }
        return response_data, status.HTTP_200_OK

    # Check for monthy submission limit
    elif submissions_done_this_month_count >= max_submissions_per_month_count:
        date_time_now = timezone.now()
        next_month_start_date_time = date_time_now + datetime.timedelta(
            days=+30
        )
        next_month_start_date_time = next_month_start_date_time.replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        remaining_time = next_month_start_date_time - date_time_now

        if submissions_done_today_count >= max_submissions_per_day_count:
            response_data = {
                "message": "Both daily and monthly submission limits are exhausted!",
                "remaining_time": remaining_time,
            }
        else:
            response_data = {
                "message": "You have exhausted this month's submission limit!",
                "remaining_time": remaining_time,
            }
        return response_data, status.HTTP_200_OK

    # Checks if #today's successful submission is greater than or equal to max submission per day
    elif submissions_done_today_count >= max_submissions_per_day_count:
        date_time_now = timezone.now()
        date_time_tomorrow = date_time_now + datetime.timedelta(1)
        # Get the midnight time of the day i.e. 12:00 AM of next day.
        midnight = date_time_tomorrow.replace(hour=0, minute=0, second=0)
        remaining_time = midnight - date_time_now

        response_data = {
            "message": "You have exhausted today's submission limit!",
            "remaining_time": remaining_time,
        }
        return response_data, status.HTTP_200_OK

    else:
        # calculate the remaining submissions from total submissions.
        remaining_submission_count = (
            max_submissions_count - submissions_done_count
        )
        # Calculate the remaining submissions for current month.
        remaining_submissions_this_month_count = (
            max_submissions_per_month_count - submissions_done_this_month_count
        )
        # Calculate the remaining submissions for today.
        remaining_submissions_today_count = (
            max_submissions_per_day_count - submissions_done_today_count
        )

        remaining_submissions_this_month_count = min(
            remaining_submission_count, remaining_submissions_this_month_count
        )
        remaining_submissions_today_count = min(
            remaining_submissions_this_month_count,
            remaining_submissions_today_count,
        )

        response_data = {
            "remaining_submissions_this_month_count": remaining_submissions_this_month_count,
            "remaining_submissions_today_count": remaining_submissions_today_count,
            "remaining_submissions_count": remaining_submission_count,
        }
        return response_data, status.HTTP_200_OK


def is_url_valid(url):
    """
    Checks that a given URL is reachable.
    :param url: A URL
    :return type: bool
    """
    request = urllib.request.Request(url)
    request.get_method = lambda: "HEAD"
    try:
        urllib.request.urlopen(request)
        return True
    except urllib.request.HTTPError:
        return False


def get_file_from_url(url):
    """ Get file object from a url """

    BASE_TEMP_DIR = tempfile.mkdtemp()
    file_name = url.split("/")[-1]
    file_path = os.path.join(BASE_TEMP_DIR, file_name)
    file_obj = {}
    headers = {"user-agent": "Wget/1.16 (linux-gnu)"}
    response = requests.get(url, stream=True, headers=headers)
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    file_obj["name"] = file_name
    file_obj["temp_dir_path"] = BASE_TEMP_DIR
    return file_obj


def handle_submission_rerun(submission, updated_status):
    """
    Function to handle the submission re-running. It is handled in the following way -
    1. Invalidate the old submission
    2. Create a new submission object for the re-running submission

    Arguments:
        submission {Submission Model class object} -- submission object
        updated_status {str} -- Updated status for current submission
    """

    data = {"status": updated_status}
    serializer = SubmissionSerializer(submission, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()

    submission.pk = None
    submission.stdout_file = None
    submission.stderr_file = None
    submission.submission_result_file = None
    submission.submission_metadata_file = None
    submission.save()
    message = {
        "challenge_pk": submission.challenge_phase.challenge.pk,
        "phase_pk": submission.challenge_phase.pk,
        "submission_pk": submission.pk,
    }

    if submission.challenge_phase.challenge.is_docker_based:
        try:
            response = requests.get(submission.input_file)
        except Exception:
            logger.exception("Failed to get input_file")
            return

        if response and response.status_code == 200:
            message["submitted_image_uri"] = response.json()[
                "submitted_image_uri"
            ]
    return message
