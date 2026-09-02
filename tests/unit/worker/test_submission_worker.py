import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import zipfile
from datetime import timedelta
from io import BytesIO
from os.path import join
from unittest import TestCase
from unittest.mock import MagicMock, Mock, patch

import boto3
import mock
import responses
from challenges.models import (
    Challenge,
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
)
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from jobs.utils import get_leaderboard_data_model
from moto import mock_sqs
from participants.models import ParticipantTeam
from rest_framework.test import APITestCase

from scripts.workers.submission_worker import (
    PHASE_ANNOTATION_FILE_NAME_MAP,
    SUBMISSION_DATA_DIR,
    ExecutionTimeLimitExceeded,
    GracefulKiller,
    MultiOut,
    alarm_handler,
    configure_challenge_pip_environment,
    create_dir,
    create_dir_as_python_package,
    delete_old_temp_directories,
    delete_zip_file,
    download_and_extract_file,
    download_and_extract_zip_file,
    extract_challenge_data,
    extract_submission_data,
    extract_zip_file,
    get_or_create_sqs_queue,
    load_challenge_and_return_max_submissions,
    main,
    process_add_challenge_message,
    process_submission_message,
    return_file_url_per_environment,
    run_submission,
    serialize_submission_artifact,
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

    @mock.patch("scripts.workers.submission_worker.run_submission")
    @mock.patch("scripts.workers.submission_worker.extract_submission_data")
    @mock.patch("scripts.workers.submission_worker.logger.error")
    def test_process_submission_message_skips_mismatched_phase(
        self, mock_logger_error, mock_extract, mock_run_submission
    ):
        """Reject SQS bodies whose phase/challenge disagree with the Submission.

        A forged message could otherwise evaluate another team's submission
        under the wrong annotation script and mutate its status/leaderboard.
        """
        mock_extract.return_value = self.submission
        forged_phase_pk = self.challenge_phase.pk + 999
        process_submission_message(
            {
                "challenge_pk": self.challenge.pk,
                "phase_pk": forged_phase_pk,
                "submission_pk": self.submission.pk,
            }
        )
        mock_run_submission.assert_not_called()
        self.assertTrue(mock_logger_error.called)

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

    @mock.patch("scripts.workers.submission_worker.load_challenge")
    def test_load_challenge_and_return_max_submissions_for_expired_challenge(
        self, mocked_load_challenge
    ):
        """
        Regression test: a CHALLENGE_PK-pinned q_params (pk only, no
        end_date filter) must load an already-expired, persisted
        challenge successfully instead of raising DoesNotExist.
        """
        self.challenge.end_date = timezone.now() - timedelta(days=1)
        self.challenge.save()

        response = load_challenge_and_return_max_submissions(
            {"pk": self.challenge.pk}
        )

        mocked_load_challenge.assert_called_with(self.challenge)
        self.assertEqual(
            response,
            (
                self.challenge.max_concurrent_submission_evaluation,
                self.challenge,
            ),
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
        queue_url = self.sqs_client.get_queue_url(
            QueueName="evalai_submission_queue"
        )["QueueUrl"]
        self.assertTrue(queue_url)
        self.sqs_client.delete_queue(QueueUrl=queue_url)

    @mock_sqs()
    def test_get_or_create_sqs_queue_for_existing_host_queue(self):
        get_or_create_sqs_queue("test_host_queue_2", self.challenge2)
        queue_url = self.sqs_client.get_queue_url(
            QueueName="evalai_submission_queue"
        )["QueueUrl"]
        self.assertTrue(queue_url)
        self.sqs_client.delete_queue(QueueUrl=queue_url)

    @mock_sqs()
    def test_get_or_create_sqs_queue_for_fifo_queue(self):
        get_or_create_sqs_queue("test_queue.fifo")
        queue_url = self.sqs_client.get_queue_url(
            QueueName="evalai_submission_queue.fifo"
        )["QueueUrl"]
        self.assertTrue(queue_url)
        attrs = self.sqs_client.get_queue_attributes(
            QueueUrl=queue_url, AttributeNames=["FifoQueue"]
        )["Attributes"]
        self.assertEqual(attrs["FifoQueue"], "true")
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

    def test_sigint_signal(self):
        killer = GracefulKiller()
        os.kill(os.getpid(), signal.SIGINT)
        self.assertTrue(killer.kill_now)

    def test_sigterm_signal(self):
        killer = GracefulKiller()
        os.kill(os.getpid(), signal.SIGTERM)
        self.assertTrue(killer.kill_now)

    def test_write(self):
        mock_handle1 = Mock()
        mock_handle2 = Mock()
        multi_out = MultiOut(mock_handle1, mock_handle2)
        multi_out.write("test string")
        mock_handle1.write.assert_called_with("test string")
        mock_handle2.write.assert_called_with("test string")

    def test_flush(self):
        mock_handle1 = Mock()
        mock_handle2 = Mock()

        multi_out = MultiOut(mock_handle1, mock_handle2)
        multi_out.flush()
        mock_handle1.flush.assert_called_once()
        mock_handle2.flush.assert_called_once()

    def test_alarm_handler(self):
        with self.assertRaises(ExecutionTimeLimitExceeded):
            alarm_handler(signal.SIGALRM, None)

    @mock.patch("scripts.workers.submission_worker.os.path.getctime")
    @mock.patch("scripts.workers.submission_worker.shutil.rmtree")
    def test_delete_old_temp_directories(self, mock_rmtree, mock_getctime):
        # Create temporary directories
        temp_dir = tempfile.gettempdir()
        old_dir = tempfile.mkdtemp(prefix="tmp", dir=temp_dir)
        new_dir = tempfile.mkdtemp(prefix="tmp", dir=temp_dir)

        # Mock creation times
        mock_getctime.side_effect = lambda path: {old_dir: 100, new_dir: 200}[
            path
        ]

        # Call the function
        delete_old_temp_directories(prefix="tmp")

        # Verify that the old directory is deleted and the new one is not
        mock_rmtree.assert_called_once_with(old_dir)
        self.assertNotIn(mock.call(new_dir), mock_rmtree.mock_calls)

        # Clean up
        shutil.rmtree(new_dir)


class ExtractChallengeDataWorkerTest(BaseAPITestClass):
    @patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @patch("scripts.workers.submission_worker.download_and_extract_zip_file")
    @patch("scripts.workers.submission_worker.create_dir")
    @patch("scripts.workers.submission_worker.download_and_extract_file")
    @patch("scripts.workers.submission_worker.os.path.isfile")
    @patch("scripts.workers.submission_worker.subprocess.check_output")
    @patch("scripts.workers.submission_worker.importlib.import_module")
    @patch("scripts.workers.submission_worker.importlib.invalidate_caches")
    def test_extract_challenge_data_success(
        self,
        mock_invalidate_caches,
        mock_import_module,
        mock_check_output,
        mock_isfile,
        mock_download_and_extract_file,
        mock_create_dir,
        mock_download_and_extract_zip_file,
        mock_create_dir_as_python_package,
    ):
        mock_isfile.return_value = False
        challenge = self.challenge
        phase = self.challenge_phase

        extract_challenge_data(challenge, [phase])

        mock_create_dir_as_python_package.assert_called()
        mock_download_and_extract_zip_file.assert_called()
        mock_create_dir.assert_called()
        mock_download_and_extract_file.assert_called()
        mock_invalidate_caches.assert_called()
        mock_import_module.assert_called()
        self.assertIsNone(challenge.evaluation_module_error)

    @patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @patch("scripts.workers.submission_worker.download_and_extract_zip_file")
    @patch("scripts.workers.submission_worker.create_dir")
    @patch("scripts.workers.submission_worker.download_and_extract_file")
    @patch("scripts.workers.submission_worker.os.path.isfile")
    @patch("scripts.workers.submission_worker.subprocess.check_output")
    @patch("scripts.workers.submission_worker.logger.info")
    @patch("scripts.workers.submission_worker.importlib.import_module")
    @patch("scripts.workers.submission_worker.importlib.invalidate_caches")
    def test_extract_challenge_data_no_requirements(
        self,
        mock_invalidate_caches,
        mock_import_module,
        mock_logger_info,
        mock_check_output,
        mock_isfile,
        mock_download_and_extract_file,
        mock_create_dir,
        mock_download_and_extract_zip_file,
        mock_create_dir_as_python_package,
    ):
        mock_isfile.return_value = False
        challenge = self.challenge
        phase = self.challenge_phase

        extract_challenge_data(challenge, [phase])

        mock_logger_info.assert_any_call(
            "No custom requirements for challenge {}".format(challenge.id)
        )
        mock_import_module.assert_called()
        mock_invalidate_caches.assert_called()

    @patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @patch("scripts.workers.submission_worker.download_and_extract_zip_file")
    @patch("scripts.workers.submission_worker.create_dir")
    @patch("scripts.workers.submission_worker.download_and_extract_file")
    @patch("scripts.workers.submission_worker.os.path.isfile")
    @patch("scripts.workers.submission_worker.subprocess.check_output")
    @patch("scripts.workers.submission_worker.importlib.import_module")
    @patch("scripts.workers.submission_worker.importlib.invalidate_caches")
    def test_extract_challenge_data_requirements_error(
        self,
        mock_invalidate_caches,
        mock_import_module,
        mock_check_output,
        mock_isfile,
        mock_download_and_extract_file,
        mock_create_dir,
        mock_download_and_extract_zip_file,
        mock_create_dir_as_python_package,
    ):
        # A failed dependency install must surface on the challenge as
        # evaluation_module_error and abort, rather than being swallowed and
        # continuing to a misleading import error.
        mock_isfile.return_value = True
        mock_check_output.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd="pip install",
            output=b"ERROR: Could not find a version for numpy==2.0.2",
        )
        challenge = self.challenge
        phase = self.challenge_phase

        with self.assertRaises(subprocess.CalledProcessError):
            extract_challenge_data(challenge, [phase])

        self.assertIsNotNone(challenge.evaluation_module_error)
        self.assertIn(
            "Could not find a version", challenge.evaluation_module_error
        )
        # Worker must not import a challenge whose requirements failed to install
        mock_import_module.assert_not_called()
        mock_invalidate_caches.assert_not_called()

    @patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @patch("scripts.workers.submission_worker.download_and_extract_zip_file")
    @patch("scripts.workers.submission_worker.create_dir")
    @patch("scripts.workers.submission_worker.download_and_extract_file")
    @patch("scripts.workers.submission_worker.os.path.isfile")
    @patch("scripts.workers.submission_worker.subprocess.check_output")
    @patch("scripts.workers.submission_worker.importlib.import_module")
    @patch("scripts.workers.submission_worker.importlib.invalidate_caches")
    def test_extract_challenge_data_pins_core_constraints(
        self,
        mock_invalidate_caches,
        mock_import_module,
        mock_check_output,
        mock_isfile,
        mock_download_and_extract_file,
        mock_create_dir,
        mock_download_and_extract_zip_file,
        mock_create_dir_as_python_package,
    ):
        # Both the challenge requirements.txt and the worker constraints file
        # exist, so pip must be invoked with a `-c` constraints file that pins
        # the worker's core dependency stack (prevents challenge deps from
        # upgrading numpy/scipy and breaking compiled C extensions).
        mock_isfile.return_value = True
        challenge = self.challenge
        phase = self.challenge_phase

        extract_challenge_data(challenge, [phase])

        mock_check_output.assert_called_once()
        pip_command = mock_check_output.call_args[0][0]
        self.assertIn("-r", pip_command)
        self.assertIn("-c", pip_command)
        constraints_arg = pip_command[pip_command.index("-c") + 1]
        self.assertIn("requirements", constraints_arg)
        self.assertTrue(constraints_arg.endswith(".txt"))


class RunSubmissionRemoteEvaluationTest(BaseAPITestClass):
    @patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @patch("scripts.workers.submission_worker.MultiOut")
    @patch("scripts.workers.submission_worker.stdout_redirect")
    @patch("scripts.workers.submission_worker.stderr_redirect")
    @patch(
        "scripts.workers.submission_worker.open",
        new_callable=mock.mock_open,
        read_data="log content",
    )
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    def test_run_submission_remote_evaluation_exception_with_logs(
        self,
        mock_rmtree,
        mock_open_builtin,
        mock_stderr_redirect,
        mock_stdout_redirect,
        mock_multiout,
        mock_evaluation_scripts,
    ):
        challenge_id = self.challenge.id
        challenge_phase = self.challenge_phase
        submission = self.submission
        submission.challenge_phase.challenge.remote_evaluation = True
        submission.challenge_phase.disable_logs = False
        user_annotation_file_path = "dummy/path"
        temp_run_dir = join(
            SUBMISSION_DATA_DIR.format(submission_id=submission.id), "run"
        )

        PHASE_ANNOTATION_FILE_NAME_MAP[challenge_id] = {
            challenge_phase.id: "dummy_annotation.txt"
        }
        mock_evaluation_scripts.__getitem__.return_value.evaluate.side_effect = Exception(
            "Eval error"
        )

        mock_evaluation_scripts.__getitem__.return_value.evaluate.side_effect = Exception(
            "Eval error"
        )

        with patch(
            "scripts.workers.submission_worker.ContentFile",
            side_effect=lambda x: ContentFile(x),
        ):
            run_submission(
                challenge_id,
                challenge_phase,
                submission,
                user_annotation_file_path,
            )

        submission.refresh_from_db()
        assert submission.status == Submission.FAILED
        assert submission.completed_at is not None

        assert mock_open_builtin.call_count >= 4

        mock_rmtree.assert_called_with(temp_run_dir)

    @patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @patch("scripts.workers.submission_worker.MultiOut")
    @patch("scripts.workers.submission_worker.stdout_redirect")
    @patch("scripts.workers.submission_worker.stderr_redirect")
    @patch(
        "scripts.workers.submission_worker.open",
        new_callable=mock.mock_open,
        read_data="log content",
    )
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    def test_run_submission_remote_evaluation_exception_logs_disabled(
        self,
        mock_rmtree,
        mock_open_builtin,
        mock_stderr_redirect,
        mock_stdout_redirect,
        mock_multiout,
        mock_evaluation_scripts,
    ):
        challenge_id = self.challenge.id
        challenge_phase = self.challenge_phase
        submission = self.submission
        submission.challenge_phase.challenge.remote_evaluation = True
        submission.challenge_phase.disable_logs = True
        user_annotation_file_path = "dummy/path"
        temp_run_dir = join(
            SUBMISSION_DATA_DIR.format(submission_id=submission.id), "run"
        )

        # Add this line to set up the annotation file name map
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge_id] = {
            challenge_phase.id: "dummy_annotation.txt"
        }
        mock_evaluation_scripts.__getitem__.return_value.evaluate.side_effect = Exception(
            "Eval error"
        )
        mock_evaluation_scripts.__getitem__.return_value.evaluate.side_effect = Exception(
            "Eval error"
        )

        with patch(
            "scripts.workers.submission_worker.ContentFile",
            side_effect=lambda x: ContentFile(x),
        ):
            run_submission(
                challenge_id,
                challenge_phase,
                submission,
                user_annotation_file_path,
            )

        submission.refresh_from_db()
        assert submission.status == Submission.FAILED
        assert submission.completed_at is not None

        assert mock_open_builtin.call_count < 4
        mock_rmtree.assert_called_with(temp_run_dir)


