from datetime import timedelta
import time

from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge
from hosts.models import ChallengeHost, ChallengeHostTeam
from participants.models import ParticipantTeam
from jobs.sender import get_or_create_sqs_queue, publish_submission_message


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.host_user = User.objects.create(
            username="host_user",
            email="host_user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.host_user,
            email="host_user@test.com",
            primary=True,
            verified=True,
        )

        self.user = User.objects.create(
            username="user", email="user@test.com", password="secret_password"
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.host_user
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description for test challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
            queue='non_worker_queue'
        )

        self.challenge_host = ChallengeHost.objects.create(
            user=self.host_user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge",
            created_by=self.host_user,
        )

        self.client.force_authenticate(user=self.host_user)


class TestSQSQueueAPI(BaseAPITestClass):

    def setUp(self):
        super(TestSQSQueueAPI, self).setUp()

        self.queue = get_or_create_sqs_queue(self.challenge.queue)
        time.sleep(5)

        self.submission_pk = 0
        self.phase_pk = 1
        self.message = {
            'challenge_pk': self.challenge.pk,
            'phase_pk': self.phase_pk,
            'submission_pk': self.submission_pk,
        }

    def test_get_submission_message_from_sqs_queue(self):
        # clear queue and wait for purging
        self.queue.purge()
        time.sleep(5)

        # submit message to queue
        self.message['submission_pk'] += 1
        publish_submission_message(self.message)

        self.url = reverse_lazy(
            "jobs:get_submission_message_from_queue",
            kwargs={
                "queue_name": self.challenge.queue,
            },
        )

        # get message from sqs queue
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['body'], self.message)

    def test_get_message_count_from_sqs_queue(self):
        # submit message to queue
        self.url = reverse_lazy(
            "jobs:get_message_count_from_queue",
            kwargs={
                "queue_name": self.challenge.queue,
            },
        )
        response = self.client.get(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.total_messages = response.data['total_messages']
        self.expected_count = 3 + self.total_messages
        for i in range(3):
            self.message['submission_pk'] += 1
            publish_submission_message(self.message)

        # get message from sqs queue
        response = self.client.get(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_messages'], self.expected_count)
