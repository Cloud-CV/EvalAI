import boto3
import mock
import os
import shutil
import tempfile

from datetime import timedelta
from moto import mock_sqs
from os.path import join

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from rest_framework.test import APITestCase

from challenges.models import (
    Challenge,
    ChallengePhase,
)
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from participants.models import ParticipantTeam
from scripts.workers.submission_worker import (
    create_dir,
    create_dir_as_python_package,
    extract_submission_data,
    load_challenge_and_return_max_submissions,
    return_file_url_per_environment,
    get_or_create_sqs_queue
)


class BaseAPITestClass(APITestCase):
    def setUp(self):

        self.BASE_TEMP_DIR = tempfile.mkdtemp()

        self.SUBMISSION_DATA_DIR = join(
            self.BASE_TEMP_DIR, "compute/submission_files/submission_{submission_id}"
        )

        self.temp_directory = join(self.BASE_TEMP_DIR, "temp_dir")

        self.testserver = "http://testserver"
        self.url = "/test/url"

        self.input_file = open(join(self.BASE_TEMP_DIR, 'dummy_input.txt'), "w+")
        self.input_file.write("file_content")
        self.input_file.close()

        self.sqs_client = boto3.client(
            "sqs",
            endpoint_url=os.environ.get("AWS_SQS_ENDPOINT", "http://sqs:9324"),
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        )
        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            max_concurrent_submission_evaluation=100,
            evaluation_script=SimpleUploadedFile(
                "test_sample_file.txt",
                b"Dummy file content",
                content_type="text/plain",
            ),
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Some Participant Team", created_by=self.user
        )

        self.challenge_phase = ChallengePhase.objects.create(
            name="Challenge Phase",
            description="Description for Challenge Phase",
            leaderboard_public=False,
            is_public=True,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            challenge=self.challenge,
            test_annotation=SimpleUploadedFile(
                "test_sample_file.txt",
                b"Dummy file content",
                content_type="text/plain",
            ),
            max_submissions_per_day=100,
            max_submissions_per_month=500,
            max_submissions=1000,
            codename="Phase Code Name",
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=SimpleUploadedFile(
                "test_sample_file.txt",
                b"Dummy file content",
                content_type="text/plain",
            ),
            method_name="Test Method",
            method_description="Test Description",
            project_url=self.testserver,
            publication_url=self.testserver,
            is_public=True,
            is_flagged=True,
        )

    def get_submission_input_file_path(self, submission_id, input_file):
        """Helper Method: Takes `submission_id` and `input_file` as input and
        returns corresponding path to submmitted input file"""

        input_file_name = os.path.basename(input_file.name)
        return join(self.SUBMISSION_DATA_DIR, "{input_file}").format(
            submission_id=submission_id,
            input_file=input_file_name,
        )

    def test_create_dir(self):
        create_dir(self.temp_directory)
        self.assertTrue(os.path.isdir(self.temp_directory))
        shutil.rmtree(self.temp_directory)

    def test_create_dir_as_python_package(self):
        create_dir_as_python_package(self.temp_directory)
        self.assertTrue(os.path.isfile(join(self.temp_directory, "__init__.py")))
        shutil.rmtree(self.temp_directory)

    def test_return_file_url_per_environment(self):
        returned_url = return_file_url_per_environment(self.url)
        self.assertEqual(returned_url, "{0}{1}".format(self.testserver, self.url))

    @mock.patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @mock.patch("scripts.workers.submission_worker.download_and_extract_file")
    def test_extract_submission_data_success(
            self,
            mock_download_and_extract_file,
            mock_create_dir_as_python_package):
        submission_input_file_path = join(
            self.SUBMISSION_DATA_DIR, "{input_file}"
        )
        mock_submission_data_dir = mock.patch(
            "scripts.workers.submission_worker.SUBMISSION_DATA_DIR",
            self.SUBMISSION_DATA_DIR
        )
        mock_submission_input_file_path = mock.patch(
            "scripts.workers.submission_worker.SUBMISSION_INPUT_FILE_PATH",
            submission_input_file_path,
        )
        mock_submission_data_dir.start()
        mock_submission_input_file_path.start()

        submission = extract_submission_data(self.submission.pk)

        expected_submission_data_dir = self.SUBMISSION_DATA_DIR.format(submission_id=self.submission.pk)
        mock_create_dir_as_python_package.assert_called_with(expected_submission_data_dir)

        expected_submission_input_file = "{0}{1}".format(self.testserver, self.submission.input_file.url)
        expected_submission_input_file_path = self.get_submission_input_file_path(
            self.submission.pk,
            self.submission.input_file,
        )
        mock_download_and_extract_file.assert_called_with(expected_submission_input_file, expected_submission_input_file_path)

        self.assertEqual(submission, self.submission)

        mock_submission_data_dir.stop()
        mock_submission_input_file_path.stop()

    @mock.patch("scripts.workers.submission_worker.logger.critical")
    def test_extract_submission_data_when_submission_does_not_exist(self, mock_logger):
        non_existing_submission_pk = self.submission.pk + 1
        value = extract_submission_data(non_existing_submission_pk)
        mock_logger.assert_called_with("Submission {} does not exist".format(non_existing_submission_pk))
        self.assertEqual(value, None)

    @mock.patch("scripts.workers.submission_worker.load_challenge")
    def test_load_challenge_and_return_max_submissions(self, mocked_load_challenge):
        q_params = {"pk": self.challenge.pk}
        response = load_challenge_and_return_max_submissions(q_params)
        mocked_load_challenge.assert_called_with(self.challenge)
        self.assertEqual(response, (self.challenge.max_concurrent_submission_evaluation, self.challenge))

    @mock.patch("scripts.workers.submission_worker.logger.exception")
    def test_load_challenge_and_return_max_submissions_when_challenge_does_not_exist(self, mock_logger):
        non_existing_challenge_pk = self.challenge.pk + 1
        with self.assertRaises(Challenge.DoesNotExist):
            load_challenge_and_return_max_submissions({"pk": non_existing_challenge_pk})
            mock_logger.assert_called_with("Challenge with pk {} doesn't exist".format(non_existing_challenge_pk))

    @mock_sqs()
    def test_get_or_create_sqs_queue_for_existing_queue(self):
        self.sqs_client.create_queue(QueueName="test_queue")
        get_or_create_sqs_queue("test_queue")
        queue_url = self.sqs_client.get_queue_url(QueueName='test_queue')['QueueUrl']
        self.assertTrue(queue_url)
        self.sqs_client.delete_queue(QueueUrl=queue_url)

    @mock_sqs()
    def test_get_or_create_sqs_queue_for_non_existing_queue(self):
        get_or_create_sqs_queue("test_queue_2")
        queue_url = self.sqs_client.get_queue_url(QueueName='test_queue_2')['QueueUrl']
        self.assertTrue(queue_url)
        self.sqs_client.delete_queue(QueueUrl=queue_url)