class RunSubmissionDatasetSplitExceptionTest(BaseAPITestClass):
    @patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @patch("scripts.workers.submission_worker.MultiOut")
    @patch("scripts.workers.submission_worker.stdout_redirect")
    @patch("scripts.workers.submission_worker.stderr_redirect")
    @patch(
        "scripts.workers.submission_worker.open",
        new_callable=mock.mock_open,
        read_data="log content",
    )
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    def test_run_submission_dataset_split_exception(
        self,
        mock_rmtree,
        mock_open_builtin,
        mock_stderr_redirect,
        mock_stdout_redirect,
        mock_multiout,
        mock_evaluation_scripts,
    ):
        challenge_id = self.challenge.id
        challenge_phase = self.challenge_phase
        submission = self.submission
        submission.challenge_phase.challenge.remote_evaluation = False
        user_annotation_file_path = "dummy/path"
        temp_run_dir = join(
            SUBMISSION_DATA_DIR.format(submission_id=submission.id), "run"
        )
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge_id] = {
            challenge_phase.id: "dummy_annotation.txt"
        }

        mock_evaluation_scripts.__getitem__.return_value.evaluate.return_value = {
            "result": [{"split_codename_1": {"key1": 10}}]
        }

        with patch(
            "scripts.workers.submission_worker.ChallengePhaseSplit.objects.get"
        ) as mock_cps_get:
            mock_cps = MagicMock()
            type(mock_cps).dataset_split = property(
                lambda self: (_ for _ in ()).throw(
                    Exception("dataset_split error")
                )
            )
            mock_cps_get.return_value = mock_cps

            with patch(
                "scripts.workers.submission_worker.ContentFile",
                side_effect=lambda x: ContentFile(x),
            ):
                run_submission(
                    challenge_id,
                    challenge_phase,
                    submission,
                    user_annotation_file_path,
                )

        submission.refresh_from_db()
        assert submission.status == Submission.FAILED
        assert submission.completed_at is not None

        mock_rmtree.assert_called_with(temp_run_dir)


