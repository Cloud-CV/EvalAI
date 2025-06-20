import os
from unittest import TestCase
import unittest
import requests
import responses

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
import botocore
from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from base.utils import (
    RandomFileName,
    decode_data,
    encode_data,
    send_slack_notification,
    is_user_a_staff,
    get_url_from_hostname,
    send_email,
    mock_if_non_prod_aws,
    get_or_create_sqs_queue,
    get_boto3_client,
)
from challenges.models import Challenge, ChallengePhase
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam
from unittest.mock import MagicMock, patch
from scripts import seed
from settings.common import SQS_RETENTION_PERIOD


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge", created_by=self.user
        )

        self.participant = Participant.objects.create(
            user=self.user, status=Participant.SELF, team=self.participant_team
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
        )

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
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
            )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )


class TestRandomFileName(BaseAPITestClass):
    def setUp(self):
        super(TestRandomFileName, self).setUp()
        self.test_file_path = os.path.join(
            settings.BASE_DIR, "examples", "example1", "test_annotation.txt"
        )

    def test_random_file_name_without_id(self):
        obj = RandomFileName("evaluation_scripts")
        filepath = obj.__call__(self.challenge, self.test_file_path)
        expected = "evaluation_scripts/{}".format(filepath.split("/")[1])
        self.assertEqual(filepath, expected)

    def test_random_file_name_with_id(self):
        obj = RandomFileName("submission_files/submission_{id}")
        filepath = obj.__call__(self.submission, self.test_file_path)
        expected = "submission_files/submission_{}/{}".format(
            self.submission.pk, filepath.split("/")[2]
        )
        self.assertEqual(filepath, expected)


class TestSeeding(BaseAPITestClass):
    def test_if_seeding_works(self):
        seed.run(1)
        self.assertEqual(Challenge.objects.all().count(), 1)
        seed.run(2)
        self.assertEqual(Challenge.objects.all().count(), 2)


