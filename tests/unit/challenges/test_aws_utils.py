import boto3
import os

from moto import mock_ecs

from django.contrib.auth.models import User

from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge
from hosts.models import ChallengeHostTeam

from challenges.aws_utils import (
    create_service_by_challenge_pk,
    start_workers,
)


class BaseTestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.ecs_client = boto3.client(
            "ecs",
            region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID")
        )
        self.ecs_client.create_cluster(clusterName="cluster")

        self.ecs_client_token = "abc123"

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password"
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team",
            created_by=self.user
        )


@mock_ecs
class TestStartWorkers(BaseTestClass):
    def setUp(self):
        super(TestStartWorkers, self).setUp()

        for i in range(3):
            Challenge.objects.create(
                pk=i,
                title="Test Challenge {}".format(i),
                creator=self.challenge_host_team,
            )

        self.ecs_client.create_cluster(clusterName="cluster")

    def test_start_workers_when_all_challenges_have_no_worker(self):
        challenges = Challenge.objects.order_by("pk").all()

        expected_workers = [None, None, None]
        self.assertEqual(list(c.workers for c in challenges), expected_workers)

        expected_response = {"count": 3, "failures": []}
        response = start_workers(challenges)
        self.assertEqual(response, expected_response)

        expected_workers = [1, 1, 1]
        self.assertEqual(list(c.workers for c in challenges), expected_workers)

    def test_start_workers_when_second_challenge_already_has_a_worker(self):
        challenges = Challenge.objects.order_by("pk").all()
        second_challenge = challenges[1]

        create_service_by_challenge_pk(self.ecs_client, second_challenge, self.ecs_client_token)
        expected_workers = [None, 1, None]
        self.assertEqual(list(c.workers for c in challenges), expected_workers)

        expected_failures = [{
            "message": "Please select challenge with inactive workers only.",
            "challenge_pk": 1
        }]
        expected_response = {"count": 2, "failures": expected_failures}
        response = start_workers(challenges)
        self.assertEqual(response, expected_response)
