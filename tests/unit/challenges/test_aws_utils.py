import mock
import boto3
import os

from moto import mock_ecs
from datetime import timedelta

from django.utils import timezone

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from http import HTTPStatus

from rest_framework.test import APITestCase, APIClient

from hosts.models import ChallengeHost, ChallengeHostTeam

import challenges.aws_utils as aws_utils
from challenges.models import Challenge, ChallengePhase


@mock_ecs
class BaseTestClass(APITestCase):
    def setUp(self):
        aws_utils.COMMON_SETTINGS_DICT["EXECUTION_ROLE_ARN"] = "arn:aws:iam::us-east-1:012345678910:role/ecsTaskExecutionRole"

        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="myUser",
            email="myUser@test.com",
            password="password",
        )

        EmailAddress.objects.create(
            user=self.user,
            email="myUser@gmail.com",
            primary=True,
            verified=True,
        )
        self.partic_user = User.objects.create(
            username="particUser",
            email="particUser@test.com",
            password="password",
        )

        EmailAddress.objects.create(
            user=self.partic_user,
            email="particUser@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Challenge Host Team Test",
            created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description Test",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            queue="test_queue",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=1),
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
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1)
        )
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase 1",
                description="Description for Challenge Phase 1",
                start_date=timezone.now() - timedelta(days=1),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
            )
            self.challenge_phase2 = ChallengePhase.objects.create(
                name="Challenge Phase 2",
                description="Description for Challenge Phase",
                start_date=timezone.now() - timedelta(days=1),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge2,
            )

        self.client.force_authenticate(user=self.user)
        self.ecs_client = boto3.client("ecs", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"), aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"), aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),)

        self.challenge3 = Challenge.objects.create(
            title="Test Challenge 3",
            creator=self.challenge_host_team,
            queue="test_queue_3",
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1)
        )
        self.ecs_client.create_cluster(clusterName="testcluster")
        self.client_token = "qwe123"

        def queryset(cls, pk_list):
            queryset = Challenge.objects.filter(pk_in=pk_list)
            queryset = sorted(queryset, key=lambda i: pk_list.index(i.pk))
            return queryset


class TestDeleteWorkers(BaseTestClass):
    def setUp(self):
        super(TestDeleteWorkers, self).setUp()

    def test_delete_workers_when_all_three_challenges_have_active_workers(self):
        aws_utils.create_service_by_challenge_pk(
            self.ecs_client,
            self.challenge,
            self.client_token)
        aws_utils.create_service_by_challenge_pk(
            self.ecs_client,
            self.challenge2,
            self.client_token)
        aws_utils.create_service_by_challenge_pk(
            self.ecs_client,
            self.challenge3,
            self.client_token)

        pk_list = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestDeleteWorkers, self).queryset(pk_list)

        count = 3
        expected_workers = [None, None, None]
        failures = []
        expected_response = {"count": count, "failures": failures}
        response = aws_utils.delete_workers(queryset)
        assert response == expected_response
        assert list(c.workers for c in queryset) == expected_workers

    def test_delete_workers_when_challenge1_has_no_workers(self):
        aws_utils.create_service_by_challenge_pk(
            self.ecs_client,
            self.challenge2,
            self.client_token)
        aws_utils.create_service_by_challenge_pk(
            self.ecs_client,
            self.challenge2,
            self.client_token)

        pk_list = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestDeleteWorkers, self).queryset(pk_list)

        count = 2
        expected_workers = [None, None, None]
        failures = []
        expected_response = {"count": count, "failures": failures}
        response = aws_utils.delete_workers(queryset)
        assert response == expected_response
        assert list(c.workers for c in queryset) == expected_workers

    @mock.patch("challenges.aws_utils.delete_service_by_challenge_pk")
    def test_delete_workers_exception(self, mock_delete_service_by_pk):
        aws_utils.create_service_by_challenge_pk(
            self.ecs_client,
            self.challenge,
            self.client_token)
        aws_utils.create_service_by_challenge_pk(
            self.ecs_client,
            self.challenge2,
            self.client_token)
        aws_utils.create_service_by_challenge_pk(
            self.ecs_client,
            self.challenge3,
            self.client_token)

        pk_list = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestDeleteWorkers, self).queryset(pk_list)

        message = "errMessage"
        exception_message = {"Error": message, "ResponseMetaData": {"HTTPStatusCode": HTTPStatus.NOT_FOUND}}
        mock_delete_service_by_pk.return_value = exception_message

        count = 0
        failures = [
            {"message": message, "challenge_pk": self.challenge.pk},
            {"message": message, "challenge_pk": self.challenge2.pk},
            {"message": message, "challenge_pk": self.challenge3.pk}
        ]
        expected_response = {"count": count, "failures": failures}
        response = aws_utils.delete_workers(queryset)
        assert expected_response == response
        assert list(c.workers for c in queryset) == [1, 1, 1]
