import os
import mock
import requests
import responses

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from base.utils import RandomFileName, send_slack_notification, encode_data, decode_data, get_url_from_hostname, get_slug, get_queue_name
from challenges.models import Challenge, ChallengePhase
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam

from scripts import seed


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


class TestEncodeData(BaseAPITestClass):
    def test_encode_data(self):
        mock_data = ['test_encode_data_on', 'test_encode_data_tw', 'test_encode_data_th']
        expected = [b'dGVzdF9lbmNvZGVfZGF0YV9vbg', b'dGVzdF9lbmNvZGVfZGF0YV90dw', b'dGVzdF9lbmNvZGVfZGF0YV90aA']
        data = encode_data(mock_data)
        self.assertEqual(data, expected)


class TestDecodeData(BaseAPITestClass):
    def test_decode_data(self):
        mock_data = ['dGVzdF9lbmNvZGVfZGF0YV9vbg', 'dGVzdF9lbmNvZGVfZGF0YV90dw', 'dGVzdF9lbmNvZGVfZGF0YV90aA']
        expected = ['test_encode_data_on', 'test_encode_data_tw', 'test_encode_data_th']
        data = decode_data(mock_data)
        self.assertEqual(data, expected)


class GetOrCreateSQSObject(BaseAPITestClass):
    @mock.patch("apps.base.utils.boto3.resource")
    def get_or_create_sqs_queue_object_when_test_is_true(self, mock_resource):
        sqs_object = get_or_create_sqs_queue_object()
        mock_resource.assertCalledWith("sqs")



class TestGetURLFromHostname(BaseAPITestClass):
    def test_get_url_from_hostname_when_debug_is_true(self):
        with self.settings(TEST=True):
            url = get_url_from_hostname('example.com')
            expected = 'http://example.com'
            self.assertEqual(url, expected)

    def test_get_url_from_hostname_when_debug_is_false(self):
        with self.settings(TEST=False, DEBUG=False):
            url = get_url_from_hostname('example.com')
            expected = 'https://example.com'
            self.assertEqual(url, expected)


class TestSeeding(BaseAPITestClass):
    def test_if_seeding_works(self):
        seed.run(1)
        self.assertEqual(Challenge.objects.all().count(), 1)
        seed.run(2)
        self.assertEqual(Challenge.objects.all().count(), 2)


class TestSlackNotification(BaseAPITestClass):

    @responses.activate
    def test_if_slack_notification_works(self):
        message = {
            "text": "Testing slack functionality",
            "fields": []
        }
        responses.add(responses.POST, settings.SLACK_WEB_HOOK_URL, status=200)
        response = send_slack_notification(
            message=message
        )
        self.assertEqual(type(response), requests.models.Response)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @mock.patch("apps.base.utils.logger.exception")
    def test_slack_notification_when_error(self, mock_logger):
        with self.assertRaises(Exception):
            message = {
                "text": "Testing slack functionality failure",
                "fields": []
            }
            responses.add(responses.POST, settings.SLACK_WEB_HOOK_URL, status=400)
            response = send_slack_notification(
                message=message
            )
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            mock_logger.assertCalledWith(
                "Exception raised while sending slack notification. \n Exception message: {}".format(
                    message["text"]
                )
            )


class GetSlug(BaseAPITestClass):
    def test_get_slug(self):
        slug = "This is A test slug"
        expected = "this-is-a-test-slug"
        self.assertEqual(get_slug(slug), expected)


class GetQueueName(BaseAPITestClass):
    @mock.patch("apps.base.utils.uuid.uuid4")
    def test_get_queue_name(self, mock_uuid):
        mock_uuid.return_value = "070afd29-f15b-4073-ab6e-174606834298"
        queue_name = "This is a Test QUEUE name"
        expected = "this-is-a-test-queue-name-070afd29-f15b-4073-ab6e-174606834298"
        self.assertEqual(get_queue_name(queue_name), expected)