class RunSubmissionLeaderboardDataTest(BaseAPITestClass):
    @patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @patch("scripts.workers.submission_worker.MultiOut")
    @patch("scripts.workers.submission_worker.stdout_redirect")
    @patch("scripts.workers.submission_worker.stderr_redirect")
    @patch(
        "scripts.workers.submission_worker.open",
        new_callable=mock.mock_open,
        read_data="log content",
    )
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    @patch("scripts.workers.submission_worker.LeaderboardData")
    @patch("scripts.workers.submission_worker.ChallengePhaseSplit.objects.get")
    def test_run_submission_leaderboard_data_success(
        self,
        mock_cps_get,
        mock_leaderboard_data,
        mock_rmtree,
        mock_open_builtin,
        mock_stderr_redirect,
        mock_stdout_redirect,
        mock_multiout,
        mock_evaluation_scripts,
    ):
        challenge_id = self.challenge.id
        challenge_phase = self.challenge_phase
        submission = self.submission
        submission.challenge_phase.challenge.remote_evaluation = False
        user_annotation_file_path = "dummy/path"
        temp_run_dir = join(
            SUBMISSION_DATA_DIR.format(submission_id=submission.id), "run"
        )
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge_id] = {
            challenge_phase.id: "dummy_annotation.txt"
        }

        mock_evaluation_scripts.__getitem__.return_value.evaluate.return_value = {
            "result": [{"split_codename_1": {"key1": 10}}]
        }

        mock_cps = MagicMock()
        mock_cps.leaderboard = MagicMock()
        mock_cps.dataset_split.codename = "split_codename_1"
        mock_cps_get.return_value = mock_cps

        with patch(
            "scripts.workers.submission_worker.ContentFile",
            side_effect=lambda x: ContentFile(x),
        ):
            run_submission(
                challenge_id,
                challenge_phase,
                submission,
                user_annotation_file_path,
            )

        assert mock_leaderboard_data.call_count >= 1
        submission.refresh_from_db()
        assert submission.status in [Submission.FINISHED, Submission.FAILED]
        assert submission.completed_at is not None
        mock_rmtree.assert_called_with(temp_run_dir)

    @patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @patch("scripts.workers.submission_worker.MultiOut")
    @patch("scripts.workers.submission_worker.stdout_redirect")
    @patch("scripts.workers.submission_worker.stderr_redirect")
    @patch(
        "scripts.workers.submission_worker.open",
        new_callable=mock.mock_open,
        read_data="log content",
    )
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    @patch("scripts.workers.submission_worker.LeaderboardData")
    @patch("scripts.workers.submission_worker.ChallengePhaseSplit.objects.get")
    def test_run_submission_leaderboard_data_with_error(
        self,
        mock_cps_get,
        mock_leaderboard_data,
        mock_rmtree,
        mock_open_builtin,
        mock_stderr_redirect,
        mock_stdout_redirect,
        mock_multiout,
        mock_evaluation_scripts,
    ):
        challenge_id = self.challenge.id
        challenge_phase = self.challenge_phase
        submission = self.submission
        submission.challenge_phase.challenge.remote_evaluation = False
        user_annotation_file_path = "dummy/path"
        temp_run_dir = join(
            SUBMISSION_DATA_DIR.format(submission_id=submission.id), "run"
        )
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge_id] = {
            challenge_phase.id: "dummy_annotation.txt"
        }

        mock_evaluation_scripts.__getitem__.return_value.evaluate.return_value = {
            "result": [{"split_codename_1": {"key1": 10}}],
            "error": [{"split_codename_1": {"errorkey": 1}}],
        }

        mock_cps = MagicMock()
        mock_cps.leaderboard = MagicMock()
        mock_cps.dataset_split.codename = "split_codename_1"
        mock_cps_get.return_value = mock_cps

        with patch(
            "scripts.workers.submission_worker.ContentFile",
            side_effect=lambda x: ContentFile(x),
        ):
            run_submission(
                challenge_id,
                challenge_phase,
                submission,
                user_annotation_file_path,
            )

        assert mock_leaderboard_data.call_count >= 1
        submission.refresh_from_db()
        assert submission.status in [Submission.FINISHED, Submission.FAILED]
        assert submission.completed_at is not None
        mock_rmtree.assert_called_with(temp_run_dir)


