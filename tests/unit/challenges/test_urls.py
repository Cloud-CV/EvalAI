import json

from datetime import timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse_lazy, resolve
from django.utils import timezone

from rest_framework.test import APITestCase, APIClient

from challenges.models import (Challenge,
                               ChallengePhase,
                               ChallengePhaseSplit,
                               DatasetSplit,
                               Leaderboard,)
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
                                                   b'Dummy file content', content_type='text/plain'),
                max_submissions_per_day=100000,
                max_submissions=100000,
            )

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team for Challenge',
            created_by=self.user)

        self.dataset_split = DatasetSplit.objects.create(name="Name of the dataset split",
                                                         codename="codename of dataset split")

        self.leaderboard = Leaderboard.objects.create(schema=json.dumps({
                                                      "labels": ["yes/no", "number", "others", "overall"],
                                                      "default_order_by": "overall"}))

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            dataset_split=self.dataset_split,
            challenge_phase=self.challenge_phase,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC
            )

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

        self.url = reverse_lazy('challenges:download_all_submissions',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'file_type': self.file_type})
        self.assertEqual(self.url,
                         '/api/challenges/{}/phase/{}/download_all_submissions/{}/'
                         .format(self.challenge.pk, self.challenge_phase.pk, self.file_type))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'challenges:download_all_submissions')

        self.url = reverse_lazy('challenges:create_leaderboard')
        self.assertEqual(self.url,
                         '/api/challenges/challenge/create/leaderboard/step_2/')
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'challenges:create_leaderboard')

        self.url = reverse_lazy('challenges:get_or_update_leaderboard',
                                kwargs={'leaderboard_pk': self.leaderboard.pk})
        self.assertEqual(self.url,
                         '/api/challenges/challenge/create/leaderboard/{}/'
                         .format(self.leaderboard.pk))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'challenges:get_or_update_leaderboard')

        self.url = reverse_lazy('challenges:create_dataset_split')
        self.assertEqual(self.url,
                         '/api/challenges/challenge/create/dataset_split/step_4/')
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'challenges:create_dataset_split')

        self.url = reverse_lazy('challenges:get_or_update_dataset_split',
                                kwargs={'dataset_split_pk': self.dataset_split.pk})
        self.assertEqual(self.url,
                         '/api/challenges/challenge/create/dataset_split/{}/'
                         .format(self.dataset_split.pk))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'challenges:get_or_update_dataset_split')

        self.url = reverse_lazy('challenges:create_challenge_phase_split')
        self.assertEqual(self.url,
                         '/api/challenges/challenge/create/challenge_phase_split/step_5/')
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'challenges:create_challenge_phase_split')

        self.url = reverse_lazy('challenges:get_or_update_challenge_phase_split',
                                kwargs={'challenge_phase_split_pk': self.challenge_phase_split.pk})
        self.assertEqual(self.url,
                         '/api/challenges/challenge/create/challenge_phase_split/{}/'
                         .format(self.challenge_phase_split.pk))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'challenges:get_or_update_challenge_phase_split')

        self.url = reverse_lazy('challenges:star_challenge',
                                kwargs={'challenge_pk': self.challenge.pk})
        self.assertEqual(self.url,
                         '/api/challenges/{}/'
                         .format(self.challenge.pk))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'challenges:star_challenge')
