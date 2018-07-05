import json
import requests
import sys

from beautifultable import BeautifulTable
from click import echo, style

from evalai.utils.auth import get_request_header
from evalai.utils.common import validate_token
from evalai.utils.urls import URLS
from evalai.utils.config import API_HOST_URL, EVALAI_ERROR_CODES


def pretty_print_team_data(teams):
    """
    Function to print the team data
    """
    table = BeautifulTable(max_width=200)
    attributes = ["id", "team_name", "created_by"]
    columns_attributes = ["ID", "Team Name", "Created By", "Members"]
    table.column_headers = columns_attributes
    for team in teams:
        values = list(map(lambda item: team[item], attributes))
        members = ", ".join(map(lambda member: member["member_name"], team["members"]))
        values.append(members)
        table.append_row(values)
    echo(table)


def display_participant_teams():
    """
    Function to display all the participant teams of a user
    """
    headers = get_request_header()

    url = "{}{}".format(API_HOST_URL, URLS.participant_team_list.value)
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

    teams = response["results"]
    if len(teams) != 0:
        pretty_print_team_data(teams)
    else:
        echo("Sorry, no teams found!")


def create_participant_team(team_name):
    """
    Function to create a new team by taking in the team name as input.
    """
    url = "{}{}".format(API_HOST_URL, URLS.participant_team_list.value)

    headers = get_request_header()
    headers['Content-Type'] = 'application/json'

    data = {}
    data["team_name"] = team_name
    data = json.dumps(data)
    try:
        response = requests.post(
                                url,
                                headers=headers,
                                data=data
                                )
        response.raise_for_status()
    except requests.exceptions.HTTPError as err:
        if (response.status_code in EVALAI_ERROR_CODES):
            validate_token(response.json())
            if "team_name" in response.json().keys():
                validate_token(response.json())
                echo(style("Error: {}".format(response.json()["team_name"][0]), fg="red", bold=True))
            else:
                echo(style("Error: {}".format(response.json()["error"]), fg="red", bold=True))
        else:
            echo(err)
        sys.exit(1)
    except requests.exceptions.RequestException as err:
        echo(err)
        sys.exit(1)

    if response.status_code == 201:
        response = response.json()
        echo(style("\nThe team {} was successfully created.\n".format(response["team_name"]),
                   fg="green", bold=True))


def participate_in_a_challenge(challenge_id, participant_team_id):
    """
    Function to participate in a particular challenge.
    """

    url = "{}{}".format(API_HOST_URL, URLS.participate_in_a_challenge.value)
    url = url.format(challenge_id, participant_team_id)

    headers = get_request_header()
    headers['Content-Type'] = 'application/json'
    try:
        response = requests.post(
                                url,
                                headers=headers,
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

    if response.status_code == 201:
        echo(style("Your team id {} is now participating in this challenge!".format(participant_team_id),
                   fg="green", bold=True))
