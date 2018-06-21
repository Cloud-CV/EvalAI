import json
import responses

from click.testing import CliRunner

from evalai.challenges import challenges
from evalai.utils.urls import URLS
from evalai.utils.config import API_HOST_URL
from tests.data import challenge_response

from .base import BaseTestClass


class TestChallenges(BaseTestClass):

    def setup(self):

        challenge_data = json.loads(challenge_response.challenges)

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value),
                      json=challenge_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.past_challenge_list.value),
                      json=challenge_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value),
                      json=challenge_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.future_challenge_list.value),
                      json=challenge_data, status=200)

        challenges = challenge_data["results"]

        self.output = ""

        title = "\n{}".format("{}")
        id_field = "{}\n\n".format("{}")
        subtitle = "\n{}\n\n".format("{}")
        br = "------------------------------------------------------------------\n"

        for challenge in challenges:
            challenge_title = title.format(challenge["title"])
            challenge_id = "ID: " + id_field.format(challenge["id"])

            heading = "{} {}".format(challenge_title, challenge_id)
            description = "{}\n".format(challenge["short_description"])
            challenge_end_date = "End Date : " + challenge["end_date"].split("T")[0]
            challenge_end_date = subtitle.format(challenge_end_date)
            challenge = "{}{}{}{}".format(heading, description, challenge_end_date, br)

            self.output = "{}{}".format(self.output, challenge)

    @responses.activate
    def test_challenge_lists(self):
        runner = CliRunner()
        result = runner.invoke(challenges)
        response_table = result.output
        assert response_table == self.output

    @responses.activate
    def test_past_challenge_lists(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['past'])
        response_table = result.output
        assert response_table == self.output

    @responses.activate
    def test_ongoing_challenge_lists(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['ongoing'])
        response_table = result.output
        assert response_table == self.output

    @responses.activate
    def test_future_challenge_lists(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['future'])
        response_table = result.output
        assert response_table == self.output


class TestParticipantOrHostTeamChallenges(BaseTestClass):

    def setup(self):

        challenge_data = json.loads(challenge_response.challenges)
        host_team_data = json.loads(challenge_response.challenge_host_teams)
        participant_team_data = json.loads(challenge_response.challenge_participant_teams)

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_teams.value),
                      json=participant_team_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_teams.value),
                      json=host_team_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_challenges.value).format("3"),
                      json=challenge_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_challenges.value).format("2"),
                      json=challenge_data, status=200)

        challenges = challenge_data["results"]

        self.output = ""

        title = "\n{}".format("{}")
        id_field = "{}\n\n".format("{}")
        subtitle = "\n{}\n\n".format("{}")
        br = "------------------------------------------------------------------\n"

        for challenge in challenges:
            challenge_title = title.format(challenge["title"])
            challenge_id = "ID: " + id_field.format(challenge["id"])

            heading = "{} {}".format(challenge_title, challenge_id)
            description = "{}\n".format(challenge["short_description"])
            challenge_end_date = "End Date : " + challenge["end_date"].split("T")[0]
            challenge_end_date = subtitle.format(challenge_end_date)
            challenge = "{}{}{}{}".format(heading, description, challenge_end_date, br)

            self.output = "{}{}".format(self.output, challenge)

    @responses.activate
    def test_host_challenge_list(self):
        runner = CliRunner()
        expected = "\nHosted Challenges\n\n"
        self.output = "{}{}".format(expected, self.output)
        result = runner.invoke(challenges, ['--host'])
        response = result.output
        assert response == self.output

    @responses.activate
    def test_participant_challenge_lists(self):
        runner = CliRunner()
        expected = "\nParticipated Challenges\n\n"
        self.output = "{}{}".format(expected, self.output)
        result = runner.invoke(challenges, ['--participant'])
        response = result.output
        assert response == self.output

    @responses.activate
    def test_participant_and_host_challenge_lists(self):
        runner = CliRunner()
        participant_string = "\nParticipated Challenges\n\n"
        host_string = "\nHosted Challenges\n\n"
        self.output = "{}{}{}{}".format(host_string, self.output, participant_string, self.output)
        result = runner.invoke(challenges, ['--participant', '--host'])
        response = result.output
        assert response == self.output
