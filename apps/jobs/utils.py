import datetime
import logging
import os
import requests
import tempfile
import urllib.request
from django.db.models import FloatField, Q, F, fields, ExpressionWrapper
from django.db.models.expressions import RawSQL
from django.utils import timezone
from rest_framework import status

from challenges.models import ChallengePhaseSplit, LeaderboardData
from participants.models import ParticipantTeam

from base.utils import get_model_object, suppress_autotime
from challenges.utils import get_challenge_model, get_challenge_phase_model
from hosts.utils import is_user_a_host_of_challenge
from participants.utils import get_participant_team_id_of_user_for_a_challenge

from .constants import submission_status_to_exclude
from .models import Submission
from .serializers import SubmissionSerializer

get_submission_model = get_model_object(Submission)
get_challenge_phase_split_model = get_model_object(ChallengePhaseSplit)

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
    with suppress_autotime(submission, ["submitted_at"]):
        submission.submitted_at = submission.submitted_at
        submission.save()

    message = {
        "challenge_pk": submission.challenge_phase.challenge.pk,
        "phase_pk": submission.challenge_phase.pk,
        "submission_pk": submission.pk,
    }

    if submission.challenge_phase.challenge.is_docker_based:
        try:
            response = requests.get(submission.input_file.url)
        except Exception:
            logger.exception("Failed to get input_file")
            return

        if response and response.status_code == 200:
            message["submitted_image_uri"] = response.json()[
                "submitted_image_uri"
            ]
    return message


def calculate_distinct_sorted_leaderboard_data(
    user, challenge_obj, challenge_phase_split, only_public_entries
):
    """
    Function to calculate and return the sorted leaderboard data

    Arguments:
        user {[Class object]} -- User model object
        challenge_obj {[Class object]} -- Challenge model object
        challenge_phase_split {[Class object]} -- Challenge phase split model object
        only_public_entries {[Boolean]} -- Boolean value to determine if the user wants to include private entries or not

    Returns:
        [list] -- Ranked list of participant teams to be shown on leaderboard
        [status] -- HTTP status code (200/400)
    """
    # Get the leaderboard associated with the Challenge Phase Split
    leaderboard = challenge_phase_split.leaderboard

    # Get the default order by key to rank the entries on the leaderboard
    try:
        default_order_by = leaderboard.schema["default_order_by"]
    except KeyError:
        response_data = {
            "error": "Sorry, default_order_by key is missing in leaderboard schema!"
        }
        return response_data, status.HTTP_400_BAD_REQUEST

    # Exclude the submissions done by members of the host team
    # while populating leaderboard
    challenge_hosts_emails = (
        challenge_obj.creator.get_all_challenge_host_email()
    )
    is_challenge_phase_public = challenge_phase_split.challenge_phase.is_public
    # Exclude the submissions from challenge host team to be displayed on the leaderboard of public phases
    challenge_hosts_emails = (
        [] if not is_challenge_phase_public else challenge_hosts_emails
    )

    challenge_host_user = is_user_a_host_of_challenge(user, challenge_obj.pk)

    all_banned_email_ids = challenge_obj.banned_email_ids

    # Check if challenge phase leaderboard is public for participant user or not
    if (
        challenge_phase_split.visibility != ChallengePhaseSplit.PUBLIC
        and not challenge_host_user
    ):
        response_data = {"error": "Sorry, the leaderboard is not public!"}
        return response_data, status.HTTP_400_BAD_REQUEST

    leaderboard_data = LeaderboardData.objects.exclude(
        Q(submission__created_by__email__in=challenge_hosts_emails)
        & Q(submission__is_baseline=False)
    )

    # Get all the successful submissions related to the challenge phase split
    all_valid_submission_status = [Submission.FINISHED]

    # Handle the case for challenges with partial submission evaluation feature
    if (
        challenge_phase_split.challenge_phase.is_partial_submission_evaluation_enabled
    ):
        all_valid_submission_status.append(Submission.PARTIALLY_EVALUATED)

    leaderboard_data = leaderboard_data.filter(
        challenge_phase_split=challenge_phase_split,
        submission__is_flagged=False,
        submission__status__in=all_valid_submission_status,
    ).order_by("-created_at")

    if challenge_phase_split.show_execution_time:
        time_diff_expression = ExpressionWrapper(F('submission__completed_at') - F('submission__started_at'), output_field=fields.DurationField())
        leaderboard_data = leaderboard_data.annotate(
            filtering_score=RawSQL(
                "result->>%s", (default_order_by,), output_field=FloatField()
            ),
            filtering_error=RawSQL(
                "error->>%s",
                ("error_{0}".format(default_order_by),),
                output_field=FloatField(),
            ),
            submission__execution_time=time_diff_expression
        ).values(
            "id",
            "submission__participant_team",
            "submission__participant_team__team_name",
            "submission__participant_team__team_url",
            "submission__is_baseline",
            "submission__is_public",
            "challenge_phase_split",
            "result",
            "error",
            "filtering_score",
            "filtering_error",
            "leaderboard__schema",
            "submission__submitted_at",
            "submission__method_name",
            "submission__id",
            "submission__submission_metadata",
            "submission__execution_time"
        )
    else:
        leaderboard_data = leaderboard_data.annotate(
            filtering_score=RawSQL(
                "result->>%s", (default_order_by,), output_field=FloatField()
            ),
            filtering_error=RawSQL(
                "error->>%s",
                ("error_{0}".format(default_order_by),),
                output_field=FloatField(),
            ),
        ).values(
            "id",
            "submission__participant_team",
            "submission__participant_team__team_name",
            "submission__participant_team__team_url",
            "submission__is_baseline",
            "submission__is_public",
            "challenge_phase_split",
            "result",
            "error",
            "filtering_score",
            "filtering_error",
            "leaderboard__schema",
            "submission__submitted_at",
            "submission__method_name",
            "submission__id",
            "submission__submission_metadata",
        )
    if only_public_entries:
        if challenge_phase_split.visibility == ChallengePhaseSplit.PUBLIC:
            leaderboard_data = leaderboard_data.filter(
                submission__is_public=True
            )

    all_banned_participant_team = []
    for leaderboard_item in leaderboard_data:
        participant_team_id = leaderboard_item["submission__participant_team"]
        participant_team = ParticipantTeam.objects.get(id=participant_team_id)
        all_participants_email_ids = (
            participant_team.get_all_participants_email()
        )
        for participant_email in all_participants_email_ids:
            if participant_email in all_banned_email_ids:
                all_banned_participant_team.append(participant_team_id)
                break
        if leaderboard_item["error"] is None:
            leaderboard_item.update(filtering_error=0)
        if leaderboard_item["filtering_score"] is None:
            leaderboard_item.update(filtering_score=0)
    if challenge_phase_split.show_leaderboard_by_latest_submission:
        sorted_leaderboard_data = leaderboard_data
    else:
        sorted_leaderboard_data = sorted(
            leaderboard_data,
            key=lambda k: (
                float(k["filtering_score"]),
                float(-k["filtering_error"]),
            ),
            reverse=True
            if challenge_phase_split.is_leaderboard_order_descending
            else False,
        )
    distinct_sorted_leaderboard_data = []
    team_list = []
    for data in sorted_leaderboard_data:
        if (
            data["submission__participant_team__team_name"] in team_list
            or data["submission__participant_team"]
            in all_banned_participant_team
        ):
            continue
        elif data["submission__is_baseline"] is True:
            distinct_sorted_leaderboard_data.append(data)
        else:
            distinct_sorted_leaderboard_data.append(data)
            team_list.append(data["submission__participant_team__team_name"])

    leaderboard_labels = challenge_phase_split.leaderboard.schema["labels"]
    for item in distinct_sorted_leaderboard_data:
        item_result = []
        for index in leaderboard_labels:
            # Handle case for partially evaluated submissions
            if index in item["result"].keys():
                item_result.append(item["result"][index])
            else:
                item_result.append("#")
        item["result"] = item_result

        if item["error"] is not None:
            item["error"] = [
                item["error"]["error_{0}".format(index)]
                for index in leaderboard_labels
            ]
    return distinct_sorted_leaderboard_data, status.HTTP_200_OK


