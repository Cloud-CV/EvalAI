import boto3
import mock
import os

from datetime import timedelta
from http import HTTPStatus
from moto import mock_ecs

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework.test import APIClient, APITestCase

from challenges.models import Challenge, ChallengePhase
from hosts.models import ChallengeHost, ChallengeHostTeam

import challenges.aws_utils as aws_utils


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
class BaseAdminCallClass(BaseTestClass):
    def setUp(self):
        aws_utils.COMMON_SETTINGS_DICT["CLUSTER"] = "cluster"
        super(BaseAdminCallClass, self).setUp()

        self.challenge3 = Challenge.objects.create(
            title="Test Challenge 3",
            creator=self.challenge_host_team,
            queue="test_queue_3",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        self.ecs_client.create_cluster(clusterName="cluster")
        self.client_token = "abc123"


class TestScaleWorkers(BaseAdminCallClass):
    def setUp(self):
        super(TestScaleWorkers, self).setUp()
        pk_list = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        self.challenges = Challenge.objects.filter(pk__in=pk_list).order_by("pk")

    def test_scale_workers_when_third_challenge_is_new_with_no_worker_service(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)

        expected_num_of_workers = [1, 1, None]
        self.assertEqual(list(c.workers for c in self.challenges), expected_num_of_workers)

        num_of_tasks = 3
        expected_num_of_workers = [num_of_tasks, num_of_tasks, None]
        expected_failures = [{
            "message": "Please start worker(s) before scaling.",
            "challenge_pk": self.challenge3.pk,
        }]
        expected_counts = 2
        expected_response = {"count": expected_counts, "failures": expected_failures}

        response = aws_utils.scale_workers(self.challenges, num_of_tasks)
        self.assertEqual(list(c.workers for c in self.challenges), expected_num_of_workers)
        self.assertEqual(response, expected_response)

    def test_scale_workers_when_second_challenge_is_scaled_to_same_number_of_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)
        self.challenge2.workers = 3
        self.challenge2.save()

        expected_num_of_workers = [1, 3, 1]
        self.assertEqual(list(c.workers for c in self.challenges), expected_num_of_workers)

        num_of_tasks = self.challenge2.workers
        expected_num_of_workers = [num_of_tasks, num_of_tasks, num_of_tasks]
        expected_message = "Please scale to a different number. Challenge has {} worker(s).".format(num_of_tasks)
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge2.pk}]
        expected_count = 2
        expected_response = {"count": expected_count, "failures": expected_failures}

        response = aws_utils.scale_workers(self.challenges, num_of_tasks)
        self.assertEqual(list(c.workers for c in self.challenges), expected_num_of_workers)
        self.assertEqual(response, expected_response)

    @mock.patch("challenges.aws_utils.update_service_by_challenge_pk")
    def test_scale_workers_when_http_connection_fails(self, mock_update_service_by_challenge_pk):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        expected_num_of_workers = [1, 1, 1]
        self.assertEqual(list(c.workers for c in self.challenges), expected_num_of_workers)

        num_of_tasks = self.challenge.workers + 3
        expected_message = "Test Error Message"
        expected_failures = [
            {"message": expected_message, "challenge_pk": self.challenge.pk},
            {"message": expected_message, "challenge_pk": self.challenge2.pk},
            {"message": expected_message, "challenge_pk": self.challenge3.pk}
        ]
        expected_count = 0
        expected_response = {"count": expected_count, "failures": expected_failures}
        mock_update_service_by_challenge_pk.return_value = {
            "Error": expected_message,
            "ResponseMetadata": {
                "HTTPStatusCode": HTTPStatus.NOT_FOUND
            }
        }

        response = aws_utils.scale_workers(self.challenges, num_of_tasks)
        self.assertEqual(list(c.workers for c in self.challenges), expected_num_of_workers)
        self.assertEqual(response, expected_response)
