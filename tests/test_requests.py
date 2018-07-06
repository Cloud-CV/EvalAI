import json
import responses

from click.testing import CliRunner
from requests.exceptions import RequestException

from evalai.challenges import challenge, challenges
from evalai.teams import teams
from evalai.submissions import submission
from evalai.utils.urls import URLS
from evalai.utils.config import API_HOST_URL

from .base import BaseTestClass
from tests.data import challenge_response, teams_response


class TestHTTPErrorRequests(BaseTestClass):

    def setup(self):

        url = "{}{}"

        # Challenge URLS

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.past_challenge_list.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.future_challenge_list.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_teams.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_teams.value), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_challenges.value).format("3"),
                      status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_challenges.value).format("2"), status=404)

        # Teams URLS

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_team_list.value), status=404)

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.participant_team_list.value), status=404)

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.participate_in_a_challenge.value).format("2", "3"),
                      status=404)

        # Phase URLS

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_list.value).format('10'),
                      status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_detail.value).format('10', '20'),
                      status=404)

        # Submission URLS
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.my_submissions.value).format("3", "7"), status=404)
        # Leaderboard URLS
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.leaderboard.value).format("1"), status=404)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.get_submission.value).format("9"), status=404)

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.make_submission.value).format("1", "2"), status=404)

        # PhaseSplit URLS
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_split_detail.value).format("1"),
                      status=404)

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

    @responses.activate
    def test_display_participant_team_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(teams)
        response = result.output
        url = "{}{}".format(API_HOST_URL, URLS.participant_team_list.value)
        expected = "{}{}".format(self.expected.format(url), "\n")
        assert response == expected

    @responses.activate
    def test_create_participant_team_for_http_error_404(self):
        user_prompt_text = ("Enter team name: : TeamTest\n"
                            "Please confirm the team name - TeamTest [y/N]: y\n")
        runner = CliRunner()
        result = runner.invoke(teams, ['create'], input="TeamTest\ny\n")
        response = result.output
        url = "{}{}".format(API_HOST_URL, URLS.participant_team_list.value)
        expected = "{}{}".format(self.expected.format(url), "\n")
        expected = "{}{}".format(user_prompt_text, expected)
        assert response == expected

    @responses.activate
    def test_participate_in_a_challenge_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['2', 'participate', '3'])
        response = result.output
        url = "{}{}".format(API_HOST_URL, URLS.participate_in_a_challenge.value).format("2", "3")
        expected = "{}{}".format(self.expected.format(url), "\n")
        assert response == expected

    @responses.activate
    def test_display_my_submission_details_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['3', 'phase', '7', 'submissions'])
        response = result.output
        url = "{}{}".format(API_HOST_URL, URLS.my_submissions.value).format("3", "7")
        expected = "{}{}".format(self.expected.format(url), "\n")
        assert response == expected

    @responses.activate
    def test_display_submission_details_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(submission, ['9'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.get_submission.value).format("9")
        assert response == self.expected.format(url)

    @responses.activate
    def test_make_submission_for_http_error_404(self):
        runner = CliRunner()
        url = "{}{}".format(API_HOST_URL, URLS.make_submission.value).format("1", "2")
        with runner.isolated_filesystem():
            with open('test_file.txt', 'w') as f:
                f.write('1 2 3 4 5 6')

            result = runner.invoke(challenge, ['1', 'phase', '2', 'submit', "test_file.txt"])
            response = result.output.rstrip()
            assert response == self.expected.format(url)

    @responses.activate
    def test_display_challenge_phase_split_list_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['1', 'phase', '2', 'splits'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.challenge_phase_split_detail.value)
        expected = self.expected.format(url).format("1")
        assert response == expected

    @responses.activate
    def test_display_leaderboard_for_http_error_404(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['2', 'leaderboard', '1'])
        response = result.output.rstrip()
        url = "{}{}".format(API_HOST_URL, URLS.leaderboard.value).format("1")
        expected = self.expected.format(url)
        assert response == expected


class TestSubmissionDetailsWhenObjectDoesNotExist(BaseTestClass):

    def setup(self):

        error_data = json.loads(teams_response.object_error)
        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.get_submission.value).format("9"),
                      json=error_data, status=406)

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.make_submission.value).format("1", "2"),
                      json=error_data, status=406)

        self.expected = "Error: Sorry, the object does not exist."

    @responses.activate
    def test_display_submission_details_for_object_does_not_exist(self):
        runner = CliRunner()
        result = runner.invoke(submission, ['9'])
        response = result.output.rstrip()
        assert response == self.expected

    @responses.activate
    def test_make_submission_for_object_does_not_exist(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('test_file.txt', 'w') as f:
                f.write('1 2 3 4 5 6')

            result = runner.invoke(challenge, ['1', 'phase', '2', 'submit', "test_file.txt"])
            response = result.output.rstrip()
            assert response == self.expected


class TestTeamsWhenObjectDoesNotExist(BaseTestClass):

    def setup(self):

        error_data = json.loads(teams_response.object_error)
        url = "{}{}"

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_teams.value),
                      json=error_data, status=406)

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.participant_team_list.value), json=error_data,
                      status=406)

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.participate_in_a_challenge.value).format("2", "3"),
                      json=error_data, status=406)
        self.expected = "Error: Sorry, the object does not exist."

    @responses.activate
    def test_display_participant_team_for_object_does_not_exist(self):
        runner = CliRunner()
        result = runner.invoke(teams)
        response = result.output.rstrip()
        assert response == self.expected

    @responses.activate
    def test_create_participant_team_for_object_does_not_exist(self):
        user_prompt_text = ("Enter team name: : TeamTest\n"
                            "Please confirm the team name - TeamTest [y/N]: y\n")
        runner = CliRunner()
        result = runner.invoke(teams, ['create'], input="TeamTest\ny\n")
        response = result.output.rstrip()
        expected = "{}{}".format(user_prompt_text, self.expected)
        assert response == expected

    @responses.activate
    def test_participate_in_a_challenge_when_object_does_not_exist(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['2', 'participate', '3'])
        response = result.output.rstrip()
        assert response == self.expected