class RunSubmissionLeaderboardDataReevalTest(BaseAPITestClass):
    """Re-evaluating the same Submission must not duplicate LeaderboardData."""

    def setUp(self):
        super().setUp()
        self.dataset_split = DatasetSplit.objects.create(
            name="Split 1", codename="split_codename_1"
        )
        self.leaderboard = Leaderboard.objects.create(
            schema={"labels": ["key1"], "default_order_by": "key1"}
        )
        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            challenge_phase=self.challenge_phase,
            dataset_split=self.dataset_split,
            leaderboard=self.leaderboard,
        )
        LeaderboardData.objects.create(
            challenge_phase_split=self.challenge_phase_split,
            submission=self.submission,
            leaderboard=self.leaderboard,
            result={"key1": 1},
            is_disabled=False,
        )

    @patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @patch("scripts.workers.submission_worker.MultiOut")
    @patch("scripts.workers.submission_worker.stdout_redirect")
    @patch("scripts.workers.submission_worker.stderr_redirect")
    @patch(
        "scripts.workers.submission_worker.open",
        new_callable=mock.mock_open,
        read_data="log content",
    )
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    def test_reeval_disables_prior_leaderboard_data_before_bulk_create(
        self,
        mock_rmtree,
        mock_open_builtin,
        mock_stderr_redirect,
        mock_stdout_redirect,
        mock_multiout,
        mock_evaluation_scripts,
    ):
        challenge_id = self.challenge.id
        challenge_phase = self.challenge_phase
        submission = self.submission
        submission.challenge_phase.challenge.remote_evaluation = False
        user_annotation_file_path = "dummy/path"
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge_id] = {
            challenge_phase.id: "dummy_annotation.txt"
        }

        mock_evaluation_scripts.__getitem__.return_value.evaluate.return_value = {
            "result": [{"split_codename_1": {"key1": 99}}]
        }

        with patch(
            "scripts.workers.submission_worker.ContentFile",
            side_effect=ContentFile,
        ):
            run_submission(
                challenge_id,
                challenge_phase,
                submission,
                user_annotation_file_path,
            )

        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.FINISHED)

        active = LeaderboardData.objects.filter(
            submission=submission, is_disabled=False
        )
        self.assertEqual(active.count(), 1)
        self.assertEqual(active.first().result["key1"], 99)

        disabled = LeaderboardData.objects.filter(
            submission=submission, is_disabled=True
        )
        self.assertEqual(disabled.count(), 1)
        self.assertEqual(disabled.first().result["key1"], 1)

        # get_leaderboard_data_model must remain unambiguous after re-eval.
        leaderboard_data = get_leaderboard_data_model(
            submission.pk, self.challenge_phase_split.pk
        )
        self.assertEqual(leaderboard_data.result["key1"], 99)


