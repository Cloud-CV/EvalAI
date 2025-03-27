import os
import shutil
import tempfile
import zipfile
from datetime import timedelta
from io import BytesIO
from os.path import join

import boto3
import mock
import responses
from challenges.models import Challenge, ChallengePhase
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from moto import mock_sqs
from participants.models import ParticipantTeam
from rest_framework.test import APITestCase

from scripts.workers.submission_worker import (
    create_dir,
    create_dir_as_python_package,
    download_and_extract_file,
    delete_zip_file,
    download_and_extract_zip_file,
    extract_zip_file,
    extract_submission_data,
    load_challenge_and_return_max_submissions,
    return_file_url_per_environment,
    get_or_create_sqs_queue,
)
from settings.common import SQS_RETENTION_PERIOD


class BaseAPITestClass(APITestCase):
    def setUp(self):

        self.BASE_TEMP_DIR = tempfile.mkdtemp()

        self.SUBMISSION_DATA_DIR = join(
            self.BASE_TEMP_DIR,
            "compute/submission_files/submission_{submission_id}",
        )

        self.temp_directory = join(self.BASE_TEMP_DIR, "temp_dir")

        self.testserver = (
            f"http://{settings.DJANGO_SERVER}:{settings.DJANGO_SERVER_PORT}"
        )
        self.url = "/test/url"

        self.input_file = open(
            join(self.BASE_TEMP_DIR, "dummy_input.txt"), "w+"
        )
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

        self.challenge2 = Challenge.objects.create(
            title="Test Challenge 2",
            description="Description for test challenge 2",
            terms_and_conditions="Terms and conditions for test challenge 2",
            submission_guidelines="Submission guidelines for test challenge 2",
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
            use_host_sqs=True,
            aws_region=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
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

        self.WORKER_LOGS_PREFIX = "WORKER_LOG"
        self.SUBMISSION_LOGS_PREFIX = "SUBMISSION_LOG"

    def get_submission_input_file_path(self, submission_id, input_file):
        """Helper Method: Takes `submission_id` and `input_file` as input and
        returns corresponding path to submitted input file"""

        input_file_name = os.path.basename(input_file.name)
        return join(self.SUBMISSION_DATA_DIR, "{input_file}").format(
            submission_id=submission_id, input_file=input_file_name
        )

    def test_create_dir(self):
        create_dir(self.temp_directory)
        self.assertTrue(os.path.isdir(self.temp_directory))
        shutil.rmtree(self.temp_directory)

    def test_create_dir_as_python_package(self):
        create_dir_as_python_package(self.temp_directory)
        self.assertTrue(
            os.path.isfile(join(self.temp_directory, "__init__.py"))
        )
        shutil.rmtree(self.temp_directory)

    def test_return_file_url_per_environment(self):
        returned_url = return_file_url_per_environment(self.url)
        self.assertEqual(
            returned_url, "{0}{1}".format(self.testserver, self.url)
        )

    @mock.patch(
        "scripts.workers.submission_worker.create_dir_as_python_package"
    )
    @mock.patch("scripts.workers.submission_worker.download_and_extract_file")
    def test_extract_submission_data_success(
        self, mock_download_and_extract_file, mock_create_dir_as_python_package
    ):
        submission_input_file_path = join(
            self.SUBMISSION_DATA_DIR, "{input_file}"
        )
        mock_submission_data_dir = mock.patch(
            "scripts.workers.submission_worker.SUBMISSION_DATA_DIR",
            self.SUBMISSION_DATA_DIR,
        )
        mock_submission_input_file_path = mock.patch(
            "scripts.workers.submission_worker.SUBMISSION_INPUT_FILE_PATH",
            submission_input_file_path,
        )
        mock_submission_data_dir.start()
        mock_submission_input_file_path.start()

        submission = extract_submission_data(self.submission.pk)

        expected_submission_data_dir = self.SUBMISSION_DATA_DIR.format(
            submission_id=self.submission.pk
        )
        mock_create_dir_as_python_package.assert_called_with(
            expected_submission_data_dir
        )

        expected_submission_input_file = "{0}{1}".format(
            self.testserver, self.submission.input_file.url
        )
        expected_submission_input_file_path = (
            self.get_submission_input_file_path(
                self.submission.pk, self.submission.input_file
            )
        )
        mock_download_and_extract_file.assert_called_with(
            expected_submission_input_file, expected_submission_input_file_path
        )

        self.assertEqual(submission, self.submission)

        mock_submission_data_dir.stop()
        mock_submission_input_file_path.stop()

    @mock.patch("scripts.workers.submission_worker.logger.critical")
    def test_extract_submission_data_when_submission_does_not_exist(
        self, mock_logger
    ):
        non_existing_submission_pk = self.submission.pk + 1
        value = extract_submission_data(non_existing_submission_pk)
        mock_logger.assert_called_with(
            "{} Submission {} does not exist".format(
                self.SUBMISSION_LOGS_PREFIX, non_existing_submission_pk
            )
        )
        self.assertEqual(value, None)

    @mock.patch("scripts.workers.submission_worker.load_challenge")
    def test_load_challenge_and_return_max_submissions(
        self, mocked_load_challenge
    ):
        q_params = {"pk": self.challenge.pk}
        response = load_challenge_and_return_max_submissions(q_params)
        mocked_load_challenge.assert_called_with(self.challenge)
        self.assertEqual(
            response,
            (
                self.challenge.max_concurrent_submission_evaluation,
                self.challenge,
            ),
        )

    @mock.patch("scripts.workers.submission_worker.logger.exception")
    def test_load_challenge_and_return_max_submissions_when_challenge_does_not_exist(
        self, mock_logger
    ):
        non_existing_challenge_pk = self.challenge.pk + 2
        with self.assertRaises(Challenge.DoesNotExist):
            load_challenge_and_return_max_submissions(
                {"pk": non_existing_challenge_pk}
            )
            mock_logger.assert_called_with(
                "Challenge with pk {} doesn't exist".format(
                    non_existing_challenge_pk
                )
            )

    @mock_sqs()
    def test_get_or_create_sqs_queue_for_existing_queue(self):
        self.sqs_client.create_queue(
            QueueName="test_queue",
            Attributes={"MessageRetentionPeriod": SQS_RETENTION_PERIOD},
        )
        get_or_create_sqs_queue("test_queue")
        queue_url = self.sqs_client.get_queue_url(QueueName="test_queue")[
            "QueueUrl"
        ]
        self.assertTrue(queue_url)
        self.sqs_client.delete_queue(QueueUrl=queue_url)

    @mock_sqs()
    def test_get_or_create_sqs_queue_for_non_existing_queue(self):
        get_or_create_sqs_queue("test_queue_2")
        queue_url = self.sqs_client.get_queue_url(QueueName="test_queue_2")[
            "QueueUrl"
        ]
        self.assertTrue(queue_url)
        self.sqs_client.delete_queue(QueueUrl=queue_url)

    @mock_sqs()
    def test_get_or_create_sqs_queue_for_existing_host_queue(self):
        get_or_create_sqs_queue("test_host_queue_2", self.challenge2)
        queue_url = self.sqs_client.get_queue_url(QueueName="test_host_queue_2")[
            "QueueUrl"
        ]
        self.assertTrue(queue_url)
        self.sqs_client.delete_queue(QueueUrl=queue_url)


class DownloadAndExtractFileTest(BaseAPITestClass):
    def setUp(self):
        super(DownloadAndExtractFileTest, self).setUp()
        self.req_url = "{}{}".format(self.testserver, self.url)
        self.file_content = b"file content"

        create_dir(self.temp_directory)
        self.download_location = join(self.temp_directory, "dummy_file")

    def tearDown(self):
        if os.path.exists(self.temp_directory):
            shutil.rmtree(self.temp_directory)

    @responses.activate
    def test_download_and_extract_file_success(self):
        responses.add(
            responses.GET,
            self.req_url,
            body=self.file_content,
            content_type="application/octet-stream",
            status=200,
        )

        download_and_extract_file(self.req_url, self.download_location)

        self.assertTrue(os.path.exists(self.download_location))
        with open(self.download_location, "rb") as f:
            self.assertEqual(f.read(), self.file_content)

    @responses.activate
    @mock.patch("scripts.workers.submission_worker.logger.error")
    def test_download_and_extract_file_when_download_fails(self, mock_logger):
        error = "ExampleError: Example Error description"
        responses.add(responses.GET, self.req_url, body=Exception(error))
        expected = "{} Failed to fetch file from {}, error {}".format(
            self.WORKER_LOGS_PREFIX, self.req_url, error
        )

        download_and_extract_file(self.req_url, self.download_location)

        mock_logger.assert_called_with(expected)
        self.assertFalse(os.path.exists(self.download_location))


class DownloadAndExtractZipFileTest(BaseAPITestClass):
    def setUp(self):
        super(DownloadAndExtractZipFileTest, self).setUp()
        self.zip_name = "test"
        self.req_url = "{}/{}".format(self.testserver, self.zip_name)
        self.extract_location = join(self.BASE_TEMP_DIR, "test-dir")
        self.download_location = join(
            self.extract_location, "{}.zip".format(self.zip_name)
        )
        create_dir(self.extract_location)

        self.file_name = "test_file.txt"
        self.file_content = b"file_content"

        self.zip_file = BytesIO()
        with zipfile.ZipFile(
            self.zip_file, mode="w", compression=zipfile.ZIP_DEFLATED
        ) as zipper:
            zipper.writestr(self.file_name, self.file_content)

    def tearDown(self):
        if os.path.exists(self.extract_location):
            shutil.rmtree(self.extract_location)

    @responses.activate
    @mock.patch("scripts.workers.submission_worker.delete_zip_file")
    @mock.patch("scripts.workers.submission_worker.extract_zip_file")
    def test_download_and_extract_zip_file_success(
        self, mock_extract_zip, mock_delete_zip
    ):
        responses.add(
            responses.GET,
            self.req_url,
            content_type="application/zip",
            body=self.zip_file.getvalue(),
            status=200,
        )

        download_and_extract_zip_file(
            self.req_url, self.download_location, self.extract_location
        )

        with open(self.download_location, "rb") as downloaded:
            self.assertEqual(downloaded.read(), self.zip_file.getvalue())
        mock_extract_zip.assert_called_with(
            self.download_location, self.extract_location
        )
        mock_delete_zip.assert_called_with(self.download_location)

    @responses.activate
    @mock.patch("scripts.workers.submission_worker.logger.error")
    def test_download_and_extract_zip_file_when_download_fails(
        self, mock_logger
    ):
        e = "Error description"
        responses.add(responses.GET, self.req_url, body=Exception(e))
        error_message = "{} Failed to fetch file from {}, error {}".format(
            self.WORKER_LOGS_PREFIX, self.req_url, e
        )

        download_and_extract_zip_file(
            self.req_url, self.download_location, self.extract_location
        )

        mock_logger.assert_called_with(error_message)

    def test_extract_zip_file(self):
        with open(self.download_location, "wb") as zf:
            zf.write(self.zip_file.getvalue())

        extract_zip_file(self.download_location, self.extract_location)
        extracted_path = join(self.extract_location, self.file_name)
        self.assertTrue(os.path.exists(extracted_path))
        with open(extracted_path, "rb") as extracted:
            self.assertEqual(extracted.read(), self.file_content)

    def test_delete_zip_file(self):
        with open(self.download_location, "wb") as zf:
            zf.write(self.zip_file.getvalue())

        delete_zip_file(self.download_location)

        self.assertFalse(os.path.exists(self.download_location))

    @mock.patch("scripts.workers.submission_worker.logger.error")
    @mock.patch("scripts.workers.submission_worker.os.remove")
    def test_delete_zip_file_error(self, mock_remove, mock_logger):
        e = "Error description"
        mock_remove.side_effect = Exception(e)
        error_message = "{} Failed to remove zip file {}, error {}".format(
            self.WORKER_LOGS_PREFIX, self.download_location, e
        )

        delete_zip_file(self.download_location)
        mock_logger.assert_called_with(error_message)
