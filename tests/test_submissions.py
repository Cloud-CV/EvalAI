import docker
import json
import os
import pytest
import responses
import socket

from click.testing import CliRunner
from datetime import datetime
from dateutil import tz

from evalai.challenges import challenge
from evalai.submissions import submission, push
from tests.data import submission_response, challenge_response

from evalai.utils.config import API_HOST_URL
from evalai.utils.urls import URLS
from .base import BaseTestClass


class TestGetSubmissionDetails(BaseTestClass):
    def setup(self):

        self.submission = json.loads(submission_response.submission_result)

        url = "{}{}"
        responses.add(
            responses.GET,
            url.format(API_HOST_URL, URLS.get_submission.value).format("9"),
            json=self.submission,
            status=200,
        )

        responses.add(
            responses.GET,
            self.submission["submission_result_file"],
            json=json.loads(submission_response.submission_result_file),
            status=200,
        )

    @responses.activate
    def test_display_submission_details(self):
        team_title = "\n{}".format(self.submission["participant_team_name"])
        sid = "Submission ID: {}\n".format(str(self.submission["id"]))

        team = "{} {}".format(team_title, sid)

        status = "\nSubmission Status : {}\n".format(self.submission["status"])
        execution_time = "\nExecution Time (sec) : {}\n".format(
            self.submission["execution_time"]
        )

        date = datetime.strptime(
            self.submission["submitted_at"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()

        date = date.replace(tzinfo=from_zone)
        converted_date = date.astimezone(to_zone)

        date = converted_date.strftime("%D %r")
        submitted_at = "\nSubmitted At : {}\n".format(date)
        submission_data = "{}{}{}{}\n".format(
            team, status, execution_time, submitted_at
        )

        runner = CliRunner()
        result = runner.invoke(submission, ["9"])
        response = result.output
        assert response == submission_data

    @responses.activate
    def test_display_submission_details_with_a_string_argument(self):
        expected = (
            "Usage: submission [OPTIONS] SUBMISSION_ID COMMAND [ARGS]...\n"
            '\nError: Invalid value for "SUBMISSION_ID": two is not a valid integer\n'
        )
        runner = CliRunner()
        result = runner.invoke(submission, ["two"])
        response = result.output
        assert response == expected

    @responses.activate
    def test_display_submission_details_with_no_argument(self):
        expected = (
            "Usage: submission [OPTIONS] SUBMISSION_ID COMMAND [ARGS]...\n"
            '\nError: Missing argument "SUBMISSION_ID".\n'
        )
        runner = CliRunner()
        result = runner.invoke(submission)
        response = result.output
        assert response == expected

    @responses.activate
    def test_display_submission_result(self):
        expected = "{}\n".format(
            submission_response.submission_result_file
        ).strip()
        runner = CliRunner()
        result = runner.invoke(submission, ["9", "result"])
        response = result.output.strip()
        assert response == expected


class TestMakeSubmission(BaseTestClass):
    def setup(self):
        self.submission = json.loads(submission_response.submission_result)

        url = "{}{}"
        responses.add(
            responses.POST,
            url.format(API_HOST_URL, URLS.make_submission.value).format(
                "1", "2"
            ),
            json=self.submission,
            status=200,
        )

        url = "{}{}"
        responses.add(
            responses.POST,
            url.format(API_HOST_URL, URLS.make_submission.value).format(
                "10", "2"
            ),
            json=self.submission,
            status=200,
        )

        # To get AWS Credentials
        url = "{}{}"
        responses.add(
            responses.GET,
            url.format(API_HOST_URL, URLS.get_aws_credentials.value).format(
                "2"
            ),
            json=json.loads(submission_response.aws_credentials),
            status=200,
        )

        # To get Challenge Phase Details
        url = "{}{}"
        responses.add(
            responses.GET,
            url.format(
                API_HOST_URL, URLS.challenge_phase_details.value
            ).format("2"),
            json=json.loads(challenge_response.challenge_phase_details),
            status=200,
        )

        # To get Challenge Phase Details using slug
        url = "{}{}"
        responses.add(
            responses.GET,
            url.format(
                API_HOST_URL, URLS.phase_details_using_slug.value
            ).format("philip-phase-2019"),
            json=json.loads(challenge_response.challenge_phase_details_slug),
            status=200,
        )

        # To get Challenge Details
        url = "{}{}"
        responses.add(
            responses.GET,
            url.format(API_HOST_URL, URLS.challenge_details.value).format(
                "10"
            ),
            json=json.loads(challenge_response.challenge_details),
            status=200,
        )

        responses.add_passthru("http+docker://localhost/")

    @responses.activate
    def test_make_submission_when_file_is_not_valid(self):
        expected = (
            "Usage: challenge phase submit [OPTIONS]\n"
            '\nError: Invalid value for "--file": Could not open file: file: No such file or directory\n'
        )
        runner = CliRunner()
        result = runner.invoke(
            challenge, ["1", "phase", "2", "submit", "--file", "file"]
        )
        response = result.output
        assert response == expected

    @responses.activate
    def test_make_submission_when_file_is_valid_without_metadata(self):
        expected = (
            "Your file {} with the ID {} is successfully submitted.\n\n"
            "You can use `evalai submission {}` to view this submission's status."
        ).format("test_file.txt", "9", "9")
        expected = "Do you want to include the Submission Details? [y/N]: N\n\n{}".format(
            expected
        )
        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("test_file.txt", "w") as f:
                f.write("1 2 3 4 5 6")

            result = runner.invoke(
                challenge,
                ["1", "phase", "2", "submit", "--file", "test_file.txt"],
                input="N",
            )
            assert result.exit_code == 0
            assert result.output.strip() == expected

    @responses.activate
    def test_make_submission_when_file_is_valid_with_metadata(self):
        expected = "Do you want to include the Submission Details? [y/N]: Y"
        expected = "{}\n{}".format(
            expected,
            (
                "Method Name []: Test\nMethod Description []: "
                "Test\nProject URL []: Test\nPublication URL []: Test\n"
            ),
        )
        expected = "{}\n{}".format(
            expected,
            (
                "Your file {} with the ID {} is successfully submitted.\n\n"
                "You can use `evalai submission {}` to view this "
                "submission's status."
            ).format("test_file.txt", "9", "9"),
        )

        runner = CliRunner()
        with runner.isolated_filesystem():
            with open("test_file.txt", "w") as f:
                f.write("1 2 3 4 5 6")

            result = runner.invoke(
                challenge,
                ["1", "phase", "2", "submit", "--file", "test_file.txt"],
                input="Y\nTest\nTest\nTest\nTest",
            )
            assert result.exit_code == 0
            assert result.output.strip() == expected

    @pytest.fixture()
    def test_make_submission_for_docker_based_challenge_setup(self, request):
        def get_open_port():
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(("", 0))
            s.listen(1)
            port = s.getsockname()[1]
            s.close()
            return port

        registry_port = get_open_port()
        client = docker.from_env()
        image_tag = "evalai-push-test:v1"
        client.images.build(
            path=os.path.join(os.path.dirname(__file__), "data"), tag=image_tag
        )
        container = client.containers.run(
            "registry:2",
            name="registry-test",
            detach=True,
            ports={"5000/tcp": registry_port},
            auto_remove=True,
        )

        def test_make_submission_for_docker_based_challenge_teardown():
            container.stop(timeout=1)

        request.addfinalizer(
            test_make_submission_for_docker_based_challenge_teardown
        )
        return (registry_port, image_tag)

    @responses.activate
    def test_make_submission_for_docker_based_challenge(
        self, test_make_submission_for_docker_based_challenge_setup
    ):
        registry_port, image_tag = (
            test_make_submission_for_docker_based_challenge_setup
        )
        runner = CliRunner()
        with runner.isolated_filesystem():
            result = runner.invoke(
                push,
                [
                    image_tag,
                    "-p",
                    "philip-phase-2019",
                    "-u",
                    "localhost:{0}".format(registry_port),
                ],
            )
            assert result.exit_code == 0
