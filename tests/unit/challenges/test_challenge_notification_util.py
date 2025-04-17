from datetime import timedelta
from unittest.mock import MagicMock
from unittest.mock import patch as mockpatch

import mock
from allauth.account.models import EmailAddress
from challenges.challenge_notification_util import (
    construct_and_send_eks_cluster_creation_mail,
)
from challenges.models import Challenge, ChallengePhase
from django.conf import settings
from django.contrib.auth.models import User
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from moto import mock_ecs
from rest_framework.test import APIClient, APITestCase


class BaseTestClass(APITestCase):
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

        self.participant_user = User.objects.create(
            username="someparticipantuser",
            email="participantuser@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.participant_user,
            email="participantuser@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description for test challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            queue="test_queue",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
        )
        self.challenge.slug = "{}-{}".format(
            self.challenge.title.replace(" ", "-").lower(), self.challenge.pk
        )[:199]
        self.challenge.save()

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
            )

        self.client.force_authenticate(user=self.user)


@mock_ecs
class TestChallengeStartNotifier(BaseTestClass):
    def setUp(self):
        super(TestChallengeStartNotifier, self).setUp()

    @mock.patch("challenges.challenge_notification_util.send_email")
    @mock.patch("challenges.aws_utils.start_workers")
    def test_feature(self, mock_start_workers, mock_send_email):
        challenge_url = "{}/web/challenges/challenge-page/{}".format(
            settings.EVALAI_API_SERVER, self.challenge.id
        )
        host_emails = [self.user.email]
        template_id = settings.SENDGRID_SETTINGS.get("TEMPLATES").get(
            "CHALLENGE_APPROVAL_EMAIL"
        )
        template_data = {
            "CHALLENGE_NAME": self.challenge.title,
            "CHALLENGE_URL": challenge_url,
        }

        calls = []
        for email in host_emails:
            calls.append(
                mock.call(
                    sender=settings.CLOUDCV_TEAM_EMAIL,
                    recipient=email,
                    template_id=template_id,
                    template_data=template_data,
                )
            )

        mock_start_workers.return_value = {"count": 1, "failures": []}

        self.challenge.approved_by_admin = True
        self.challenge.save()

        mock_start_workers.assert_called_with([self.challenge])
        self.assertEqual(mock_send_email.call_args_list, calls)


class TestUnittestChallengeNotification(BaseTestClass):
    @mockpatch("challenges.challenge_notification_util.send_email")
    @mockpatch("challenges.challenge_notification_util.settings")
    def test_construct_and_send_eks_cluster_creation_mail(
        self, mock_settings, mock_send_email
    ):
        # Mock challenge object
        mock_challenge = MagicMock()
        mock_challenge.title = "Test Challenge"
        mock_challenge.image = None

        # Set settings.DEBUG to False
        mock_settings.DEBUG = False

        # Call the function
        mock_settings.configure_mock(
            ADMIN_EMAIL="admin@cloudcv.org",
            CLOUDCV_TEAM_EMAIL="team@cloudcv.org",
            SENDGRID_SETTINGS={
                "TEMPLATES": {"CLUSTER_CREATION_TEMPLATE": "template-id"}
            },
        )
        construct_and_send_eks_cluster_creation_mail(mock_challenge)

        # Assert send_email was called with correct arguments
        mock_send_email.assert_called_once_with(
            sender="team@cloudcv.org",
            recipient="admin@cloudcv.org",
            template_id="template-id",
            template_data={"CHALLENGE_NAME": "Test Challenge"},
        )
