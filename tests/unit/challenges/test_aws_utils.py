import mock
import boto3
import os

from unittest import TestCase

from moto import mock_ecs
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from http import HTTPStatus

from rest_framework.test import APITestCase, APIClient

from hosts.models import ChallengeHost, ChallengeHostTeam

import challenges.aws_utils as aws_utils
from challenges.models import Challenge, ChallengePhase


class BaseTestClass(APITestCase):
    def setUp(self):
        aws_utils.COMMON_SETTINGS_DICT["EXECUTION_ROLE_ARN"] = "arn:aws:iam::us-east-1:012345678910:role/ecsTaskExecutionRole"

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
        self.challenge2 = Challenge.objects.create(
            title="Test Challenge 2",
            creator=self.challenge_host_team,
            queue="test_queue_2",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
            )
            self.challenge_phase2 = ChallengePhase.objects.create(
                name="Challenge Phase 2",
                description="Description for Challenge Phase",
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge2,
            )

        self.client.force_authenticate(user=self.user)
        self.ecs_client = boto3.client(
            "ecs",
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        )


@mock_ecs
class BaseAdminCallsClass(BaseTestClass):
    def setUp(self):
        super(BaseAdminCallsClass, self).setUp()

        self.challenge3 = Challenge.objects.create(
            title="Test Challenge 3",
            creator=self.challenge_host_team,
            queue="test_queue_3",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        self.ecs_client.create_cluster(clusterName="cluster")
        self.client_token = "abc123"

    @classmethod
    def queryset(cls, pklist):
        queryset = Challenge.objects.filter(pk__in=pklist)
        queryset = sorted(queryset, key=lambda i: pklist.index(i.pk))
        return queryset


class TestRestartWorkers(BaseAdminCallsClass):

    def test_restart_workers_when_all_challenges_have_active_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestRestartWorkers, self).queryset(pklist)

        expected_count = 3
        expected_num_of_workers = [1, 1, 1]
        expected_failures = []
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.restart_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    def test_restart_workers_when_first_challenge_has_zero_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)
        aws_utils.scale_workers([self.challenge], 0)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestRestartWorkers, self).queryset(pklist)

        expected_count = 2
        expected_num_of_workers = [0, 1, 1]
        expected_message = "Please select challenges with active workers only."
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge.pk}]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.restart_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    @mock.patch("challenges.aws_utils.restart_workers")
    def test_restart_workers_signal_callback_evaluation_script(self, mock_restart_workers):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        self.challenge.evaluation_script = SimpleUploadedFile(
            "test_sample_file_changer.zip",
            b"Dummy content.",
            content_type="zip",
        )
        self.challenge.save()

        mock_restart_workers.assert_called_with([self.challenge])

    @mock.patch("challenges.aws_utils.restart_workers")
    def test_restart_workers_signal_callback_test_annotation(self, mock_restart_workers):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)

        self.challenge_phase.test_annotation = SimpleUploadedFile(
            "test_sample_annotation1.txt",
            b"Dummy content 1.",
            content_type="text/plain",
        )
        self.challenge_phase.save()
        self.challenge_phase2.test_annotation = SimpleUploadedFile(
            "test_sample_annotation2.txt",
            b"Dummy content 2.",
            content_type="text/plain",
        )
        self.challenge_phase2.save()

        mock_call_args = mock_restart_workers.call_args_list
        mock_call_1 = mock.call([self.challenge])
        mock_call_2 = mock.call([self.challenge2])
        self.assertEqual(mock_call_args, [mock_call_1, mock_call_2])
