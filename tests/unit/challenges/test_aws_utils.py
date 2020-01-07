import boto3
import challenges.aws_utils as aws_utils
import os

from allauth.account.models import EmailAddress
from challenges.models import Challenge, ChallengePhase
from datetime import timedelta
from django.contrib.auth.models import User
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
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

    @classmethod
    def queryset(cls, pklist):
        queryset = Challenge.objects.filter(pk__in=pklist)
        queryset = sorted(queryset, key=lambda i: pklist.index(i.pk))
        return queryset


class TestStartWorkers(BaseAdminCallClass):
    def setUp(self):
        super(TestStartWorkers, self).setUp()

    def test_start_workers_when_two_challenges_have_zero_or_none_workers(self):
        pks = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestStartWorkers, self).queryset(pks)

        expected_count = 2  # we will set the workers of challenge1 and challenge3
        expected_num_of_workers = [1, 1, 1]
        expected_message = "Please select challenge with inactive workers only."
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge2.pk}]
        expected_response = {"count": expected_count, "failures": expected_failures}

        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)
        self.challenge.workers = 0  # change challenge workers to zero to ensure test success
        self.challenge.save()
        self.challenge3.workers = 0  # change challenge workers to zero to ensure test success
        self.challenge3.save()

        aws_start_workers = aws_utils.start_workers(queryset)
        self.assertEqual(aws_start_workers, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    def test_start_workers_with_two_active_workers(self):
        Challenge.objects.filter(pk=self.challenge2.pk).update(workers=0)

        pks = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestStartWorkers, self).queryset(pks)
        expected_count = 1
        expected_message = "Please select challenge with inactive workers only."
        expected_failures = [
            {"message": expected_message, "challenge_pk": self.challenge.pk},
            {"message": expected_message, "challenge_pk": self.challenge3.pk},
        ]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.start_workers(queryset)
        self.assertEqual(response, expected_response)

    def test_start_workers_for_all_new_challenges_with_no_worker_service(self):
        pks = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestStartWorkers, self).queryset(pks)

        expected_count = 3
        expected_failures = []
        expected_response = {"count": expected_count, "failures": expected_failures}

        aws_start_workers = aws_utils.start_workers(queryset)

        self.assertEqual(aws_start_workers, expected_response)
        self.assertTrue(all(i.workers == 1 for i in queryset))
        