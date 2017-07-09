from datetime import timedelta

from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge
from hosts.models import ChallengeHost, ChallengeHostTeam
from participants.models import ParticipantTeam, Participant


class BaseAPITestClass(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            email="user@test.com",
            password='secret_password')

        EmailAddress.objects.create(
            user=self.user,
            email='user@test.com',
            primary=True,
            verified=True)

        self.user2 = User.objects.create(
            username='otheruser',
            email="otheruser@test.com",
            password='secret_password')

        EmailAddress.objects.create(
            user=self.user2,
            email='otheruser@test.com',
            primary=True,
            verified=True)

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            short_description='Short description for test challenge',
            description='Description for test challenge',
            terms_and_conditions='Terms and conditions for test challenge',
            submission_guidelines='Submission guidelines for test challenge',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN)

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team',
            created_by=self.user)

        self.participant = Participant.objects.create(
            user=self.user2,
            status=Participant.SELF,
            team=self.participant_team)

        self.client.force_authenticate(user=self.user)


class GetParticipantTeamTest(BaseAPITestClass):

    def setUp(self):
        super(GetParticipantTeamTest, self).setUp()
        self.url = reverse_lazy('analytics:get_participant_team_count',
                                kwargs={'challenge_pk': self.challenge.pk})

        self.challenge.participant_teams.add(self.participant_team)

    def test_get_participant_team_count(self):

        expected = {
            "participant_team_count": 1
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_participant_team_count_when_challenge_doe_not_exist(self):

        self.url = reverse_lazy('analytics:get_participant_team_count',
                                kwargs={'challenge_pk': self.challenge.pk + 1})

        expected = {
            "detail": "Challenge {} does not exist".format(self.challenge.pk + 1)
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetParticipantCountTest(BaseAPITestClass):

    def setUp(self):
        super(GetParticipantCountTest, self).setUp()
        self.url = reverse_lazy('analytics:get_participant_count',
                                kwargs={'challenge_pk': self.challenge.pk})

        self.challenge.participant_teams.add(self.participant_team)

    def test_get_participant_team_count(self):

        expected = {
            "participant_count": 1
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_participant_team_count_when_challenge_doe_not_exist(self):

        self.url = reverse_lazy('analytics:get_participant_count',
                                kwargs={'challenge_pk': self.challenge.pk + 1})

        expected = {
            "detail": "Challenge {} does not exist".format(self.challenge.pk + 1)
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
