import json
import responses

from click.testing import CliRunner

from evalai.challenges import challenges
from evalai.utils.urls import URLS
from evalai.utils.config import API_HOST_URL

from .base import BaseTestClass
from tests.data import challenge_response


class TestHTTPErrorRequests(BaseTestClass):

    def setup(self):

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.past_challenge_list.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.future_challenge_list.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_teams.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_teams.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_challenges.value).format("3"),
                      status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_challenges.value).format("2"), status=404)

        self.expected = "404 Client Error: Not Found for url: {}"

    @responses.activate
    def test_display_all_challenge_list_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenges)
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.challenge_list.value)
        assert response == self.expected.format(url)

    @responses.activate
    def test_display_past_challenge_list_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['past'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.past_challenge_list.value)
        assert response == self.expected.format(url)

    @responses.activate
    def test_display_ongoing_challenge_list_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['ongoing'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.challenge_list.value)
        assert response == self.expected.format(url)

    @responses.activate
    def test_display_future_challenge_list_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['future'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.future_challenge_list.value)
        assert response == self.expected.format(url)

    @responses.activate
    def test_display_host_challenge_list_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['--host'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.host_teams.value)
        assert response == self.expected.format(url)

    @responses.activate
    def test_display_participant_challenge_lists_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['--participant'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.participant_teams.value)
        assert response == self.expected.format(url)

    @responses.activate
    def test_display_participant_and_host_challenge_lists_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['--participant', '--host'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.host_teams.value)
        assert response == self.expected.format(url)


class TestGetParticipantOrHostTeamChallengesHTTPErrorRequests(BaseTestClass):

    def setup(self):

        participant_team_data = json.loads(challenge_response.challenge_participant_teams)

        url = "{}{}"

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_teams.value),
                      json=participant_team_data, status=200)
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_challenges.value).format("3"),
                      status=404)

        self.expected = "404 Client Error: Not Found for url: {}"

    @responses.activate
    def test_get_participant_or_host_team_challenges_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['--participant'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.participant_challenges.value)
        assert response == self.expected.format(url.format("3"))


class TestGetParticipantOrHostTeamChallengesRequestForExceptions(BaseTestClass):

    def setup(self):

        participant_team_data = json.loads(challenge_response.challenge_participant_teams)

        url = "{}{}"

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_teams.value),
                      json=participant_team_data, status=200)
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_challenges.value).format("3"),
                      body=Exception('...'))

        self.expected = "404 Client Error: Not Found for url: {}"

    @responses.activate
    def test_get_participant_or_host_team_challenges_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['--participant'])
        assert result.exit_code == -1


class TestRequestForExceptions(BaseTestClass):

    def setup(self):

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value), body=Exception('...'))

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.past_challenge_list.value), body=Exception('...'))

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value), body=Exception('...'))

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.future_challenge_list.value), body=Exception('...'))

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_teams.value), body=Exception('...'))

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_teams.value), body=Exception('...'))

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_challenges.value).format("3"),
                      body=Exception('...'))

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_challenges.value).format("2"),
                      body=Exception('...'))

    @responses.activate
    def test_display_challenge_list_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenges)
        assert result.exit_code == -1

    @responses.activate
    def test_display_past_challenge_list_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['past'])
        assert result.exit_code == -1

    @responses.activate
    def test_display_ongoing_challenge_list_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['ongoing'])
        assert result.exit_code == -1

    @responses.activate
    def test_display_future_challenge_list_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['future'])
        assert result.exit_code == -1

    @responses.activate
    def test_display_host_challenge_list_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['--host'])
        assert result.exit_code == -1

    @responses.activate
    def test_display_participant_challenge_lists_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['--participant'])
        assert result.exit_code == -1

    @responses.activate
    def test_display_participant_and_host_challenge_lists_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['--participant', '--host'])
        assert result.exit_code == -1
