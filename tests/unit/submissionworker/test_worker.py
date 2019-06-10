import boto3
import os
import shutil
import tempfile
import zipfile

from datetime import timedelta
from moto import mock_sqs
from os.path import join

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework.test import APITestCase, APIClient

from challenges.models import (
    Challenge,
    ChallengePhase,
)
from participants.models import Participant, ParticipantTeam
from hosts.models import ChallengeHostTeam
from jobs.models import Submission

from scripts.workers.submission_worker import (
    download_and_extract_file,
    create_dir,
    create_dir_as_python_package,
    return_file_url_per_environment,
    get_or_create_sqs_queue
)


class BaseAPITestClass(APITestCase):

    def setUp(self):

        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            email="user@test.com",
            password='secret_password')

        EmailAddress.objects.create(
            user=self.user,
            email='user@test.com',
            primary=True,
            verified=True)

        self.user1 = User.objects.create(
            username='someuser1',
            email="user1@test.com",
            password='secret_password1')

        EmailAddress.objects.create(
            user=self.user1,
            email='user1@test.com',
            primary=True,
            verified=True)

        self.client.force_authenticate(user=self.user1)

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team for Challenge',
            created_by=self.user1)

        self.participant = Participant.objects.create(
            user=self.user1,
            status=Participant.SELF,
            team=self.participant_team)

        self.BASE_TEMP_DIR = tempfile.mkdtemp()

        f = open(join(self.BASE_TEMP_DIR, 'dummy_input.txt'), "x")
        f = open(join(self.BASE_TEMP_DIR, 'dummy_input.txt'), "w")
        f.write("file_content")

        self.zipped = zipfile.ZipFile(join(self.BASE_TEMP_DIR, 'test_zip.zip'), 'w')
        self.zipped.write(join(self.BASE_TEMP_DIR, 'dummy_input.txt'), 'dummy_input.txt')
        self.zipped.close()
        file = open(join(self.BASE_TEMP_DIR, 'test_zip.zip'), 'rb')
        self.z = SimpleUploadedFile(join(self.BASE_TEMP_DIR, 'test_zip.zip'), file.read(), content_type='application/zip')

        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            description='Description for test challenge',
            terms_and_conditions='Terms and conditions for test challenge',
            submission_guidelines='Submission guidelines for test challenge',
            creator=self.challenge_host_team,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            published=True,
            evaluation_script=self.z,
            approved_by_admin=True,
            enable_forum=True,
            anonymous_leaderboard=False)

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge_phase = ChallengePhase.objects.create(
                name='Challenge Phase',
                description='Description for Challenge Phase',
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   b'Dummy file content',
                                                   content_type='text/plain')
            )

        self.url = ""

        self.input_file = SimpleUploadedFile(
            "test_file.txt", b"file_content", content_type="text/plain")

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.input_file,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.sqs_client = boto3.client(
            "sqs",
            endpoint_url=os.environ.get("AWS_SQS_ENDPOINT", "http://sqs:9324"),
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        )

        self.directory = join(self.BASE_TEMP_DIR, "temp_dir")

    def tearDown(self):
        shutil.rmtree('/tmp/evalai')

    def test_download_and_extract_file(self):
        download_location = join(self.BASE_TEMP_DIR, "test_file.txt")
        self.url = return_file_url_per_environment(self.submission.input_file.url)
        download_and_extract_file(self.url, download_location)
        self.assertTrue(os.path.isfile(download_location))
        os.remove(download_location)

    def test_create_dir(self):
        create_dir(self.directory)
        self.assertTrue(os.path.isdir(self.directory))
        shutil.rmtree(self.directory)

    def test_create_dir_as_python_package(self):
        create_dir_as_python_package(self.directory)
        self.assertTrue(os.path.isfile(join(self.directory, "__init__.py")))
        shutil.rmtree(self.directory)

    def test_return_file_url_per_environment(self):
        self.url = "/test/url"
        returned_url = return_file_url_per_environment(self.url)
        self.assertEqual(returned_url, "http://testserver/test/url")

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
