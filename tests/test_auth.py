import json
import os
import responses
import shutil
from click.testing import CliRunner

from evalai.challenges import challenge, challenges
from evalai.set_host import host
from evalai.utils.urls import URLS
from evalai.utils.config import (API_HOST_URL,
                                 AUTH_TOKEN_DIR,
                                 HOST_URL_FILE_PATH)

from tests.data import challenge_response
from tests.base import BaseTestClass


class TestGetUserAuthToken(BaseTestClass):

    def setup(self):
        if os.path.exists(AUTH_TOKEN_DIR):
            shutil.rmtree(AUTH_TOKEN_DIR)

    def test_get_user_auth_token_when_file_does_not_exist(self):
        expected = ("\nThe authentication token json file doesn't exists at the required path. "
                    "Please download the file from the Profile section of the EvalAI webapp and "
                    "place it at ~/.evalai/token.json\n\n")
        runner = CliRunner()
        result = runner.invoke(challenges)
        response = result.output
        assert response == expected


class TestUserRequestWithInvalidToken(BaseTestClass):

    def setup(self):

        invalid_token_data = json.loads(challenge_response.invalid_token)

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value),
                      json=invalid_token_data, status=401)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_teams.value),
                      json=invalid_token_data, status=401)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.leaderboard.value).format("1"),
                      json=invalid_token_data, status=401)

        self.expected = "\nThe authentication token you are using isn't valid. Please generate it again.\n\n"

    @responses.activate
    def test_display_all_challenge_lists_when_token_is_invalid(self):
        runner = CliRunner()
        result = runner.invoke(challenges)
        response = result.output
        assert response == self.expected

    @responses.activate
    def test_display_leaderboard_when_token_is_invalid(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['2', 'leaderboard', '1'])
        response = result.output
        assert response == self.expected

    @responses.activate
    def test_display_participant_challenge_lists_when_token_is_invalid(self):
        expected = "The authentication token you are using isn't valid. Please generate it again."
        runner = CliRunner()
        result = runner.invoke(challenges, ['--host'])
        response = result.output.strip()
        assert response == expected


class TestUserRequestWithExpiredToken(BaseTestClass):

    def setup(self):

        token_expired_data = json.loads(challenge_response.token_expired)

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value),
                      json=token_expired_data, status=401)

    @responses.activate
    def test_display_all_challenge_lists_when_token_has_expired(self):
        expected = "\nSorry, the token has expired. Please generate it again.\n\n"
        runner = CliRunner()
        result = runner.invoke(challenges)
        response = result.output
        assert response == expected


class TestHostConfig(BaseTestClass):

    def teardown(self):
        if os.path.exists(HOST_URL_FILE_PATH):
            os.remove(HOST_URL_FILE_PATH)

    def test_get_default_host(self):
        expected = ("You haven't configured a Host URL for the CLI.\n"
                    "The CLI would be using http://localhost:8000 as the default url.\n")
        runner = CliRunner()
        result = runner.invoke(host)
        assert expected == result.output
        assert result.exit_code == 0

    def test_set_host_wrong_url(self):
        expected = ("Sorry, please enter a valid url.\n"
                    "Example: https://evalapi.cloudcv.org\n")
        runner = CliRunner()
        result = runner.invoke(host, ['-sh', 'http:/evalapi.cloudcv'])
        assert expected == result.output
        assert result.exit_code == 0

    def test_set_host_url(self):
        expected = "{} is set as the host url!\n".format("https://evalapi.cloudcv.org")
        runner = CliRunner()
        result = runner.invoke(host, ['-sh', 'https://evalapi.cloudcv.org'])
        assert expected == result.output
        assert result.exit_code == 0

    def test_set_host_url_and_display(self):
        expected = "https://evalapi.cloudcv.org is the Host URL of EvalAI.\n"
        runner = CliRunner()
        runner.invoke(host, ['-sh', 'https://evalapi.cloudcv.org'])
        result = runner.invoke(host)
        assert expected == result.output
        assert result.exit_code == 0


class TestSetAndLoadHostURL(BaseTestClass):

    def setup(self):

        challenge_data = json.loads(challenge_response.challenges)

        url = "{}{}"
        responses.add(responses.GET, url.format("https://evalapi.cloudcv.org", URLS.challenge_list.value),
                      json=challenge_data, status=200)

        challenges_json = challenge_data["results"]

        self.output = ""

        title = "\n{}".format("{}")
        id_field = "{}\n\n".format("{}")
        subtitle = "\n{}\n\n".format("{}")

        for challenge_data in challenges_json:
            challenge_title = title.format(challenge_data["title"])
            challenge_id = "ID: " + id_field.format(challenge_data["id"])

            heading = "{} {}".format(challenge_title, challenge_id)
            description = "{}\n".format(challenge_data["short_description"])
            end_date = "End Date : " + challenge_data["end_date"].split("T")[0]
            end_date = subtitle.format(end_date)
            br = "------------------------------------------------------------------\n"
            challenge_data = "{}{}{}{}".format(heading, description, end_date, br)

            self.output = "{}{}".format(self.output, challenge_data)

    def teardown(self):
        if os.path.exists(HOST_URL_FILE_PATH):
            os.remove(HOST_URL_FILE_PATH)

    @responses.activate
    def test_set_and_load_host_url(self):
        runner = CliRunner()
        result = runner.invoke(host, ['-sh', "https://evalapi.cloudcv.org"])
        result = runner.invoke(challenges)
        response_table = result.output
        assert response_table == self.output