class ProcessAddChallengeMessageTest(BaseAPITestClass):
    @patch("scripts.workers.submission_worker.extract_challenge_data")
    @patch("scripts.workers.submission_worker.Challenge.objects.get")
    def test_process_add_challenge_message_success(
        self, mock_challenge_get, mock_extract_challenge_data
    ):
        mock_challenge = MagicMock()
        mock_challenge.challengephase_set.all.return_value = [MagicMock()]
        mock_challenge_get.return_value = mock_challenge

        message = {"challenge_id": 123}
        process_add_challenge_message(message)

        mock_challenge_get.assert_called_with(id=123)
        mock_extract_challenge_data.assert_called_with(
            mock_challenge, mock_challenge.challengephase_set.all.return_value
        )

    @patch("scripts.workers.submission_worker.logger.exception")
    @patch("scripts.workers.submission_worker.Challenge.objects.get")
    def test_process_add_challenge_message_challenge_does_not_exist(
        self, mock_challenge_get, mock_logger_exception
    ):
        mock_challenge_get.side_effect = Challenge.DoesNotExist
        message = {"challenge_id": 999}
        try:
            process_add_challenge_message(message)
        except UnboundLocalError:
            pass

        mock_challenge_get.assert_called_with(id=999)
        mock_logger_exception.assert_called_with(
            "{} Challenge {} does not exist".format("WORKER_LOG", 999)
        )


class RunSubmissionEvaluationExceptionTest(BaseAPITestClass):
    @patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @patch("scripts.workers.submission_worker.MultiOut")
    @patch("scripts.workers.submission_worker.stdout_redirect")
    @patch("scripts.workers.submission_worker.stderr_redirect")
    @patch(
        "scripts.workers.submission_worker.open",
        new_callable=mock.mock_open,
        read_data="log content",
    )
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    def test_run_submission_evaluation_exception(
        self,
        mock_rmtree,
        mock_open_builtin,
        mock_stderr_redirect,
        mock_stdout_redirect,
        mock_multiout,
        mock_evaluation_scripts,
    ):
        challenge_id = self.challenge.id
        challenge_phase = self.challenge_phase
        submission = self.submission
        submission.challenge_phase.challenge.remote_evaluation = False
        user_annotation_file_path = "dummy/path"
        temp_run_dir = join(
            SUBMISSION_DATA_DIR.format(submission_id=submission.id), "run"
        )
        PHASE_ANNOTATION_FILE_NAME_MAP[challenge_id] = {
            challenge_phase.id: "dummy_annotation.txt"
        }

        # Simulate evaluate raising exception
        mock_evaluation_scripts.__getitem__.return_value.evaluate.side_effect = Exception(
            "Eval error"
        )

        with patch(
            "scripts.workers.submission_worker.ContentFile",
            side_effect=lambda x: ContentFile(x),
        ):
            run_submission(
                challenge_id,
                challenge_phase,
                submission,
                user_annotation_file_path,
            )

        submission.refresh_from_db()
        assert submission.status == Submission.FAILED
        assert submission.completed_at is not None
        mock_rmtree.assert_called_with(temp_run_dir)


