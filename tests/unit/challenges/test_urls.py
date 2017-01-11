from challenges.models import Challenge
from django.contrib.auth.models import User
from hosts.models import ChallengeHostTeam
from participants.models import ParticipantTeam

from django.urls import reverse_lazy

from rest_framework.test import APITestCase, APIClient


class BaseAPITestClass(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            email="user@test.com",
            password='secret_password')

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            description='Description for test challenge',
            terms_and_conditions='Terms and conditions for test challenge',
            submission_guidelines='Submission guidelines for test challenge',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False)

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team for Challenge',
            created_by=self.user)

        self.client.force_authenticate(user=self.user)


class TestChallengeUrls(BaseAPITestClass):

    def test_challenges_urls(self):
        url = reverse_lazy('challenges:get_challenge_list',
                           kwargs={'challenge_host_team_pk': self.challenge_host_team.pk})
        self.assertEqual(url, '/api/challenges/challenge_host_team/' + str(self.challenge_host_team.pk) + '/challenge')

        url = reverse_lazy('challenges:get_challenge_detail',
                           kwargs={'challenge_host_team_pk': self.challenge_host_team.pk, 'pk': self.challenge.pk})
        self.assertEqual(url, '/api/challenges/challenge_host_team/' +
                         str(self.challenge_host_team.pk) + '/challenge/' + str(self.challenge.pk))

        url = reverse_lazy('challenges:add_participant_team_to_challenge',
                           kwargs={'challenge_pk': self.challenge.pk, 'participant_team_pk': self.participant_team.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/participant_team/' +
                         str(self.participant_team.pk))

        url = reverse_lazy('challenges:disable_challenge', kwargs={'pk': self.challenge.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/disable')

        url = reverse_lazy('challenges:get_challenge_phase_list', kwargs={'challenge_pk': self.challenge.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/challenge_phase')

        url = reverse_lazy('challenges:get_challenge_phase_detail',
                           kwargs={'challenge_pk': self.challenge.pk, 'pk': self.challenge.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/challenge_phase/' +
                         str(self.challenge.pk))

        url = reverse_lazy('challenges:get_challenge_by_pk', kwargs={'pk': self.challenge.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/')

        url = reverse_lazy('challenges:get_all_challenges', kwargs={'challenge_time': "PAST"})
        self.assertEqual(url, '/api/challenges/PAST')
