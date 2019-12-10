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
from scripts.workers.submission_worker import (
    create_dir,
    create_dir_as_python_package,
    extract_challenge_data,
    load_challenge_and_return_max_submissions,
    return_file_url_per_environment,
    get_or_create_sqs_queue
)


class BaseAPITestClass(APITestCase):
    def setUp(self):

        self.BASE_TEMP_DIR = tempfile.mkdtemp()

        self.CHALLENGE_DATA_DIR = join(
            self.BASE_TEMP_DIR,
            "compute/challenge_data/challenge_{challenge_id}",
        )
        self.PHASE_DATA_BASE_DIR = join(
            self.CHALLENGE_DATA_DIR, "phase_data"
        )
        self.PHASE_DATA_DIR = join(
            self.PHASE_DATA_BASE_DIR, "phase_{phase_id}"
        )
        self.CHALLENGE_IMPORT_STRING = "challenge_data.challenge_{challenge_id}"

        self.temp_directory = join(self.BASE_TEMP_DIR, "temp_dir")

        self.testserver = "http://testserver"
        self.url = "/test/url"

        self.input_file = open(
            join(self.BASE_TEMP_DIR, 'dummy_input.txt'), "w+"
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

    def get_phase_annotation_file_path(
            self,
            challenge_id,
            phase_id,
            annotation_file):
        """Helper Method: Takes `challenge_id`, `phase_id` and `annotation_file`
        as input and returns corresponding path to annotation file"""

        annotation_file_name = os.path.basename(annotation_file.name)
        return join(self.PHASE_DATA_DIR, "{annotation_file}").format(
            challenge_id=challenge_id,
            phase_id=phase_id,
            annotation_file=annotation_file_name,
        )

    def get_url_for_test_environment(self, url):
        """Helper Method: Takes in `url` and returns URL for test environment"""
        return "{0}{1}".format(self.testserver, url)

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
        self.assertEqual(returned_url, self.get_url_for_test_environment(self.url))

    @mock.patch("scripts.workers.submission_worker.importlib.import_module",
                return_value="Test Value for Challenge Module")
    @mock.patch("scripts.workers.submission_worker.download_and_extract_file")
    @mock.patch("scripts.workers.submission_worker.download_and_extract_zip_file")
    def test_extract_challenge_data(self,
                                    mock_download_and_extract_zip_file,
                                    mock_download_and_extract_file,
                                    mock_import_module):

        # Setting up expected data first, so all assertions can be made inside
        # the with block in their original order.
        challenge_data_directory = self.CHALLENGE_DATA_DIR.format(
            challenge_id=self.challenge.id
        )
        evaluation_script_url = self.get_url_for_test_environment(
            self.challenge.evaluation_script.url
        )
        challenge_zip_file = join(
            challenge_data_directory, "challenge_{}.zip".format(self.challenge.id)
        )
        annotation_file_name = os.path.basename(self.challenge_phase.test_annotation.name)
        annotation_file_url = self.get_url_for_test_environment(
            self.challenge_phase.test_annotation.url
        )
        annotation_file_path = self.get_phase_annotation_file_path(
            challenge_id=self.challenge.id,
            phase_id=self.challenge_phase.id,
            annotation_file=self.challenge_phase.test_annotation,
        )
        challenge_import_string = self.CHALLENGE_IMPORT_STRING.format(challenge_id=self.challenge.id)
        expected_phase_annotation_file_name_map = {
            self.challenge.id: {self.challenge_phase.id: annotation_file_name}
        }
        expected_evaluation_scripts = {self.challenge.id: "Test Value for Challenge Module"}

        dir_patcher = mock.patch.multiple(
            "scripts.workers.submission_worker",
            CHALLENGE_DATA_DIR=self.CHALLENGE_DATA_DIR,
            PHASE_DATA_BASE_DIR=self.PHASE_DATA_BASE_DIR,
            PHASE_DATA_DIR=self.PHASE_DATA_DIR,
            PHASE_ANNOTATION_FILE_PATH=join(
                self.PHASE_DATA_DIR, "{annotation_file}"
            )
        )
        patcher_phase_annotation_file_name_map = mock.patch(
            "scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_NAME_MAP",
            {},
        )
        patcher_evaluation_scripts = mock.patch(
            "scripts.workers.submission_worker.EVALUATION_SCRIPTS",
            {},
        )

        with dir_patcher,\
                patcher_phase_annotation_file_name_map as mock_annotation_file_map,\
                patcher_evaluation_scripts as mock_evaluation_scripts:

            phases = [self.challenge_phase]
            extract_challenge_data(self.challenge, phases)

            # Order as executed in original function
            mock_download_and_extract_zip_file.assert_called_with(
                evaluation_script_url, challenge_zip_file, challenge_data_directory
            )
            self.assertEqual(
                mock_annotation_file_map,
                expected_phase_annotation_file_name_map,
            )
            mock_download_and_extract_file.assert_called_with(
                annotation_file_url,
                annotation_file_path,
            )
            mock_import_module.assert_called_with(challenge_import_string)
            self.assertEqual(mock_evaluation_scripts, expected_evaluation_scripts)

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