class MainFunctionTest(BaseAPITestClass):
    @patch("scripts.workers.submission_worker.importlib.import_module")
    @patch("scripts.workers.submission_worker.importlib.invalidate_caches")
    @patch("scripts.workers.submission_worker.GracefulKiller")
    @patch("scripts.workers.submission_worker.logger.info")
    @patch("scripts.workers.submission_worker.delete_old_temp_directories")
    @patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @patch(
        "scripts.workers.submission_worker.load_challenge_and_return_max_submissions"
    )
    @patch("scripts.workers.submission_worker.get_or_create_sqs_queue")
    @patch("scripts.workers.submission_worker.process_submission_callback")
    @patch("scripts.workers.submission_worker.Submission")
    def test_main_debug_limit_concurrent(
        self,
        mock_Submission,
        mock_process_submission_callback,
        mock_get_or_create_sqs_queue,
        mock_load_challenge_and_return_max_submissions,
        mock_create_dir_as_python_package,
        mock_delete_old_temp_directories,
        mock_logger_info,
        mock_GracefulKiller,
        mock_invalidate_caches,
        mock_import_module,
    ):
        with patch.object(sys, "argv", ["worker"]), patch(
            "scripts.workers.submission_worker.settings"
        ) as mock_settings, patch(
            "scripts.workers.submission_worker.time.sleep", return_value=None
        ), patch(
            # LIMIT_CONCURRENT_SUBMISSION_PROCESSING is read from os.environ
            # once at module import time, so patching os.environ here has no
            # effect on it - the module-level name has to be patched
            # directly to actually select the eval(...) branch below.
            "scripts.workers.submission_worker.LIMIT_CONCURRENT_SUBMISSION_PROCESSING",
            "True",
        ):
            mock_settings.DEBUG = True
            mock_settings.TEST = False

            with patch.dict(
                "os.environ",
                {"CHALLENGE_PK": str(self.challenge.pk)},
            ):
                killer_instance = MagicMock()
                killer_instance.kill_now = True
                mock_GracefulKiller.return_value = killer_instance
                mock_load_challenge_and_return_max_submissions.return_value = (
                    1,
                    self.challenge,
                )
                mock_queue = MagicMock()
                mock_message = MagicMock()
                mock_message.body = (
                    '{"is_static_dataset_code_upload_submission": false}'
                )
                mock_queue.receive_messages.return_value = [mock_message]
                mock_get_or_create_sqs_queue.return_value = mock_queue
                mock_Submission.objects.filter.return_value.count.return_value = 0

                main()

                # A CHALLENGE_PK-pinned lookup must not filter by end_date,
                # so a worker can reload its challenge after it has expired
                # (regression test for the crash-on-restart bug).
                mock_load_challenge_and_return_max_submissions.assert_called_with(
                    {"pk": str(self.challenge.pk)}
                )
                assert any(
                    str(call_args[0][0]).startswith("WORKER_LOG Using ")
                    for call_args in mock_logger_info.call_args_list
                )
                mock_delete_old_temp_directories.assert_called()
                mock_create_dir_as_python_package.assert_any_call(mock.ANY)
                mock_get_or_create_sqs_queue.assert_called()
                mock_queue.receive_messages.assert_called_with(
                    WaitTimeSeconds=20
                )
                mock_process_submission_callback.assert_called_with(
                    mock_message.body
                )

    @patch("scripts.workers.submission_worker.importlib.import_module")
    @patch("scripts.workers.submission_worker.importlib.invalidate_caches")
    @patch("scripts.workers.submission_worker.GracefulKiller")
    @patch("scripts.workers.submission_worker.logger.info")
    @patch("scripts.workers.submission_worker.delete_old_temp_directories")
    @patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @patch(
        "scripts.workers.submission_worker.load_challenge_and_return_max_submissions"
    )
    @patch("scripts.workers.submission_worker.get_or_create_sqs_queue")
    @patch("scripts.workers.submission_worker.process_submission_callback")
    @patch("scripts.workers.submission_worker.Submission")
    def test_main_production_loads_expired_challenge_when_challenge_pk_set(
        self,
        mock_Submission,
        mock_process_submission_callback,
        mock_get_or_create_sqs_queue,
        mock_load_challenge_and_return_max_submissions,
        mock_create_dir_as_python_package,
        mock_delete_old_temp_directories,
        mock_logger_info,
        mock_GracefulKiller,
        mock_invalidate_caches,
        mock_import_module,
    ):
        """
        The production path (settings.DEBUG=False) must be able to load a
        CHALLENGE_PK-pinned challenge even after its end_date has passed,
        so a worker restarting after expiry doesn't crash-loop on
        Challenge.DoesNotExist while pending submissions are still queued.
        """
        with patch.object(sys, "argv", ["worker"]), patch(
            "scripts.workers.submission_worker.settings"
        ) as mock_settings, patch(
            "scripts.workers.submission_worker.time.sleep", return_value=None
        ):
            mock_settings.DEBUG = False
            mock_settings.TEST = False

            with patch.dict(
                "os.environ", {"CHALLENGE_PK": str(self.challenge.pk)}
            ):
                killer_instance = MagicMock()
                killer_instance.kill_now = True
                mock_GracefulKiller.return_value = killer_instance
                mock_load_challenge_and_return_max_submissions.return_value = (
                    1,
                    self.challenge,
                )
                mock_queue = MagicMock()
                mock_queue.receive_messages.return_value = []
                mock_get_or_create_sqs_queue.return_value = mock_queue

                main()

                mock_load_challenge_and_return_max_submissions.assert_called_with(
                    {"pk": str(self.challenge.pk)}
                )

    @patch("scripts.workers.submission_worker.importlib.import_module")
    @patch("scripts.workers.submission_worker.importlib.invalidate_caches")
    @patch("scripts.workers.submission_worker.GracefulKiller")
    @patch("scripts.workers.submission_worker.logger.info")
    @patch("scripts.workers.submission_worker.delete_old_temp_directories")
    @patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @patch(
        "scripts.workers.submission_worker.load_challenge_and_return_max_submissions"
    )
    @patch("scripts.workers.submission_worker.get_or_create_sqs_queue")
    @patch("scripts.workers.submission_worker.process_submission_callback")
    @patch("scripts.workers.submission_worker.Submission")
    def test_main_debug_no_limit_concurrent(
        self,
        mock_Submission,
        mock_process_submission_callback,
        mock_get_or_create_sqs_queue,
        mock_load_challenge_and_return_max_submissions,
        mock_create_dir_as_python_package,
        mock_delete_old_temp_directories,
        mock_logger_info,
        mock_GracefulKiller,
        mock_invalidate_caches,
        mock_import_module,
    ):
        with patch.object(sys, "argv", ["worker"]), patch(
            "scripts.workers.submission_worker.settings"
        ) as mock_settings, patch(
            "scripts.workers.submission_worker.time.sleep", return_value=None
        ), patch(
            "scripts.workers.submission_worker.Challenge"
        ) as mock_Challenge, patch(
            # See test_main_debug_limit_concurrent - os.environ has no
            # effect on this module-level name once imported.
            "scripts.workers.submission_worker.LIMIT_CONCURRENT_SUBMISSION_PROCESSING",
            "False",
        ):
            mock_settings.DEBUG = True
            mock_settings.TEST = False
            killer_instance = MagicMock()
            killer_instance.kill_now = True
            mock_GracefulKiller.return_value = killer_instance
            mock_challenge = MagicMock()
            mock_Challenge.objects.filter.return_value = [mock_challenge]
            mock_queue = MagicMock()
            mock_message = MagicMock()
            mock_message.body = (
                '{"is_static_dataset_code_upload_submission": false}'
            )
            mock_queue.receive_messages.return_value = [mock_message]
            mock_get_or_create_sqs_queue.return_value = mock_queue

            main()

            # Without a CHALLENGE_PK, this stays the multi-challenge
            # dev/test loader and must keep excluding expired
            # challenges - unlike the CHALLENGE_PK-pinned case above.
            filter_call_kwargs = mock_Challenge.objects.filter.call_args.kwargs
            self.assertIn("end_date__gte", filter_call_kwargs)
            self.assertNotIn("pk", filter_call_kwargs)
            assert any(
                str(call_args[0][0]).startswith("WORKER_LOG Using ")
                for call_args in mock_logger_info.call_args_list
            )
            mock_delete_old_temp_directories.assert_called()
            mock_create_dir_as_python_package.assert_any_call(mock.ANY)
            mock_get_or_create_sqs_queue.assert_called()
            mock_queue.receive_messages.assert_called_with(WaitTimeSeconds=20)
            mock_process_submission_callback.assert_called_with(
                mock_message.body
            )


