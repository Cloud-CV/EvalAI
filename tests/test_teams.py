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
        host_team = json.loads(teams_response.host_teams)

        url = "{}{}"
        responses.add(
            responses.GET,
            url.format(API_HOST_URL, URLS.participant_team_list.value),
            json=team_list_data,
            status=200,
        )

        responses.add(
            responses.POST,
            url.format(API_HOST_URL, URLS.participant_team_list.value),
            json=team_created_data,
            status=201,
        )

        responses.add(
            responses.POST,
            url.format(API_HOST_URL, URLS.create_host_team.value),
            json=team_created_data,
            status=201,
        )

        responses.add(
            responses.POST,
            url.format(API_HOST_URL, URLS.participate_in_a_challenge.value).format(
                "2", "3"
            ),
            json=team_list_data,
            status=201,
        )

        responses.add(
            responses.GET,
            url.format(API_HOST_URL, URLS.host_team_list.value),
            json=host_team,
            status=201,
        )

        self.participant_teams = team_list_data["results"]
        self.host_teams = host_team["results"]

    @responses.activate
    def test_display_participant_teams_list(self):
        table = BeautifulTable(max_width=200)
        attributes = ["id", "team_name", "created_by"]
        columns_attributes = ["ID", "Team Name", "Created By", "Members", "Team URL"]
        table.column_headers = columns_attributes
        for team in self.participant_teams:
            values = list(map(lambda item: team[item], attributes))
            members = ", ".join(
                map(lambda member: member["member_name"], team["members"])
            )
            values.append(members)
            if team["team_url"]:
                values.append(team["team_url"])
            else:
                values.append("None")
            table.append_row(values)
        output = str(table)
        runner = CliRunner()
        result = runner.invoke(teams, ["--participant"])
        response = result.output.rstrip()
        assert response == output

    @responses.activate
    def test_display_host_teams_list(self):
        table = BeautifulTable(max_width=200)
        attributes = ["id", "team_name", "created_by"]
        columns_attributes = ["ID", "Team Name", "Created By", "Members", "Team URL"]
        table.column_headers = columns_attributes
        for team in self.host_teams:
            values = list(map(lambda item: team[item], attributes))
            members = ", ".join(map(lambda member: member["user"], team["members"]))
            values.append(members)
            if team["team_url"]:
                values.append(team["team_url"])
            else:
                values.append("None")
            table.append_row(values)
        output = str(table)
        runner = CliRunner()
        result = runner.invoke(teams, ["--host"])
        response = result.output.rstrip()
        assert response == output

    @responses.activate
    def test_create_participant_team_for_option_yes(self):
        output = (
            "Enter team name: TeamTest\n"
            "Please confirm the team name - TeamTest [y/N]: y\n"
            "Do you want to enter the Team URL [y/N]: N\n"
            "\nYour participant team TestTeam was successfully created."
        )
        runner = CliRunner()
        result = runner.invoke(teams, ["create", "participant"], input="TeamTest\ny\nN")
        response = result.output.strip()
        assert response == output

    @responses.activate
    def test_create_host_team_for_option_yes(self):
        output = (
            "Enter team name: TeamTest\n"
            "Please confirm the team name - TeamTest [y/N]: y\n"
            "Do you want to enter the Team URL [y/N]: N\n"
            "\nYour host team TestTeam was successfully created."
        )
        runner = CliRunner()
        result = runner.invoke(teams, ["create", "host"], input="TeamTest\ny\nN")
        response = result.output.strip()
        assert response == output

    @responses.activate
    def test_create_team_for_option_no(self):
        output = (
            "Enter team name: TeamTest\n"
            "Please confirm the team name - TeamTest [y/N]: n\n"
            "Aborted!\n"
        )
        runner = CliRunner()
        result = runner.invoke(teams, ["create", "host"], input="TeamTest\nn\n")
        response = result.output
        assert response == output

    @responses.activate
    def test_create_host_team_for_option_yes_with_valid_team_url(self):
        output = (
            "Enter team name: TeamTest\n"
            "Please confirm the team name - TeamTest [y/N]: y\n"
            "Do you want to enter the Team URL [y/N]: Y\n"
            "Team URL: http://testteam.com\n"
            "\nYour host team TestTeam was successfully created."
        )
        runner = CliRunner()
        result = runner.invoke(
            teams, ["create", "host"], input="TeamTest\ny\nY\nhttp://testteam.com\n"
        )
        response = result.output.strip()
        assert response == output

    @responses.activate
    def test_create_host_team_for_option_yes_with_invalid_team_url(self):
        output = (
            "Enter team name: TeamTest\n"
            "Please confirm the team name - TeamTest [y/N]: y\n"
            "Do you want to enter the Team URL [y/N]: Y\n"
            "Team URL: TestURL\n"
            "Sorry, please enter a valid link.\n"
            "Team URL: http://testteam.com\n"
            "\nYour host team TestTeam was successfully created."
        )
        runner = CliRunner()
        result = runner.invoke(
            teams,
            ["create", "host"],
            input="TeamTest\ny\nY\nTestURL\nhttp://testteam.com",
        )
        response = result.output.strip()
        assert response == output

    @responses.activate
    def test_create_team_for_wrong_argument(self):
        output = "Sorry, wrong argument. Please choose either participant or host."
        runner = CliRunner()
        result = runner.invoke(teams, ["create", "test"])
        response = result.output.strip()
        assert response == output

    @responses.activate
    def test_participate_in_a_challenge(self):
        output = "Your team id {} is now participating in this challenge.\n".format("3")
        runner = CliRunner()
        result = runner.invoke(challenge, ["2", "participate", "3"])
        response = result.output
        assert response == output

    @responses.activate
    def test_participate_in_a_challenge_with_single_argument(self):
        output = (
            "Usage: challenge participate [OPTIONS] TEAM\n"
            '\nError: Missing argument "TEAM".\n'
        )
        runner = CliRunner()
        result = runner.invoke(challenge, ["2", "participate"])
        response = result.output
        assert response == output

    @responses.activate
    def test_participate_in_a_challenge_with_string_argument(self):
        output = (
            "Usage: challenge [OPTIONS] CHALLENGE COMMAND [ARGS]...\n"
            '\nError: Invalid value for "CHALLENGE": two is not a valid integer\n'
        )
        runner = CliRunner()
        result = runner.invoke(challenge, ["two", "participate", "3"])
        response = result.output
        assert response == output


class TestDisplayTeamsListWithNoTeamsData:
    def setup(self):
        team_list_data = '{"count": 2, "next": null, "previous": null, "results": []}'
        url = "{}{}"
        responses.add(
            responses.GET,
            url.format(API_HOST_URL, URLS.participant_team_list.value),
            json=json.loads(team_list_data),
            status=200,
        )

    @responses.activate
    def test_teams_list_with_no_teams_data(self):
        expected = "Sorry, no teams found.\n"
        runner = CliRunner()
        result = runner.invoke(teams, ["--participant"])
        response = result.output
        assert response == expected