def get_leaderboard_data_model(submission_pk, challenge_phase_split_pk):
    """
    Function to calculate and return the sorted leaderboard data

    Arguments:
        submission_pk {[int]} -- Submission object primary key
        challenge_phase_split_pk {[int]} -- ChallengePhase object primary key

    Returns:
        [Class Object] -- LeaderboardData model object
    """
    leaderboard_data = LeaderboardData.objects.get(
        submission=submission_pk,
        challenge_phase_split__pk=challenge_phase_split_pk,
    )
    return leaderboard_data


def reorder_submissions_comparator(submission_1, submission_2):
    """
    Comparator for reordering my submissions page

    Arguments:
         submission_1 {[Class Object]} -- Submission object
         submission_2 {[Class Object]} -- Submission object

    Returns:
        [int] -- comparison result
    """
    submissions_in_progress_status = [
        Submission.SUBMITTED,
        Submission.SUBMITTING,
        Submission.RUNNING,
    ]
    if (
        submission_1.status in submissions_in_progress_status
        and submission_2.status in submissions_in_progress_status
    ):
        return submission_1.submitted_at > submission_2.submitted_at
    return submission_1.submitted_at < submission_2.submitted_at


def reorder_submissions_comparator_to_key(comparator):
    """
    Convert a cmp= function into a key= function for lambda

    Arguments:
         comparator {[function]} -- comparator function

    Returns:
        [class] -- key class object for lamdbda
    """

    class ComparatorToLambdaKey:
        def __init__(self, obj, *args):
            self.obj = obj

        # Compares if first object is less than second object
        def __lt__(self, other):
            return comparator(self.obj, other.obj) == 0

        # Compares if first object is greater than second object
        def __gt__(self, other):
            return comparator(self.obj, other.obj) > 0

        # Compares if first object is equal than second object
        def __eq__(self, other):
            return comparator(self.obj, other.obj) == 0

        # Compares if first object is less than equal to second object
        def __le__(self, other):
            return comparator(self.obj, other.obj) == 0

        # Compares if first object is greater than equal to second object
        def __ge__(self, other):
            return comparator(self.obj, other.obj) >= 0

        # Compares if first object is not equal to second object
        def __ne__(self, other):
            return comparator(self.obj, other.obj) != 0

    return ComparatorToLambdaKey