class DeleteOldTempDirectoriesTest(BaseAPITestClass):
    @patch("scripts.workers.submission_worker.logger.info")
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    @patch("scripts.workers.submission_worker.os.path.getctime")
    def test_delete_old_temp_directories_delete_error(
        self, mock_getctime, mock_rmtree, mock_logger_info
    ):
        temp_dir = tempfile.gettempdir()
        dir1 = tempfile.mkdtemp(prefix="tmp", dir=temp_dir)
        dir2 = tempfile.mkdtemp(prefix="tmp", dir=temp_dir)

        mock_getctime.side_effect = lambda path: {dir1: 100, dir2: 200}[path]

        def rmtree_side_effect(path):
            if path == dir1:
                raise Exception("delete error")

        mock_rmtree.side_effect = rmtree_side_effect

        delete_old_temp_directories(prefix="tmp")

        assert any(
            f"Error deleting directory {dir1}: delete error"
            in str(call_args[0][0])
            for call_args in mock_logger_info.call_args_list
        )

        if os.path.exists(dir2):
            shutil.rmtree(dir2)


class ExtractSubmissionDataCancelledTest(BaseAPITestClass):
    @patch("scripts.workers.submission_worker.logger.info")
    @patch("scripts.workers.submission_worker.Submission.objects")
    def test_extract_submission_data_cancelled(
        self, mock_submission_objects, mock_logger_info
    ):
        mock_submission = MagicMock()
        mock_submission.status = Submission.CANCELLED
        queryset = MagicMock()
        queryset.get.return_value = mock_submission
        mock_submission_objects.select_related.return_value = queryset

        result = extract_submission_data(123)
        assert result is None
        mock_submission_objects.select_related.assert_called_once_with(
            "challenge_phase",
            "challenge_phase__challenge",
        )
        queryset.get.assert_called_once_with(id=123)
        mock_logger_info.assert_called_with(
            "{} Submission {} was cancelled by the user".format(
                "SUBMISSION_LOG", 123
            )
        )


class ConfigureChallengePipEnvironmentTest(APITestCase):
    def setUp(self):
        self._saved = {
            key: os.environ.get(key)
            for key in ("PIP_CONSTRAINT", "PIP_BUILD_CONSTRAINT")
        }
        os.environ.pop("PIP_CONSTRAINT", None)
        os.environ.pop("PIP_BUILD_CONSTRAINT", None)

    def tearDown(self):
        for key, value in self._saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value

    @patch(
        "scripts.workers.submission_worker.get_challenge_pip_constraints_file"
    )
    def test_sets_both_pip_constraint_env_vars(self, mock_constraints):
        mock_constraints.return_value = "/code/requirements/worker_py3_9.txt"

        returned = configure_challenge_pip_environment()

        self.assertEqual(returned, "/code/requirements/worker_py3_9.txt")
        self.assertEqual(
            os.environ["PIP_CONSTRAINT"],
            "/code/requirements/worker_py3_9.txt",
        )
        self.assertEqual(
            os.environ["PIP_BUILD_CONSTRAINT"],
            "/code/requirements/worker_py3_9.txt",
        )

    @patch(
        "scripts.workers.submission_worker.get_challenge_pip_constraints_file"
    )
    def test_no_constraints_file_leaves_env_untouched(self, mock_constraints):
        mock_constraints.return_value = None
        os.environ["PIP_CONSTRAINT"] = "/existing/constraints.txt"
        os.environ["PIP_BUILD_CONSTRAINT"] = "/existing/build-constraints.txt"

        returned = configure_challenge_pip_environment()

        self.assertIsNone(returned)
        self.assertEqual(
            os.environ["PIP_CONSTRAINT"], "/existing/constraints.txt"
        )
        self.assertEqual(
            os.environ["PIP_BUILD_CONSTRAINT"],
            "/existing/build-constraints.txt",
        )


class ExtractChallengeDataConstraintEnvTest(APITestCase):
    @patch("scripts.workers.submission_worker.importlib.import_module")
    @patch("scripts.workers.submission_worker.download_and_extract_file")
    @patch("scripts.workers.submission_worker.download_and_extract_zip_file")
    @patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @patch("scripts.workers.submission_worker.create_dir")
    @patch(
        "scripts.workers.submission_worker.os.path.isfile", return_value=False
    )
    @patch(
        "scripts.workers.submission_worker.configure_challenge_pip_environment"
    )
    def test_configures_pip_env_before_import(
        self,
        mock_configure,
        mock_isfile,
        mock_create_dir,
        mock_create_pkg,
        mock_zip,
        mock_file,
        mock_import,
    ):
        # Fail if the challenge module is imported before the pip environment
        # is configured (the install() helper runs at import time).
        mock_configure.side_effect = mock_import.assert_not_called

        challenge = MagicMock()
        challenge.id = 356
        challenge.evaluation_script.url = "http://server/eval.zip"
        phase = MagicMock()
        phase.id = 1
        phase.test_annotation.url = "http://server/ann.txt"
        phase.test_annotation.name = "ann.txt"

        extract_challenge_data(challenge, [phase])

        mock_configure.assert_called_once_with()
        mock_import.assert_called_once()