class TestSlackNotification(BaseAPITestClass):
    @responses.activate
    def test_if_slack_notification_works(self):
        message = {"text": "Testing slack functionality", "fields": []}
        responses.add(responses.POST, settings.SLACK_WEB_HOOK_URL, status=200)
        response = send_slack_notification(message=message)
        self.assertEqual(type(response), requests.models.Response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestUserIsStaff(BaseAPITestClass):
    def test_if_user_is_staff(self):
        self.user = User.objects.create(
            username="someuser1",
            email="user@test.com",
            password="secret_password",
            is_staff=True,
        )
        self.assertTrue(is_user_a_staff(self.user))

    def test_if_user_is_not_staff(self):
        self.user = User.objects.create(
            username="someuser2",
            email="user@test.com",
            password="secret_password",
            is_staff=False,
        )
        self.user.is_staff = False
        self.user.save()
        self.assertFalse(is_user_a_staff(self.user))


class TestGetUrlFromHostname(TestCase):
    def test_debug_mode(self):
        settings.DEBUG = True
        hostname = 'example.com'
        expected_url = 'http://example.com'
        self.assertEqual(get_url_from_hostname(hostname), expected_url)

    def test_test_mode(self):
        settings.TEST = True
        hostname = 'example.com'
        expected_url = 'http://example.com'
        self.assertEqual(get_url_from_hostname(hostname), expected_url)

    def test_production_mode(self):
        settings.DEBUG = False
        settings.TEST = False
        hostname = 'example.com'
        expected_url = 'https://example.com'
        self.assertEqual(get_url_from_hostname(hostname), expected_url)


class TestAwsReturnFunc(BaseAPITestClass):
    def test_mock_if_non_prod_aws_returns_original_func_when_not_debug_or_test(self):
        with patch('django.conf.settings.DEBUG', False):
            with patch('django.conf.settings.TEST', False):
                aws_mocker = MagicMock()
                func = MagicMock(return_value="mocked_value")
                decorated_func = mock_if_non_prod_aws(aws_mocker)(func)
                result = decorated_func()
                self.assertEqual(result, "mocked_value")
                aws_mocker.assert_not_called()


class TestGetOrCreateSqsQueue(BaseAPITestClass):
    @patch('base.utils.boto3.resource')
    @patch('base.utils.settings.DEBUG', True)
    @patch('base.utils.settings.TEST', False)
    def test_debug_mode_queue_name(self, mock_boto3):
        mock_sqs = MagicMock()
        mock_boto3.return_value = mock_sqs
        queue_name = "test_queue"

        get_or_create_sqs_queue(queue_name)

        mock_boto3.assert_called_with(
            "sqs",
            endpoint_url="http://sqs:9324",
            region_name="us-east-1",
            aws_secret_access_key="x",
            aws_access_key_id="x"
        )
        mock_sqs.get_queue_by_name.assert_called_with(QueueName="evalai_submission_queue")

    @patch('base.utils.boto3.resource')
    @patch('base.utils.settings.DEBUG', False)
    @patch('base.utils.settings.TEST', False)
    def test_non_debug_non_test_mode_with_challenge(self, mock_boto3):
        mock_sqs = MagicMock()
        mock_boto3.return_value = mock_sqs
        queue_name = "test_queue"
        challenge = MagicMock()
        challenge.use_host_sqs = True
        challenge.queue_aws_region = "us-west-2"
        challenge.aws_secret_access_key = "challenge_secret"
        challenge.aws_access_key_id = "challenge_key"

        get_or_create_sqs_queue(queue_name, challenge)

        mock_boto3.assert_called_with(
            "sqs",
            region_name="us-west-2",
            aws_secret_access_key="challenge_secret",
            aws_access_key_id="challenge_key"
        )
        mock_sqs.get_queue_by_name.assert_called_with(QueueName=queue_name)

    @patch('base.utils.boto3.resource')
    @patch('base.utils.settings.DEBUG', False)
    @patch('base.utils.settings.TEST', False)
    def test_non_debug_non_test_mode_without_challenge(self, mock_boto3):
        mock_sqs = MagicMock()
        mock_boto3.return_value = mock_sqs
        queue_name = "test_queue"

        with patch.dict('os.environ', {
            'AWS_DEFAULT_REGION': 'us-east-1',
            'AWS_SECRET_ACCESS_KEY': 'env_secret',
            'AWS_ACCESS_KEY_ID': 'env_key'
        }):
            get_or_create_sqs_queue(queue_name)

        mock_boto3.assert_called_with(
            "sqs",
            region_name="us-east-1",
            aws_secret_access_key="env_secret",
            aws_access_key_id="env_key"
        )
        mock_sqs.get_queue_by_name.assert_called_with(QueueName=queue_name)

    @patch('base.utils.boto3.resource')
    @patch('base.utils.logger')
    @patch('base.utils.settings')
    def test_get_or_create_sqs_queue_exception_logging(self, mock_settings, mock_logger, mock_boto3_resource):
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        mock_sqs = MagicMock()
        mock_boto3_resource.return_value = mock_sqs

        error_response = {'Error': {'Code': 'SomeOtherError', 'Message': 'An error occurred'}}
        client_error = botocore.exceptions.ClientError(error_response, 'GetQueueUrl')

        mock_sqs.get_queue_by_name.side_effect = client_error

        queue_name = "test_queue"
        get_or_create_sqs_queue(queue_name)

        mock_logger.exception.assert_called_once_with("Cannot get queue: {}".format(queue_name))

    @patch('base.utils.boto3.resource')
    @patch('base.utils.settings.DEBUG', False)
    @patch('base.utils.settings.TEST', False)
    @patch('base.utils.logger')
    def test_queue_creation_on_non_existent_queue(self, mock_logger, mock_boto3):
        mock_sqs = MagicMock()
        mock_boto3.return_value = mock_sqs
        queue_name = "test_queue"
        challenge = None
        mock_sqs.get_queue_by_name.side_effect = botocore.exceptions.ClientError(
            {"Error": {"Code": "AWS.SimpleQueueService.NonExistentQueue"}}, "GetQueueUrl"
        )

        get_or_create_sqs_queue(queue_name, challenge)

        mock_sqs.create_queue.assert_called_with(
            QueueName=queue_name,
            Attributes={"MessageRetentionPeriod": SQS_RETENTION_PERIOD}
        )
        mock_logger.exception.assert_not_called()


class TestSendEmail(unittest.TestCase):

    @patch('base.utils.sendgrid.SendGridAPIClient')
    @patch('base.utils.os.environ.get')
    @patch('base.utils.logger')
    def test_send_email_success(self, mock_logger, mock_get_env, mock_sendgrid_client):
        mock_get_env.return_value = 'fake_api_key'
        mock_sg_instance = MagicMock()
        mock_sendgrid_client.return_value = mock_sg_instance

        send_email(
            sender='sender@example.com',
            recipient='recipient@example.com',
            template_id='template_id',
            template_data={'key': 'value'}
        )

        mock_sendgrid_client.assert_called_once_with(api_key='fake_api_key')
        mock_sg_instance.client.mail.send.post.assert_called_once()
        mock_logger.warning.assert_not_called()

    @patch('base.utils.sendgrid.SendGridAPIClient')
    @patch('base.utils.os.environ.get')
    @patch('base.utils.logger')
    def test_send_email_exception(self, mock_logger, mock_get_env, mock_sendgrid_client):
        # Mock environment variable
        mock_get_env.return_value = 'fake_api_key'
        mock_sendgrid_client.side_effect = Exception('SendGrid error')

        send_email(
            sender='sender@example.com',
            recipient='recipient@example.com',
            template_id='template_id',
            template_data={'key': 'value'}
        )

        mock_logger.warning.assert_called_once_with(
            "Cannot make sendgrid call. Please check if SENDGRID_API_KEY is present."
        )


class TestGetBoto3Client(unittest.TestCase):
    @patch('base.utils.boto3.client')
    @patch('base.utils.logger')
    def test_get_boto3_client_exception(self, mock_logger, mock_boto3_client):
        mock_boto3_client.side_effect = Exception('Boto3 error')

        aws_keys = {
            "AWS_REGION": "us-west-2",
            "AWS_ACCESS_KEY_ID": "fake_access_key_id",
            "AWS_SECRET_ACCESS_KEY": "fake_secret_access_key"
        }

        get_boto3_client('s3', aws_keys)
        mock_logger.exception.assert_called_once()
        args, kwargs = mock_logger.exception.call_args
        self.assertIsInstance(args[0], Exception)
        self.assertEqual(str(args[0]), 'Boto3 error')


class TestDataEncoding(unittest.TestCase):
    def test_encode_data_empty_list(self):
        data = []
        self.assertEqual(encode_data(data), [])

    def test_decode_data_empty_list(self):
        data = []
        self.assertEqual(decode_data(data), [])