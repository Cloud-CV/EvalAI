import requests
import sys

from bs4 import BeautifulSoup
from beautifultable import BeautifulTable
from click import echo, style
from datetime import datetime

from evalai.utils.auth import get_request_header, get_host_url
from evalai.utils.common import (clean_data,
                                 validate_token,
                                 convert_UTC_date_to_local,
                                 validate_date_format
                                 )
from evalai.utils.config import EVALAI_ERROR_CODES
from evalai.utils.urls import URLS


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

    cleaned_desc = BeautifulSoup(challenge["short_description"], "lxml").text
    description = "{}\n".format(cleaned_desc)
    end_date = "End Date : {}".format(style(challenge["end_date"].split("T")[0], fg="red"))
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
        if (response.status_code == 401):
            validate_token(response.json())
        echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    response = response.json()

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
    url = "{}{}".format(get_host_url(), URLS.challenge_list.value)
    display_challenges(url)


def display_past_challenge_list():
    """
    Displays the list of past challenges from the backend
    """
    url = "{}{}".format(get_host_url(), URLS.past_challenge_list.value)
    display_challenges(url)


def display_ongoing_challenge_list():
    """
    Displays the list of ongoing challenges from the backend
    """
    url = "{}{}".format(get_host_url(), URLS.challenge_list.value)
    display_challenges(url)


def display_future_challenge_list():
    """
    Displays the list of future challenges from the backend
    """
    url = "{}{}".format(get_host_url(), URLS.future_challenge_list.value)
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
        if (response.status_code == 401):
            validate_token(response.json())
        echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    response = response.json()

    return response['results']


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
            if (response.status_code == 401):
                validate_token(response.json())
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
        team_url = "{}{}".format(get_host_url(),
                                 URLS.host_teams.value)
        challenge_url = "{}{}".format(get_host_url(),
                                      URLS.host_challenges.value)

        teams = get_participant_or_host_teams(team_url)
        challenges = get_participant_or_host_team_challenges(challenge_url, teams)
        echo(style("\nHosted Challenges\n", bold=True))

        if len(challenges) != 0:
            for challenge in challenges:
                pretty_print_challenge_data(challenge)
        else:
            echo("Sorry, no challenges found!")

    if is_participant:
        team_url = "{}{}".format(get_host_url(),
                                 URLS.participant_teams.value)
        challenge_url = "{}{}".format(get_host_url(),
                                      URLS.participant_challenges.value)

        teams = get_participant_or_host_teams(team_url)
        challenges = get_participant_or_host_team_challenges(challenge_url, teams)

        if len(challenges) != 0:

            # Filter out past/unapproved/unpublished challenges.
            challenges = list(filter(lambda challenge:
                                     validate_date_format(challenge['end_date']) > datetime.now() and
                                     challenge["approved_by_admin"] and
                                     challenge["published"],
                                     challenges))
            if challenges:
                echo(style("\nParticipated Challenges\n", bold=True))
                for challenge in challenges:
                    pretty_print_challenge_data(challenge)
            else:
                echo("Sorry, no challenges found!")
        else:
            echo("Sorry, no challenges found!")


def pretty_print_all_challenge_phases(phases):
    """
    Function to print all the challenge phases of a challenge
    """
    table = BeautifulTable(max_width=150)
    attributes = ["id", "name", "challenge"]
    columns_attributes = ["Phase ID", "Phase Name", "Challenge ID", "Description"]
    table.column_headers = columns_attributes
    for phase in phases:
        values = list(map(lambda item: phase[item], attributes))
        description = clean_data(phase["description"])
        values.append(description)
        table.append_row(values)
    echo(table)


def display_challenge_phase_list(challenge_id):
    """
    Function to display all challenge phases for a particular challenge.
    """
    url = URLS.challenge_phase_list.value
    url = "{}{}".format(get_host_url(), url)
    url = url.format(challenge_id)
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
    challenge_phases = response["results"]
    pretty_print_all_challenge_phases(challenge_phases)


