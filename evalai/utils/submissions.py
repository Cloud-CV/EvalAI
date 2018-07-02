import requests
import sys

from beautifultable import BeautifulTable
from click import echo, style
from datetime import datetime
from dateutil import tz

from evalai.utils.auth import get_request_header
from evalai.utils.common import validate_token
from evalai.utils.urls import URLS
from evalai.utils.config import API_HOST_URL, EVALAI_ERROR_CODES


def pretty_print_my_submissions_data(submissions):
    """
    Funcion to print the submissions for a particular Challenge.
    """
    table = BeautifulTable(max_width=100)
    attributes = ["id", "participant_team_name", "execution_time", "status"]
    columns_attributes = ["ID", "Participant Team", "Execution Time(sec)", "Status", "Submitted At", "Method Name"]
    table.column_headers = columns_attributes
    if len(submissions) == 0:
        echo(style("\nSorry, you have not made any submissions to this challenge phase.\n", bold=True))
        sys.exit(1)

    for submission in submissions:
        # Format date
        date = datetime.strptime(submission['submitted_at'], "%Y-%m-%dT%H:%M:%S.%fZ")
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()

        # Convert to local timezone from UTC.
        date = date.replace(tzinfo=from_zone)
        converted_date = date.astimezone(to_zone)
        date = converted_date.strftime('%D %r')

        # Check for empty method name
        method_name = submission["method_name"] if submission["method_name"] else "None"
        values = list(map(lambda item: submission[item], attributes))
        values.append(date)
        values.append(method_name)
        table.append_row(values)
    echo(table)


def display_my_submission_details(challenge_id, phase_id):
    """
    Function to display the details of a particular submission.
    """
    url = URLS.my_submissions.value
    url = "{}{}".format(API_HOST_URL, url)
    url = url.format(challenge_id, phase_id)
    headers = get_request_header()

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if (response.status_code in EVALAI_ERROR_CODES):
            validate_token(response.json())
            echo(style("Error: {}".format(response.json()["error"]), fg="red", bold=True))
        else:
            echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    response = response.json()

    submissions = response["results"]
    pretty_print_my_submissions_data(submissions)