class SerializeSubmissionArtifactTest(TestCase):
    def test_none_and_empty(self):
        self.assertEqual(serialize_submission_artifact(None), "")
        self.assertEqual(serialize_submission_artifact(""), "")

    def test_string_passthrough(self):
        self.assertEqual(serialize_submission_artifact("already"), "already")

    def test_bytes_decoded(self):
        self.assertEqual(serialize_submission_artifact(b"logs"), "logs")

    def test_dict_json_serialized(self):
        serialized = serialize_submission_artifact({"foo": "bar", "n": 1})
        self.assertEqual(json.loads(serialized), {"foo": "bar", "n": 1})

    def test_list_json_serialized(self):
        serialized = serialize_submission_artifact([1, "a"])
        self.assertEqual(json.loads(serialized), [1, "a"])

    def test_non_json_native_uses_default_str(self):
        class Weird:
            def __str__(self):
                return "weird-value"

        serialized = serialize_submission_artifact({"x": Weird()})
        self.assertIn("weird-value", serialized)


class RunSubmissionArtifactPersistenceTest(BaseAPITestClass):
    def _setup_phase_map(self):
        PHASE_ANNOTATION_FILE_NAME_MAP[self.challenge.id] = {
            self.challenge_phase.id: "dummy_annotation.txt"
        }

    @patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @patch("scripts.workers.submission_worker.MultiOut")
    @patch("scripts.workers.submission_worker.stdout_redirect")
    @patch("scripts.workers.submission_worker.stderr_redirect")
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    @patch("scripts.workers.submission_worker.LeaderboardData")
    @patch("scripts.workers.submission_worker.ChallengePhaseSplit.objects.get")
    def test_dict_metadata_still_persists_stdout_and_result_files(
        self,
        mock_cps_get,
        mock_leaderboard_data,
        mock_rmtree,
        mock_stderr_redirect,
        mock_stdout_redirect,
        mock_multiout,
        mock_evaluation_scripts,
    ):
        """Dict submission_metadata used to TypeError in ContentFile and skip
        all artifact uploads after status was already marked finished."""
        self._setup_phase_map()
        submission = self.submission
        # remote_evaluation is read from submission.challenge_phase.challenge;
        # disable_logs is read from the challenge_phase arg to run_submission.
        submission.challenge_phase.challenge.remote_evaluation = False
        self.challenge_phase.disable_logs = False

        mock_evaluation_scripts.__getitem__.return_value.evaluate.return_value = {
            "result": [{"split_codename_1": {"key1": 10}}],
            "submission_result": {"score": 10},
            "submission_metadata": {"foo": "bar", "split": "dev"},
        }

        mock_cps = MagicMock()
        mock_cps.leaderboard = MagicMock()
        mock_cps.dataset_split.codename = "split_codename_1"
        mock_cps_get.return_value = mock_cps

        temp_run_dir = join(
            SUBMISSION_DATA_DIR.format(submission_id=submission.id), "run"
        )
        os.makedirs(temp_run_dir, exist_ok=True)
        with open(join(temp_run_dir, "temp_stdout.txt"), "w") as fh:
            fh.write("eval stdout")
        with open(join(temp_run_dir, "temp_stderr.txt"), "w") as fh:
            fh.write("")

        run_submission(
            self.challenge.id,
            self.challenge_phase,
            submission,
            "dummy/path",
        )

        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.FINISHED)
        self.assertTrue(bool(submission.stdout_file.name))
        self.assertTrue(bool(submission.submission_result_file.name))
        self.assertTrue(bool(submission.submission_metadata_file.name))
        self.assertIn(b"eval stdout", submission.stdout_file.read())
        self.assertEqual(
            json.loads(submission.submission_metadata_file.read().decode()),
            {"foo": "bar", "split": "dev"},
        )
        self.assertEqual(
            json.loads(submission.submission_result_file.read().decode()),
            {"score": 10},
        )

    @patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @patch("scripts.workers.submission_worker.MultiOut")
    @patch("scripts.workers.submission_worker.stdout_redirect")
    @patch("scripts.workers.submission_worker.stderr_redirect")
    @patch("scripts.workers.submission_worker.shutil.rmtree")
    @patch("scripts.workers.submission_worker.LeaderboardData")
    @patch("scripts.workers.submission_worker.ChallengePhaseSplit.objects.get")
    @patch(
        "scripts.workers.submission_worker.enqueue_submission_artifact_retention_tagging",
        side_effect=[None, RuntimeError("tagging boom")],
    )
    def test_result_artifact_failure_still_persists_stdout(
        self,
        mock_enqueue,
        mock_cps_get,
        mock_leaderboard_data,
        mock_rmtree,
        mock_stderr_redirect,
        mock_stdout_redirect,
        mock_multiout,
        mock_evaluation_scripts,
    ):
        """Failures while saving/tagging result files must not drop stdout."""
        self._setup_phase_map()
        submission = self.submission
        # remote_evaluation is read from submission.challenge_phase.challenge;
        # disable_logs is read from the challenge_phase arg to run_submission.
        submission.challenge_phase.challenge.remote_evaluation = False
        self.challenge_phase.disable_logs = False

        mock_evaluation_scripts.__getitem__.return_value.evaluate.return_value = {
            "result": [{"split_codename_1": {"key1": 10}}],
            "submission_result": {"score": 10},
            "submission_metadata": {"foo": "bar"},
        }

        mock_cps = MagicMock()
        mock_cps.leaderboard = MagicMock()
        mock_cps.dataset_split.codename = "split_codename_1"
        mock_cps_get.return_value = mock_cps

        temp_run_dir = join(
            SUBMISSION_DATA_DIR.format(submission_id=submission.id), "run"
        )
        os.makedirs(temp_run_dir, exist_ok=True)
        with open(join(temp_run_dir, "temp_stdout.txt"), "w") as fh:
            fh.write("kept stdout")
        with open(join(temp_run_dir, "temp_stderr.txt"), "w") as fh:
            fh.write("")

        run_submission(
            self.challenge.id,
            self.challenge_phase,
            submission,
            "dummy/path",
        )

        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.FINISHED)
        self.assertTrue(bool(submission.stdout_file.name))
        self.assertIn(b"kept stdout", submission.stdout_file.read())
        # Second enqueue (result/metadata tagging) must have raised after
        # result files were already saved; stdout must still be present.
        self.assertEqual(mock_enqueue.call_count, 2)
        self.assertTrue(bool(submission.submission_result_file.name))
