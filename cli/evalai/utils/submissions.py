import requests
import sys

from beautifultable import BeautifulTable
from click import echo, style
from datetime import datetime

from evalai.utils.auth import get_request_header, get_host_url
from evalai.utils.config import EVALAI_ERROR_CODES
from evalai.utils.urls import URLS
from evalai.utils.common import (
    convert_UTC_date_to_local,
    validate_token,
    validate_date_format,
)


requests.packages.urllib3.disable_warnings()


def make_submission(challenge_id, phase_id, file, submission_metadata={}):
    """
    Function to submit a file to a challenge
    """
    url = "{}{}".format(get_host_url(), URLS.make_submission.value)
    url = url.format(challenge_id, phase_id)

    headers = get_request_header()
    input_file = {"input_file": file}
    data = {"status": "submitting"}
    data = dict(data, **submission_metadata)

    try:
        response = requests.post(
            url, headers=headers, files=input_file, data=data
        )
        file.close()
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if response.status_code in EVALAI_ERROR_CODES:
            validate_token(response.json())
            echo(
                style(
                    "\nError: {}\n"
                    "\nUse `evalai challenges` to fetch the active challenges.\n"
                    "\nUse `evalai challenge CHALLENGE phases` to fetch the "
                    "active phases.\n".format(response.json()["error"]),
                    fg="red",
                    bold=True,
                )
            )
        else:
            echo(err)
        if "input_file" in response.json():
            echo(style(response.json()["input_file"][0], fg="red", bold=True))
        sys.exit(1)
    except requests.exceptions.RequestException:
        echo(
            style(
                "\nCould not establish a connection to EvalAI."
                " Please check the Host URL.\n",
                bold=True,
                fg="red",
            )
        )
        sys.exit(1)
    response = response.json()
    echo(
        style(
            "\nYour file {} with the ID {} is successfully submitted.\n".format(
                file.name, response["id"]
            ),
            fg="green",
            bold=True,
        )
    )
    echo(
        style(
            "You can use `evalai submission {}` to view this submission's status.\n".format(
                response["id"]
            ),
            bold=True,
            fg="white"
        )
    )


def pretty_print_my_submissions_data(submissions, start_date, end_date):
    """
    Function to print the submissions for a particular challenge.
    """
    table = BeautifulTable(max_width=100)
    attributes = ["id", "participant_team_name", "execution_time", "status"]
    columns_attributes = [
        "ID",
        "Participant Team",
        "Execution Time(sec)",
        "Status",
        "Submitted At",
        "Method Name",
    ]
    table.column_headers = columns_attributes
    if len(submissions) == 0:
        echo(
            style(
                "\nSorry, you have not made any submissions to this challenge phase.\n",
                bold=True,
                fg="red"
            )
        )
        sys.exit(1)

    if not start_date:
        start_date = datetime.min

    if not end_date:
        end_date = datetime.max

    for submission in submissions:
        date = validate_date_format(submission["submitted_at"])
        if date >= start_date and date <= end_date:
            # Check for empty method name
            date = convert_UTC_date_to_local(submission["submitted_at"])
            method_name = (
                submission["method_name"]
                if submission["method_name"]
                else "None"
            )
            values = list(map(lambda item: submission[item], attributes))
            values.append(date)
            values.append(method_name)
            table.append_row(values)
    if len(table) == 0:
        echo(
            style(
                "\nSorry, no submissions were made during this time period.\n",
                bold=True,
                fg="red"
            )
        )
        sys.exit(1)
    echo(table)


def display_my_submission_details(
    challenge_id, phase_id, start_date, end_date
):
    """
    Function to display the details of a particular submission.
    """
    url = URLS.my_submissions.value
    url = "{}{}".format(get_host_url(), url)
    url = url.format(challenge_id, phase_id)
    headers = get_request_header()

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if response.status_code in EVALAI_ERROR_CODES:
            validate_token(response.json())
            echo(
                style(
                    "\nError: {}\n"
                    "\nUse `evalai challenges` to fetch the active challenges.\n"
                    "\nUse `evalai challenge CHALLENGE phases` to fetch the "
                    "active phases.\n".format(response.json()["error"]),
                    fg="red",
                    bold=True,
                )
            )
        else:
            echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException:
        echo(
            style(
                "\nCould not establish a connection to EvalAI."
                " Please check the Host URL.\n",
                bold=True,
                fg="red",
            )
        )
        sys.exit(1)

    response = response.json()

    submissions = response["results"]
    pretty_print_my_submissions_data(submissions, start_date, end_date)


def pretty_print_submission_details(submission):
    """
    Function to print details of a submission
    """
    team_name = "\n{}".format(
        style(submission["participant_team_name"], bold=True, fg="green")
    )
    sid = "Submission ID: {}\n".format(
        style(str(submission["id"]), bold=True, fg="blue")
    )
    team_name = "{} {}".format(team_name, sid)

    status = style(
        "\nSubmission Status : {}\n".format(submission["status"]), bold=True
    )
    execution_time = style(
        "\nExecution Time (sec) : {}\n".format(submission["execution_time"]),
        bold=True,
    )

    date = convert_UTC_date_to_local(submission["submitted_at"])
    submitted_at = style("\nSubmitted At : {}\n".format(date), bold=True)
    submission = "{}{}{}{}".format(
        team_name, status, execution_time, submitted_at
    )
    echo(submission)


def submission_details_request(submission_id):
    """
    Function to request details of a particular submission
    """
    url = "{}{}".format(get_host_url(), URLS.get_submission.value)
    url = url.format(submission_id)
    headers = get_request_header()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if response.status_code in EVALAI_ERROR_CODES:
            validate_token(response.json())
            echo(
                style(
                    "\nError: {}\n"
                    "\nUse `evalai challenge CHALLENGE phase PHASE submissions` "
                    "to view your submission.\n".format(
                        response.json()["error"]
                    ),
                    fg="red",
                    bold=True,
                )
            )
        else:
            echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException:
        echo(
            style(
                "\nCould not establish a connection to EvalAI."
                " Please check the Host URL.\n",
                bold=True,
                fg="red",
            )
        )
        sys.exit(1)
    return response


def display_submission_details(submission_id):
    """
    Function to display details of a particular submission
    """
    response = submission_details_request(submission_id).json()
    pretty_print_submission_details(response)


def display_submission_result(submission_id):
    """
    Function to display result of a particular submission
    """
    try:
        response = submission_details_request(submission_id).json()
        echo(requests.get(response['submission_result_file']).text)
    except requests.exceptions.MissingSchema:
        echo(
            style(
                "\nThe Submission is yet to be evaluated.\n",
                bold=True,
                fg="red",
            )
        )


def convert_bytes_to(byte, to, bsize=1024):
    """
    Convert bytes to KB, MB, GB etc.
    Arguments:
        bytes {int} -- The bytes which are to be converted
        to {str} -- To which unit it is to be converted
    """
    units_mapping = {"kb": 1, "mb": 2, "gb": 3, "tb": 4, "pb": 5, "eb": 6}
    unit = byte
    for value in range(units_mapping[to]):
        unit = int(unit / bsize)

    return unit
