import requests
import sys

from beautifultable import BeautifulTable
from click import echo, style

from evalai.utils.auth import get_request_header
from evalai.utils.config import API_HOST_URL, EVALAI_ERROR_CODES
from evalai.utils.urls import URLS
from evalai.utils.common import validate_token, convert_UTC_date_to_local


def make_submission(challenge_id, phase_id, file, submission_metadata={}):
    """
    Function to submit a file to a challenge
    """
    url = "{}{}".format(API_HOST_URL, URLS.make_submission.value)
    url = url.format(challenge_id, phase_id)

    headers = get_request_header()
    input_file = {'input_file': file}
    data = {
            'status': 'submitting',
            **submission_metadata,
           }
    try:
        response = requests.post(
                                url,
                                headers=headers,
                                files=input_file,
                                data=data,
                                )
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
    echo(style("\nYour file {} with the ID {} is successfully submitted.\n".format(file.name, response["id"]),
               fg="green", bold=True))
    echo(style("You can use `evalai submission {}` to view this submission's status.\n".format(response["id"]),
               bold=True))


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
        date = convert_UTC_date_to_local(submission['submitted_at'])
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


def pretty_print_submission_details(submission):
    """
    Function to print details of a submission
    """
    team_name = "\n{}".format(style(submission['participant_team_name'], bold=True, fg="green"))
    sid = "Submission ID: {}\n".format(style(str(submission['id']), bold=True, fg="blue"))
    team_name = "{} {}".format(team_name, sid)

    status = style("\nSubmission Status : {}\n".format(submission['status']), bold=True)
    execution_time = style("\nExecution Time (sec) : {}\n".format(submission['execution_time']), bold=True)

    date = convert_UTC_date_to_local(submission['submitted_at'])
    submitted_at = style("\nSubmitted At : {}\n".format(date), bold=True)
    submission = "{}{}{}{}".format(team_name, status, execution_time, submitted_at)
    echo(submission)


def display_submission_details(submission_id):
    """
    Function to display details of a particular submission
    """
    url = "{}{}".format(API_HOST_URL, URLS.get_submission.value)
    url = url.format(submission_id)

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

    pretty_print_submission_details(response)
