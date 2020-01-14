import boto3
import challenges.aws_utils as aws_utils
import mock
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


class TestRestartWorkers(BaseAdminCallsClass):

    def setUp(self):
        super(TestRestartWorkers, self).setUp()

        self.no_active_workers = 0
        self.one_active_worker = 1

        self.example_error = "Example Error Description"
        self.response_OK = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
        }
        self.response_BAD_REQUEST = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": self.example_error
        }

    def sm_side_effect(self, client, challenge, num_of_tasks, force_new_deployment):
        self.set_challenge_workers(challenge, num_of_tasks)
        return self.response_OK

    @mock.patch("challenges.aws_utils.service_manager")
    def test_restart_workers_when_all_challenges_have_active_workers(self, mock_sm):
        mock_sm.side_effect = self.sm_side_effect

        self.set_challenge_workers(self.challenge, self.one_active_worker)
        self.set_challenge_workers(self.challenge2, self.one_active_worker)
        self.set_challenge_workers(self.challenge3, self.one_active_worker)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestRestartWorkers, self).queryset(pklist)

        expected_count = 3
        expected_num_of_workers = [self.one_active_worker, self.one_active_worker, self.one_active_worker]
        expected_failures = []
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.restart_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    @mock.patch("challenges.aws_utils.service_manager")
    def test_restart_workers_when_first_challenge_has_zero_workers(self, mock_sm):
        mock_sm.side_effect = self.sm_side_effect

        self.set_challenge_workers(self.challenge, self.no_active_workers)
        self.set_challenge_workers(self.challenge2, self.one_active_worker)
        self.set_challenge_workers(self.challenge3, self.one_active_worker)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestRestartWorkers, self).queryset(pklist)

        expected_count = 2
        expected_num_of_workers = [self.no_active_workers, self.one_active_worker, self.one_active_worker]
        expected_message = "Please select challenges with active workers only."
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge.pk}]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.restart_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    @mock.patch("challenges.aws_utils.service_manager")
    def test_restart_workers_when_service_manager_fails_for_second_challenge(self, mock_sm):
        self.set_challenge_workers(self.challenge, self.one_active_worker)
        self.set_challenge_workers(self.challenge2, self.one_active_worker)
        self.set_challenge_workers(self.challenge3, self.one_active_worker)

        mock_sm.side_effect = [self.response_OK, self.response_BAD_REQUEST, self.response_OK]

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestRestartWorkers, self).queryset(pklist)

        expected_count = 2
        expected_num_of_workers = [self.one_active_worker, self.one_active_worker, self.one_active_worker]
        expected_message = self.example_error
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge2.pk}]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.restart_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    def test_create_service_by_challenge_pk(self):
        self.ecs_client.create_cluster(clusterName=aws_utils.COMMON_SETTINGS_DICT["CLUSTER"])
        response = aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        self.assertEqual(response["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK)
        self.assertEqual(self.challenge.workers, 1)
