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
    return_file_url_per_environment,
    get_or_create_sqs_queue
)


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.BASE_TEMP_DIR = tempfile.mkdtemp()
        self.temp_directory = join(self.BASE_TEMP_DIR, "temp_dir")
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
            max_concurrent_submission_evaluation=200000,
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
            max_submissions_per_day=100000,
            max_submissions_per_month=100000,
            max_submissions=100000,
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
            method_name="Test Method 1",
            method_description="Test Description 1",
            project_url="http://testserver1/",
            publication_url="http://testserver1/",
            is_public=True,
            is_flagged=True,
        )
        self.testserver = "http://testserver"

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

    @mock.patch("scripts.workers.submission_worker.SUBMISSION_DATA_DIR", "/tmp/test-dir/compute/submission_files/submission_{submission_id}")
    @mock.patch("scripts.workers.submission_worker.SUBMISSION_INPUT_FILE_PATH", "/tmp/test-dir/compute/submission_files/submission_{submission_id}/{input_file}")
    @mock.patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @mock.patch("scripts.workers.submission_worker.download_and_extract_file")
    def test_extract_submission_data_successful(self, mock_download_and_extract_file, mock_create_dir_as_python_package):
        submission = extract_submission_data(self.submission.pk)
        expected_submission_data_dir = "/tmp/test-dir/compute/submission_files/submission_{submission_id}".format(submission_id=self.submission.pk)
        mock_create_dir_as_python_package.assert_called_with(expected_submission_data_dir)
        expected_submission_input_file = "{0}{1}".format(self.testserver, self.submission.input_file.url)
        expected_submission_input_file_path = "/tmp/test-dir/compute/submission_files/submission_{submission_id}/{input_file}".format(submission_id=self.submission.pk, input_file=os.path.basename(self.submission.input_file.name))
        mock_download_and_extract_file.assert_called_with(expected_submission_input_file, expected_submission_input_file_path)
        self.assertEqual(submission, self.submission)

    @mock.patch("scripts.workers.submission_worker.logger.critical")
    def test_extract_submission_data_when_submission_does_not_exist(self, mock_logger):
        non_existing_submission_pk = self.submission.pk + 1
        value = extract_submission_data(non_existing_submission_pk)
        mock_logger.assert_called_with("Submission {} does not exist".format(non_existing_submission_pk))
        self.assertEqual(value, None)

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