def pretty_print_challenge_phase_data(phase):
    """
    Function to print the details of a challenge phase.
    """
    phase_title = "\n{}".format(style(phase["name"], bold=True, fg="green"))
    challenge_id = "Challenge ID: {}".format(style(str(phase["challenge"]), bold=True, fg="blue"))
    phase_id = "Phase ID: {}\n\n".format(style(str(phase["id"]), bold=True, fg="blue"))

    title = "{} {} {}".format(phase_title, challenge_id, phase_id)

    cleaned_desc = BeautifulSoup(phase["description"], "lxml").text
    description = "{}\n".format(cleaned_desc)

    start_date = "Start Date : {}".format(style(phase["start_date"].split("T")[0], fg="green"))
    start_date = "\n{}\n".format(style(start_date, bold=True))

    end_date = "End Date : {}".format(style(phase["end_date"].split("T")[0], fg="red"))
    end_date = "\n{}\n".format(style(end_date, bold=True))
    max_submissions_per_day = style("\nMaximum Submissions per day : {}\n".format(
                                    str(phase["max_submissions_per_day"])), bold=True)

    max_submissions = style("\nMaximum Submissions : {}\n".format(str(phase["max_submissions"])),
                            bold=True)

    codename = style("\nCode Name : {}\n".format(phase["codename"]), bold=True)
    leaderboard_public = style("\nLeaderboard Public : {}\n".format(phase["leaderboard_public"]), bold=True)
    is_active = style("\nActive : {}\n".format(phase["is_active"]), bold=True)
    is_public = style("\nPublic : {}\n".format(phase["is_public"]), bold=True)

    challenge_phase = "{}{}{}{}{}{}{}{}{}{}".format(title, description, start_date,
                                                    end_date,
                                                    max_submissions_per_day,
                                                    max_submissions,
                                                    leaderboard_public,
                                                    codename, is_active, is_public)
    echo(challenge_phase)


def display_challenge_phase_detail(challenge_id, phase_id):
    """
    Function to print details of a challenge phase.
    """
    url = URLS.challenge_phase_detail.value
    url = "{}{}".format(get_host_url(), url)
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

    phase = response
    pretty_print_challenge_phase_data(phase)


def pretty_print_challenge_phase_split_data(phase_splits):
    """
    Function to print the details of a Challenge Phase Split.
    """
    table = BeautifulTable(max_width=100)
    attributes = ["id", "dataset_split_name", "challenge_phase_name"]
    columns_attributes = ["Challenge Phase ID", "Dataset Split", "Challenge Phase Name"]
    table.column_headers = columns_attributes

    for split in phase_splits:
        if split['visibility'] == 3:
            values = list(map(lambda item: split[item], attributes))
            table.append_row(values)
    echo(table)


def display_challenge_phase_split_list(challenge_id):
    """
    Function to display Challenge Phase Splits of a particular challenge.
    """
    url = URLS.challenge_phase_split_detail.value
    url = "{}{}".format(get_host_url(), url)
    url = url.format(challenge_id)
    headers = get_request_header()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if (response.status_code in EVALAI_ERROR_CODES):
            validate_token(response.json())
            echo(style("Error: {}".format(response.json()["error"], fg="red", bold=True)))
        else:
            echo(err)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    phase_splits = response.json()
    if len(phase_splits) != 0:
        pretty_print_challenge_phase_split_data(phase_splits)
    else:
        echo("Sorry, no Challenge Phase Splits found.")


def pretty_print_leaderboard_data(attributes, results):
    """
    Pretty print the leaderboard for a particular CPS.
    """
    leaderboard_table = BeautifulTable(max_width=150)
    attributes = ["Rank", "Participant Team"] + attributes + ["Last Submitted"]
    leaderboard_table.column_headers = attributes

    for rank, result in enumerate(results, start=1):
        name = result['submission__participant_team__team_name']
        scores = result['result']

        last_submitted = convert_UTC_date_to_local(result['submission__submitted_at'])

        leaderboard_row = [rank, name] + scores + [last_submitted]
        leaderboard_table.append_row(leaderboard_row)
    echo(leaderboard_table)


def display_leaderboard(challenge_id, phase_split_id):
    """
    Function to display the Leaderboard of a particular CPS.
    """
    url = "{}{}".format(get_host_url(), URLS.leaderboard.value)
    url = url.format(phase_split_id)
    headers = get_request_header()
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if (response.status_code in EVALAI_ERROR_CODES):
            validate_token(response.json())
            echo(style("Error: {}".format(response.json()["error"], fg="red", bold=True)))
        else:
            echo(err)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    response = response.json()

    results = response["results"]
    if len(results) != 0:
        attributes = results[0]["leaderboard__schema"]["labels"]
        pretty_print_leaderboard_data(attributes, results)
    else:
        echo("Sorry, no Leaderboard results found.")
