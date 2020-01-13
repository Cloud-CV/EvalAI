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
        self.ecs_client = boto3.client("ecs", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"), aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"), aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),)


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


class TestScaleWorkers(BaseAdminCallsClass):
    def setUp(self):
        super(TestScaleWorkers, self).setUp()

    def test_scale_workers_when_first_challenge_has_no_worker_service(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestScaleWorkers, self).queryset(pklist)
        num_of_tasks = 3
        expected_count = 2
        expected_message = "Please start worker(s) before scaling."
        expected_failures = [
            {"message": expected_message, "challenge_pk": self.challenge.pk}
        ]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.scale_workers(queryset, num_of_tasks)
        self.assertEqual(response, expected_response)

    def test_scale_workers_when_second_challenge_scaled_to_same_num_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestScaleWorkers, self).queryset(pklist)
        num_of_tasks = self.challenge2.workers
        expected_count = 2
        expected_message = "Please scale to a different number. Challenge has {} worker(s).".format(num_of_tasks)
        expected_failures = [
            {"message": expected_message, "challenge_pk": self.challenge2.pk}
        ]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.scale_workers(queryset, num_of_tasks)
        self.assertEqual(response, expected_response)

    @mock.patch("challenges.aws_utils.service_manager")
    def test_scale_workers_when_service_manager_response_http_status_not_ok(self, mocked_service_manager):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestScaleWorkers, self).queryset(pklist)
        num_of_tasks = self.challenge2.workers + 2
        expected_count = 0
        expected_message = "error message"
        expected_failures = [
            {"message": expected_message, "challenge_pk": self.challenge.pk},
            {"message": expected_message, "challenge_pk": self.challenge2.pk},
            {"message": expected_message, "challenge_pk": self.challenge3.pk}
        ]
        expected_response = {"count": expected_count, "failures": expected_failures}
        service_manager_response = {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.EXPECTATION_FAILED},
                                    "Error": expected_message}
        mocked_service_manager.return_value = service_manager_response
        response = aws_utils.scale_workers(queryset, num_of_tasks)
        self.assertEqual(response, expected_response)
