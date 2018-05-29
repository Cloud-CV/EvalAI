import os
import requests
import sys

from click import echo, style

from pylsy import pylsytable

from evalai.utils.auth import get_headers
from evalai.utils.urls import Urls
from evalai.utils.common import valid_token


API_HOST_URL = os.environ.get("EVALAI_API_URL", 'http://localhost:8000')


def print_challenge_table(challenge):
    br = style("----------------------------------------"
               "--------------------------", bold=True)

    challenge_title = "\n{}".format(style(challenge["title"],
                                    bold=True, fg="green"))
    challenge_id = "ID: {}\n\n".format(style(str(challenge["id"]),
                                       bold=True, fg="blue"))

    title = "{} {}".format(challenge_title, challenge_id)

    description = "{}\n".format(challenge["short_description"])
    date = "End Date : " + style(challenge["end_date"].split("T")[0], fg="red")
    date = "\n{}\n\n".format(style(date, bold=True))
    challenge = "{}{}{}{}".format(title, description, date, br)
    echo(challenge)


def get_challenges(url):

    headers = get_headers()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    response_json = response.json()
    if valid_token(response_json):

        challenges = response_json["results"]
        if len(challenges) is not 0:
            for challenge in challenges:
                print_challenge_table(challenge)
        else:
            echo("Sorry, no challenges found.")


def get_challenge_list():
    """
    Fetches the list of challenges from the backend.
    """
    url = "{}{}".format(API_HOST_URL, Urls.challenge_list.value)
    get_challenges(url)


def get_past_challenge_list():
    """
    Fetches the list of past challenges from the backend.
    """
    url = "{}{}".format(API_HOST_URL, Urls.past_challenge_list.value)
    get_challenges(url)


def get_ongoing_challenge_list():
    """
    Fetches the list of ongoing challenges from the backend.
    """
    url = "{}{}".format(API_HOST_URL, Urls.challenge_list.value)
    get_challenges(url)


def get_future_challenge_list():
    """
    Fetches the list of future challenges from the backend.
    """
    url = "{}{}".format(API_HOST_URL, Urls.future_challenge_list.value)
    get_challenges(url)


def get_teams(url):
    """
    Returns the teams corresponding to the user.
    """
    headers = get_headers()

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    response_json = response.json()

    if valid_token(response_json):
        return response_json['results']
    else:
        echo("The token is not valid. Try again.")
        sys.exit(1)


def get_teams_challenges(url, teams):
    """
    Returns the challenges corresponding to the teams.
    """
    challenges = []
    for team in teams:
        headers = get_headers()
        try:
            response = requests.get(url.format(team['id']), headers=headers)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            echo(err)
            sys.exit(1)
        except requests.exceptions.RequestException as err:
            echo(err)
            sys.exit(1)
        response_json = response.json()
        challenges = challenges + response_json['results']
    return challenges


def get_challenge_count(is_host=False, is_participant=False):
    """
    Gets the challenge the user has participated or hosted.
    """
    challenges = []

    if is_host:
        team_url = "{}{}".format(API_HOST_URL,
                                 Urls.host_teams.value)
        challenge_url = "{}{}".format(API_HOST_URL,
                                      Urls.host_challenges.value)
    elif is_participant:
        team_url = "{}{}".format(API_HOST_URL,
                                 Urls.participant_teams.value)
        challenge_url = "{}{}".format(API_HOST_URL,
                                      Urls.participant_challenges.value)
    else:
        echo("Option doesn't exist. Use --help for information")
        sys.exit(1)

    teams = get_teams(team_url)

    challenges = get_teams_challenges(challenge_url, teams)

    for challenge in challenges:
        print_challenge_table(challenge)
