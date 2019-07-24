import os
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

from base.utils import RandomFileName, send_slack_notification
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
