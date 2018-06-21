import requests
import sys

from click import echo, style

from evalai.utils.auth import get_request_header
from evalai.utils.common import validate_token
from evalai.utils.urls import URLS
from evalai.utils.config import API_HOST_URL


def pretty_print_challenge_data(challenge):
    """
    Function to print the challenge data
    """
    br = style("----------------------------------------"
               "--------------------------", bold=True)

    challenge_title = "\n{}".format(style(challenge["title"],
                                    bold=True, fg="green"))
    challenge_id = "ID: {}\n\n".format(style(str(challenge["id"]),
                                       bold=True, fg="blue"))

    title = "{} {}".format(challenge_title, challenge_id)

    description = "{}\n".format(challenge["short_description"])
    end_date = "End Date : " + style(challenge["end_date"].split("T")[0], fg="red")
    end_date = "\n{}\n\n".format(style(end_date, bold=True))
    challenge = "{}{}{}{}".format(title, description, end_date, br)
    echo(challenge)


def display_challenges(url):
    """
    Function to fetch & display the challenge list based on API
    """

    header = get_request_header()
    try:
        response = requests.get(url, headers=header)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    response = response.json()
    if validate_token(response):

        challenges = response["results"]
        if len(challenges) is not 0:
            for challenge in challenges:
                pretty_print_challenge_data(challenge)
        else:
            echo("Sorry, no challenges found!")


def display_all_challenge_list():
    """
    Displays the list of all challenges from the backend
    """
    url = "{}{}".format(API_HOST_URL, URLS.challenge_list.value)
    display_challenges(url)


def display_past_challenge_list():
    """
    Displays the list of past challenges from the backend
    """
    url = "{}{}".format(API_HOST_URL, URLS.past_challenge_list.value)
    display_challenges(url)


def display_ongoing_challenge_list():
    """
    Displays the list of ongoing challenges from the backend
    """
    url = "{}{}".format(API_HOST_URL, URLS.challenge_list.value)
    display_challenges(url)


def display_future_challenge_list():
    """
    Displays the list of future challenges from the backend
    """
    url = "{}{}".format(API_HOST_URL, URLS.future_challenge_list.value)
    display_challenges(url)


def get_participant_or_host_teams(url):
    """
    Returns the participant or host teams corresponding to the user
    """
    header = get_request_header()

    try:
        response = requests.get(url, headers=header)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    response = response.json()

    if validate_token(response):
        return response['results']
    else:
        echo("The authentication token is not valid. Please try again!")
        sys.exit(1)


def get_participant_or_host_team_challenges(url, teams):
    """
    Returns the challenges corresponding to the participant or host teams
    """
    challenges = []
    for team in teams:
        header = get_request_header()
        try:
            response = requests.get(url.format(team['id']), headers=header)
            response.raise_for_status()
        except requests.exceptions.HTTPError as err:
            echo(err)
            sys.exit(1)
        except requests.exceptions.RequestException as err:
            echo(err)
            sys.exit(1)
        response = response.json()
        challenges += response['results']
    return challenges


def display_participated_or_hosted_challenges(is_host=False, is_participant=False):
    """
    Function to display the participated or hosted challenges by a user
    """

    challenges = []

    if is_host:
        team_url = "{}{}".format(API_HOST_URL,
                                 URLS.host_teams.value)
        challenge_url = "{}{}".format(API_HOST_URL,
                                      URLS.host_challenges.value)
        echo(style("\nHosted Challenges\n", bold=True))

        teams = get_participant_or_host_teams(team_url)

        challenges = get_participant_or_host_team_challenges(challenge_url, teams)

        if len(challenges) != 0:
            for challenge in challenges:
                pretty_print_challenge_data(challenge)
        else:
            echo("Sorry, no challenges found!")

    if is_participant:
        team_url = "{}{}".format(API_HOST_URL,
                                 URLS.participant_teams.value)
        challenge_url = "{}{}".format(API_HOST_URL,
                                      URLS.participant_challenges.value)
        echo(style("\nParticipated Challenges\n", bold=True))

        teams = get_participant_or_host_teams(team_url)

        challenges = get_participant_or_host_team_challenges(challenge_url, teams)

        if len(challenges) != 0:
            for challenge in challenges:
                pretty_print_challenge_data(challenge)
        else:
            echo("Sorry, no challenges found!")
