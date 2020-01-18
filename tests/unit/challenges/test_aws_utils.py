import boto3
import challenges.aws_utils as aws_utils
import os

from allauth.account.models import EmailAddress
from challenges.models import Challenge
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from http import HTTPStatus
from moto import mock_ecs
from rest_framework.test import APITestCase, APIClient


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

        self.client.force_authenticate(user=self.user)
        self.ecs_client = boto3.client(
            "ecs",
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        )

    def set_challenge_workers(self, challenge, num_workers):
        challenge.workers = num_workers
        challenge.save()


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
        self.client_token = aws_utils.client_token_generator()

    @classmethod
    def queryset(cls, pklist):
        queryset = Challenge.objects.filter(pk__in=pklist)
        queryset = sorted(queryset, key=lambda i: pklist.index(i.pk))
        return queryset


class TestCreateServiceByChallengePK(BaseAdminCallsClass):

    def test_create_service_by_challenge_pk(self):
        self.ecs_client.create_cluster(clusterName=aws_utils.COMMON_SETTINGS_DICT["CLUSTER"])
        response = aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK)
        self.assertEqual(self.challenge.workers, 1)


class TestRegisterTaskDefByChallengePK(BaseAdminCallsClass):

    def test_register_task_def_by_challenge_pk(self):
        self.ecs_client.create_cluster(clusterName=aws_utils.COMMON_SETTINGS_DICT["CLUSTER"])
        response = aws_utils.create_task_def_by_challenge_pk(
            self.ecs_client, self.challenge.queue, self.challenge)
        self.assertEqual(
            response["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK)
        self.assertEqual(
            self.challenge.task_def_arn, response["taskDefinition"]["taskDefinitionArn"])
