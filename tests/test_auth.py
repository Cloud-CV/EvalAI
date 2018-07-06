import json
import os
import responses
import shutil
from click.testing import CliRunner

from evalai.challenges import challenge, challenges
from evalai.utils.urls import URLS
from evalai.utils.config import API_HOST_URL, AUTH_TOKEN_DIR

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
