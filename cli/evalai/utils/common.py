import click
import random
import requests
import string
import sys

from bs4 import BeautifulSoup
from click import echo, style
from datetime import datetime
from dateutil import tz
from http import HTTPStatus

from evalai.utils.auth import get_request_header, get_host_url
from evalai.utils.config import EVALAI_ERROR_CODES
from evalai.utils.urls import URLS


class Date(click.ParamType):
    """
    Date object parsed using datetime.
    """

    name = "date"

    def __init__(self, format):
        self.format = format

    def convert(self, value, param, ctx):
        try:
            date = datetime.strptime(value, self.format)
            return date
        except ValueError:
            raise self.fail(
                "Incorrect date format, please use {} format. Example: 8/23/17.".format(
                    self.format
                )
            )


def upload_file_to_s3(file, presigned_url):
    """
    Function to upload a file, given the target presigned s3 url

    Arguments:
        file_name (str) -- the path of the file to be uploaded
        presigned_url (str) -- the presigned url to upload the file on s3
    """
    echo(
        style(
            "Uploading the file...",
            fg="green",
            bold=False,
        )
    )

    try:
        response = requests.put(
            presigned_url,
            data=file
        )
    except Exception as err:
        echo(style("\nThere was an error while uploading the file: {}".format(err), fg="red", bold=True))
        sys.exit(1)
    return response


def validate_token(response):
    """
    Function to check if the authentication token provided by user is valid or not.
    """
    if "detail" in response:
        if response["detail"] == "Invalid token":
            echo(
                style(
                    "\nThe authentication token you are using isn't valid."
                    " Please generate it again.\n",
                    bold=True,
                    fg="red",
                )
            )
            sys.exit(1)
        if response["detail"] == "Token has expired":
            echo(
                style(
                    "\nSorry, the token has expired. Please generate it again.\n",
                    bold=True,
                    fg="red",
                )
            )
            sys.exit(1)


def validate_date_format(date):
    for date_format in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(date, date_format)
        except ValueError:
            pass
    raise ValueError("Invalid date format. Please check again.")


def convert_UTC_date_to_local(date):
    # Format date
    date = validate_date_format(date)
    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()

    # Convert to local timezone from UTC.
    date = date.replace(tzinfo=from_zone)
    converted_date = date.astimezone(to_zone)
    date = converted_date.strftime("%D %r")
    return date


def clean_data(data):
    """
    Strip HTML and clean spaces
    """
    data = BeautifulSoup(data, "lxml").text.strip()
    data = " ".join(data.split()).encode("utf-8")
    return data


def notify_user(message, color="green", bold=False):
    echo(style(message, fg=color, bold=bold))


def generate_random_string(length):
    letter_set = string.ascii_lowercase + string.digits
    return "".join(random.choice(letter_set) for _ in range(length))


def upload_file_using_presigned_url(challenge_phase_pk, file, file_type, submission_metadata={}):
    if file_type == "submission":
        url = "{}{}".format(get_host_url(), URLS.get_presigned_url_for_submission_file.value)
    elif file_type == "annotation":
        url = "{}{}".format(get_host_url(), URLS.get_presigned_url_for_annotation_file.value)
    url = url.format(challenge_phase_pk)
    headers = get_request_header()

    try:
        # Fetching the presigned url
        if file_type == "submission":
            data = {"status": "submitting", "file_name": file.name}
            data = dict(data, **submission_metadata)
            response = requests.post(
                url, headers=headers, data=data
            )
            if response.status_code is not HTTPStatus.CREATED:
                response.raise_for_status()
        elif file_type == "annotation":
            data = {"file_name": file.name}
            response = requests.get(url, headers=headers, data=data)
            if response.status_code is not HTTPStatus.OK:
                response.raise_for_status()

        response = response.json()
        presigned_url = response.get("presigned_url")
        if file_type == "submission":
            submission_pk = response.get("submission_pk")

        # Uploading the file to S3
        response = upload_file_to_s3(file, presigned_url)
        if response.status_code is not HTTPStatus.OK:
            response.raise_for_status()

        if file_type == "submission":
            # Publishing submission message to the message queue for processing
            url = "{}{}".format(get_host_url(), URLS.send_submission_message.value)
            url = url.format(challenge_phase_pk, submission_pk)
            response = requests.post(
                url,
                headers=headers,
            )
            response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if response.status_code in EVALAI_ERROR_CODES:
            validate_token(response.json())
            if file_type == "submission":
                error_message = "\nThere was an error while making the submission: {}\n".format(response.json()["error"])
            elif file_type == "annotation":
                error_message = "\nThere was an error while uploading the annotation file: {}".format(response.json()["error"])
            echo(
                style(
                    error_message,
                    fg="red",
                    bold=True,
                )
            )
        else:
            echo(style("{}".format(err), fg='red'))
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

    if file_type == "submission":
        success_message = "\nYour submission {} with the id {} is successfully submitted for evaluation.\n".format(
            file.name, submission_pk
        )
    elif file_type == "annotation":
        success_message = "\nThe annotation file {} for challenge phase {} is successfully uploaded.\n".format(
            file.name, challenge_phase_pk
        )
    echo(
        style(
            success_message,
            fg="green",
            bold=True,
        )
    )
