import json
import responses

from click.testing import CliRunner

from evalai.challenges import (challenge,
                               challenges)
from evalai.utils.urls import URLS
from evalai.utils.config import API_HOST_URL
from tests.data import challenge_response

from .base import BaseTestClass


class TestDisplayChallenges(BaseTestClass):

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

    @responses.activate
    def test_diaplay_all_challenge_lists(self):
        runner = CliRunner()
        result = runner.invoke(challenges)
        response_table = result.output
        assert response_table == self.output

    @responses.activate
    def test_display_past_challenge_lists(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['past'])
        response_table = result.output
        assert response_table == self.output

    @responses.activate
    def test_display_ongoing_challenge_lists(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['ongoing'])
        response_table = result.output
        assert response_table == self.output

    @responses.activate
    def test_display_future_challenge_lists(self):
        runner = CliRunner()
        result = runner.invoke(challenges, ['future'])
        response_table = result.output
        assert response_table == self.output


class TestDisplayChallengesWithNoChallengeData(BaseTestClass):

    def setup(self):

        participant_team_data = json.loads(challenge_response.challenge_participant_teams)
        host_team_data = json.loads(challenge_response.challenge_host_teams)

        url = "{}{}"

        challenges = '{"count": 2, "next": null, "previous": null,"results": []}'

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_list.value),
                      json=json.loads(challenges), status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_teams.value),
                      json=participant_team_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_teams.value),
                      json=host_team_data, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_challenges.value).format("3"),
                      json=json.loads(challenges), status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.host_challenges.value).format("2"),
                      json=json.loads(challenges), status=200)

        self.output = "Sorry, no challenges found!\n"

    @responses.activate
    def test_display_all_challenge_lists_with_no_challenge_data(self):
        runner = CliRunner()
        result = runner.invoke(challenges)
        response = result.output
        assert response == self.output

    @responses.activate
    def test_display_host_challenge_list_with_no_challenge_data(self):
        runner = CliRunner()
        expected = "\nHosted Challenges\n\n"
        self.output = "{}{}".format(expected, self.output)
        result = runner.invoke(challenges, ['--host'])
        response = result.output
        assert response == self.output

    @responses.activate
    def test_display_participant_challenge_lists_with_no_challenge_data(self):
        runner = CliRunner()
        expected = "\nParticipated Challenges\n\n"
        self.output = "{}{}".format(expected, self.output)
        result = runner.invoke(challenges, ['--participant'])
        response = result.output
        assert response == self.output

    @responses.activate
    def test_display_participant_and_host_challenge_lists_with_no_challenge_data(self):
        runner = CliRunner()
        participant_string = "\nParticipated Challenges\n\n"
        host_string = "\nHosted Challenges\n\n"
        self.output = "{}{}{}{}".format(host_string, self.output, participant_string, self.output)
        result = runner.invoke(challenges, ['--participant', '--host'])
        response = result.output
        assert response == self.output


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

        challenges_json = challenge_data["results"]

        self.output = ""

        title = "\n{}".format("{}")
        id_field = "{}\n\n".format("{}")
        subtitle = "\n{}\n\n".format("{}")
        br = "------------------------------------------------------------------\n"

        for challenge_data in challenges_json:
            challenge_title = title.format(challenge_data["title"])
            challenge_id = "ID: " + id_field.format(challenge_data["id"])

            heading = "{} {}".format(challenge_title, challenge_id)
            description = "{}\n".format(challenge_data["short_description"])
            end_date = "End Date : " + challenge_data["end_date"].split("T")[0]
            end_date = subtitle.format(end_date)
            challenge_data = "{}{}{}{}".format(heading, description, end_date, br)

            self.output = "{}{}".format(self.output, challenge_data)

    @responses.activate
    def test_display_host_challenge_list(self):
        runner = CliRunner()
        expected = "\nHosted Challenges\n\n"
        self.output = "{}{}".format(expected, self.output)
        result = runner.invoke(challenges, ['--host'])
        response = result.output
        assert response == self.output

    @responses.activate
    def test_display_participant_challenge_lists(self):
        runner = CliRunner()
        expected = "\nParticipated Challenges\n\n"
        self.output = "{}{}".format(expected, self.output)
        result = runner.invoke(challenges, ['--participant'])
        response = result.output
        assert response == self.output

    @responses.activate
    def test_display_participant_and_host_challenge_lists(self):
        runner = CliRunner()
        participant_string = "\nParticipated Challenges\n\n"
        host_string = "\nHosted Challenges\n\n"
        self.output = "{}{}{}{}".format(host_string, self.output, participant_string, self.output)
        result = runner.invoke(challenges, ['--participant', '--host'])
        response = result.output
        assert response == self.output


class TestDisplayChallengePhases(BaseTestClass):

    def setup(self):
        challenge_phase_list_json = json.loads(challenge_response.challenge_phase_list)
        challenge_phase_details_json = json.loads(challenge_response.challenge_phase_details)

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_list.value).format('10'),
                      json=challenge_phase_list_json, status=200)

        responses.add(responses.GET, url.format(API_HOST_URL, URLS.challenge_phase_detail.value).format('10', '20'),
                      json=challenge_phase_details_json, status=200)
        self.phases = challenge_phase_list_json['results']
        self.phase = challenge_phase_details_json

    @responses.activate
    def test_display_challenge_phase_list(self):

        self.output = ""

        for phase in self.phases:
            br = ("--------------------------------"
                  "----------------------------------")

            phase_title = "\n{}".format(phase["name"])
            challenge_id = "Challenge ID: {}".format(str(phase["challenge"]))
            phase_id = "Phase ID: {}\n\n".format(str(phase["id"]))

            title = "{} {} {}".format(phase_title, challenge_id, phase_id)

            description = "{}\n\n".format(phase["description"])
            phase = "{}{}{}\n".format(title, description, br)

            self.output += phase

        runner = CliRunner()
        result = runner.invoke(challenge, ['10', 'phases'])
        response = result.output
        assert response == self.output

    @responses.activate
    def test_display_challenge_phase_detail(self):

        phase = self.phase
        phase_title = "\n{}".format(phase["name"])
        challenge_id = "Challenge ID: {}".format(str(phase["challenge"]))
        phase_id = "Phase ID: {}\n\n".format(str(phase["id"]))

        title = "{} {} {}".format(phase_title, challenge_id, phase_id)

        description = "{}\n".format(phase["description"])

        start_date = "Start Date : " + phase["start_date"].split("T")[0]
        start_date = "\n{}\n".format(start_date)

        end_date = "End Date : " + phase["end_date"].split("T")[0]
        end_date = "\n{}\n".format(end_date)

        max_submissions_per_day = "\nMaximum Submissions per day : {}\n".format(
                                    str(phase["max_submissions_per_day"]))

        max_submissions = "\nMaximum Submissions : {}\n".format(
                                    str(phase["max_submissions"]))

        codename = "\nCode Name : {}\n".format(
                                              phase["codename"])

        leaderboard_public = "\nLeaderboard Public : {}\n".format(
                                              phase["leaderboard_public"])

        is_active = "\nActive : {}\n".format(phase["is_active"])

        is_public = "\nPublic : {}\n".format(phase["is_public"])

        phase = "{}{}{}{}{}{}{}{}{}{}\n".format(title, description, start_date, end_date,
                                                max_submissions_per_day, max_submissions, leaderboard_public,
                                                codename, is_active, is_public)

        runner = CliRunner()
        result = runner.invoke(challenge, ['10', 'phase', '20'])
        response = result.output
        assert response == phase
