import sys
import click

from bs4 import BeautifulSoup
from click import echo, style
from datetime import datetime
from dateutil import tz


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
                    bg="red",
                )
            )
            sys.exit(1)
        if response["detail"] == "Token has expired":
            echo(
                style(
                    "\nSorry, the token has expired. Please generate it again.\n",
                    bold=True,
                    bg="red",
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
