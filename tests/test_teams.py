import json
import responses

from beautifultable import BeautifulTable
from click.testing import CliRunner

from evalai.teams import teams
from evalai.challenges import challenge

from tests.data import teams_response

from evalai.utils.config import API_HOST_URL
from evalai.utils.urls import URLS


class TestTeams:
    def setup(self):
        team_list_data = json.loads(teams_response.teams_list)
        team_created_data = json.loads(teams_response.create_team)

        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_team_list.value),
                      json=team_list_data, status=200)

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.participant_team_list.value),
                      json=team_created_data, status=201)

        responses.add(responses.POST, url.format(API_HOST_URL, URLS.participate_in_a_challenge.value).format("2", "3"),
                      json=team_list_data, status=201)

        self.teams = team_list_data["results"]

    @responses.activate
    def test_teams_list(self):
        table = BeautifulTable(max_width=200)
        attributes = ["id", "team_name", "created_by"]
        columns_attributes = ["ID", "Team Name", "Created By", "Members"]
        table.column_headers = columns_attributes
        for team in self.teams:
            values = list(map(lambda item: team[item], attributes))
            members = ", ".join(map(lambda member: member["member_name"], team["members"]))
            values.append(members)
            table.append_row(values)
        output = str(table)
        runner = CliRunner()
        result = runner.invoke(teams)
        response = result.output.rstrip()
        assert response == output

    @responses.activate
    def test_create_participant_team_for_option_yes(self):
        output = ("Enter team name: : TeamTest\n"
                  "Please confirm the team name - TeamTest [y/N]: y\n"
                  "\nThe team TestTeam was successfully created.\n\n")
        runner = CliRunner()
        result = runner.invoke(teams, ['create'], input="TeamTest\ny\n")
        response = result.output
        assert response == output

    @responses.activate
    def test_create_participant_team_for_option_no(self):
        output = ("Enter team name: : TeamTest\n"
                  "Please confirm the team name - TeamTest [y/N]: n\n"
                  "Aborted!\n")
        runner = CliRunner()
        result = runner.invoke(teams, ['create'], input="TeamTest\nn\n")
        response = result.output
        assert response == output

    @responses.activate
    def test_participate_in_a_challenge(self):
        output = "Your team id {} is now participating in this challenge!\n".format("3")
        runner = CliRunner()
        result = runner.invoke(challenge, ['2', 'participate', '3'])
        response = result.output
        assert response == output

    @responses.activate
    def test_participate_in_a_challenge_with_single_argument(self):
        output = ("Usage: challenge [OPTIONS] CHALLENGE COMMAND [ARGS]...\n"
                  "\nError: Missing command.\n")
        runner = CliRunner()
        result = runner.invoke(challenge, ['2'])
        response = result.output
        assert response == output

    @responses.activate
    def test_participate_in_a_challenge_with_string_argument(self):
        output = ("Usage: challenge [OPTIONS] CHALLENGE COMMAND [ARGS]...\n"
                  "\nError: Invalid value for \"CHALLENGE\": two is not a valid integer\n")
        runner = CliRunner()
        result = runner.invoke(challenge, ['two', 'participate', '3'])
        response = result.output
        assert response == output


class TestDisplayTeamsListWithNoTeamsData:

    def setup(self):
        team_list_data = '{"count": 2, "next": null, "previous": null, "results": []}'
        url = "{}{}"
        responses.add(responses.GET, url.format(API_HOST_URL, URLS.participant_team_list.value),
                      json=json.loads(team_list_data), status=200)

    @responses.activate
    def test_teams_list_with_no_teams_data(self):
        expected = "Sorry, no teams found!\n"
        runner = CliRunner()
        result = runner.invoke(teams)
        response = result.output
        assert response == expected
