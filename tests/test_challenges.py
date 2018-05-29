import ast
import click
import responses
import subprocess

from click.testing import CliRunner
from pylsy import pylsytable

from evalai.challenges import challenges
from tests.data import challenge_response

from evalai.utils.challenges import API_HOST_URL
from evalai.utils.urls import Urls


class TestChallenges:

    def setup(self):

        json_data = ast.literal_eval(challenge_response.challenges)

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, Urls.challenge_list.value),
                      json=json_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, Urls.past_challenge_list.value),
                      json=json_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, Urls.challenge_list.value),
                      json=json_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, Urls.future_challenge_list.value),
                      json=json_data, status=200)

        challenges = json_data["results"]

        self.output = ""

        title = "\n{}".format("{}")
        idfield = "{}\n\n".format("{}")
        subtitle = "\n{}\n\n".format("{}")
        br = "------------------------------------------------------------------\n"

        for challenge in challenges:
            challenge_title = title.format(challenge["title"])
            challenge_id = "ID: " + idfield.format(challenge["id"])

            heading = "{} {}".format(challenge_title, challenge_id)
            description = "{}\n".format(challenge["short_description"])
            date = "End Date : " + challenge["end_date"].split("T")[0]
            date = subtitle.format(date)
            challenge = "{}{}{}{}".format(heading, description, date, br)

            self.output = self.output + challenge


    @responses.activate
    def test_challenge_lists(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['list'])
        response_table = result.output
        assert response_table == self.output


    @responses.activate
    def test_challenge_lists_past(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['list', 'past'])
        response_table = result.output
        assert response_table == self.output

    @responses.activate
    def test_challenge_lists_ongoing(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['list', 'ongoing'])
        response_table = result.output
        assert response_table == self.output

    @responses.activate
    def test_challenge_lists_future(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['list', 'future'])
        response_table = result.output
        assert response_table == self.output


class TestTeamChallenges:

    def setup(self):

        challenge_data = ast.literal_eval(challenge_response.challenges)
        host_team_data = ast.literal_eval(challenge_response.challenge_host_teams)
        participant_team_data = ast.literal_eval(challenge_response.challenge_participant_teams)

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, Urls.participant_teams.value),
                      json=participant_team_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, Urls.host_teams.value),
                      json=host_team_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, Urls.participant_challenges.value).format("3"),
                      json=challenge_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, Urls.host_challenges.value).format("2"),
                      json=challenge_data, status=200)

        challenges = challenge_data["results"]

        self.output = ""

        title = "\n{}".format("{}")
        idfield = "{}\n\n".format("{}")
        subtitle = "\n{}\n\n".format("{}")
        br = "------------------------------------------------------------------\n"

        for challenge in challenges:
            challenge_title = title.format(challenge["title"])
            challenge_id = "ID: " + idfield.format(challenge["id"])

            heading = "{} {}".format(challenge_title, challenge_id)
            description = "{}\n".format(challenge["short_description"])
            date = "End Date : " + challenge["end_date"].split("T")[0]
            date = subtitle.format(date)
            challenge = "{}{}{}{}".format(heading, description, date, br)

            self.output = self.output + challenge

    @responses.activate
    def test_challenge_lists_host(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['list', '--host'])
        response_table = result.output
        assert response_table == self.output

    @responses.activate
    def test_challenge_lists_participant(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['list', '--participant'])
        response_table = result.output
        assert response_table == self.output
