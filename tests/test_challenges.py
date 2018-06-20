import json
import responses

from click.testing import CliRunner

from evalai.challenges import challenges
from evalai.utils.urls import URLS
from evalai.utils.config import API_HOST_URL
from tests.data import challenge_response


class TestChallenges:

    def setup(self):

        json_data = json.loads(challenge_response.challenges)

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value),
                      json=json_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.past_challenge_list.value),
                      json=json_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value),
                      json=json_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.future_challenge_list.value),
                      json=json_data, status=200)

        challenges = json_data["results"]

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
            end_date = "End Date : " + challenge["end_date"].split("T")[0]
            end_date = subtitle.format(end_date)
            challenge = "{}{}{}{}".format(heading, description, end_date, br)

            self.output = "{}{}".format(self.output, challenge)

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
            end_date = "End Date : " + challenge["end_date"].split("T")[0]
            end_date = subtitle.format(end_date)
            challenge = "{}{}{}{}".format(heading, description, end_date, br)

            self.output = "{}{}".format(self.output, challenge)

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