class TestTeamsWhenTeamNameAlreadyExists(BaseTestClass):

    def setup(self):

        error_data = json.loads(teams_response.participant_team_already_exists_error)
        url = "{}{}"

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.participant_team_list.value), json=error_data,
                      status=406)

    @responses.activate
    def test_participate_in_a_challenge_for_team_name_exists(self):
        user_prompt_text = ("Enter team name: : TeamTest\n"
                            "Please confirm the team name - TeamTest [y/N]: y\n")
        runner = CliRunner()
        result = runner.invoke(teams, ['create'], input="TeamTest\ny\n")
        response = result.output.rstrip()
        expected = "Error: participant team with this team name already exists."
        expected = "{}{}".format(user_prompt_text, expected)
        assert response == expected


class TestDisplayChallengePhasesWhenObjectDoesNotExist(BaseTestClass):

    def setup(self):

        error_data = json.loads(challenge_response.object_error)
        url = "{}{}"

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_list.value).format('10'),
                      json=error_data, status=406)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_detail.value).format('10', '20'),
                      json=error_data, status=406)

        self.expected = "Error: Sorry, the object does not exist."

    @responses.activate
    def test_display_challenge_phase_list_for_object_does_not_exist(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['10', 'phases'])
        response = result.output.rstrip()
        assert response == self.expected

    @responses.activate
    def test_display_challenge_phase_detail_for_object_does_not_exist(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['10', 'phase', '20'])
        response = result.output.rstrip()
        assert response == self.expected


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

        # Challenge URLS

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

        # Teams URLS

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_team_list.value), body=Exception('...'))

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.participant_team_list.value),
                      body=Exception('...'))

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.participate_in_a_challenge.value).format("2", "3"),
                      body=RequestException('...'))

        # Phase URLS

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_list.value).format('10'),
                      body=Exception('...'))

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_detail.value).format('10', '20'),
                      body=Exception('...'))

        # Submission URLS
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.my_submissions.value).format("3", "7"),
                      body=RequestException('...'))

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.get_submission.value).format("9"),
                      body=RequestException('RequestException'))

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.make_submission.value).format("1", "2"),
                      body=RequestException('RequestException'))

        # Phase Split URLS
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_split_detail.value).format("1"),
                      body=RequestException('...'))

        # Leaderboard URLS
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.leaderboard.value).format("1"),
                      body=RequestException('...'))

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

    @responses.activate
    def test_display_participant_team_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(teams)
        assert result.exit_code == -1

    @responses.activate
    def test_create_participant_team_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(teams, ['create'], input="TeamTest\ny\n")
        output = ("Enter team name: : TeamTest\n"
                  "Please confirm the team name - TeamTest [y/N]: y")
        assert result.output.strip() == output

    @responses.activate
    def test_participate_in_a_challenge_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['2', 'participate', '3'])
        assert result.output.strip() == "..."

    @responses.activate
    def test_display_challenge_phase_list_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['10', 'phases'])
        assert result.exit_code == -1

    @responses.activate
    def test_display_challenge_phase_detail_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['10', 'phase', '20'])
        assert result.exit_code == -1

    @responses.activate
    def test_display_my_submission_details_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['3', 'phase', '7', 'submissions'])
        assert result.output.strip() == "..."

    @responses.activate
    def test_display_submission_details_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(submission, ['9'])
        response = result.output.strip()
        assert response == "RequestException"

    @responses.activate
    def test_make_submission_for_request_exception(self):
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open('test_file.txt', 'w') as f:
                f.write('1 2 3 4 5 6')

            result = runner.invoke(challenge, ['1', 'phase', '2', 'submit', "test_file.txt"])
            response = result.output.strip()
            assert response == "RequestException"

    @responses.activate
    def test_display_challenge_phase_split_list_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['1', 'phase', '2', 'splits'])
        response = result.output.strip()
        assert response == "..."

    @responses.activate
    def test_display_leaderboard_for_request_exception(self):
        runner = CliRunner()
        result = runner.invoke(challenge, ['2', 'leaderboard', '1'])
        response = result.output.strip()
        assert response == "..."
