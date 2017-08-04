from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse_lazy, resolve
from django.utils import timezone

from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge, ChallengePhase
from hosts.models import ChallengeHostTeam
from participants.models import ParticipantTeam


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

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge_phase = ChallengePhase.objects.create(
                name='Challenge Phase',
                description='Description for Challenge Phase',
                leaderboard_public=False,
                is_public=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   'Dummy file content', content_type='text/plain'),
                max_submissions_per_day=100000,
                max_submissions=100000,
            )

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team for Challenge',
            created_by=self.user)

        self.file_type = 'csv'

        self.client.force_authenticate(user=self.user)


class TestChallengeUrls(BaseAPITestClass):

    def test_challenges_urls(self):
        url = reverse_lazy('challenges:get_challenge_list',
                           kwargs={'challenge_host_team_pk': self.challenge_host_team.pk})
        self.assertEqual(url, '/api/challenges/challenge_host_team/' + str(self.challenge_host_team.pk) + '/challenge')

        url = reverse_lazy('challenges:get_challenge_detail',
                           kwargs={'challenge_host_team_pk': self.challenge_host_team.pk,
                                   'challenge_pk': self.challenge.pk})
        self.assertEqual(url, '/api/challenges/challenge_host_team/' +
                         str(self.challenge_host_team.pk) + '/challenge/' + str(self.challenge.pk))

        url = reverse_lazy('challenges:add_participant_team_to_challenge',
                           kwargs={'challenge_pk': self.challenge.pk, 'participant_team_pk': self.participant_team.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/participant_team/' +
                         str(self.participant_team.pk))

        url = reverse_lazy('challenges:disable_challenge', kwargs={'challenge_pk': self.challenge.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/disable')

        url = reverse_lazy('challenges:get_challenge_phase_list', kwargs={'challenge_pk': self.challenge.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/challenge_phase')

        url = reverse_lazy('challenges:get_challenge_phase_detail',
                           kwargs={'challenge_pk': self.challenge.pk, 'pk': self.challenge_phase.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/challenge_phase/' +
                         str(self.challenge_phase.pk))

        url = reverse_lazy('challenges:get_challenge_by_pk', kwargs={'pk': self.challenge.pk})
        self.assertEqual(url, '/api/challenges/challenge/' + str(self.challenge.pk) + '/')

        url = reverse_lazy('challenges:get_all_challenges', kwargs={'challenge_time': "PAST"})
        self.assertEqual(url, '/api/challenges/challenge/PAST')

        self.url = reverse_lazy('challenges:download_all_submissions_file',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'file_type': self.file_type})
        self.assertEqual(self.url, '/api/challenges/{}/download_all_submissions_file/{}/'.format(self.challenge.pk,
                                                                                                 self.file_type))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'challenges:download_all_submissions_file')
