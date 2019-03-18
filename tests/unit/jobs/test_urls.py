import os
import json
import shutil

from datetime import timedelta

from django.core.urlresolvers import reverse_lazy, resolve
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge, ChallengePhase, Leaderboard, DatasetSplit, ChallengePhaseSplit
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
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

        self.user1 = User.objects.create(
            username='someuser1',
            email="user1@test.com",
            password='secret_password1')

        EmailAddress.objects.create(
            user=self.user1,
            email='user1@test.com',
            primary=True,
            verified=True)

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team for Challenge',
            created_by=self.user1)

        self.participant = Participant.objects.create(
            user=self.user1,
            status=Participant.SELF,
            team=self.participant_team)

        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            description='Description for test challenge',
            terms_and_conditions='Terms and conditions for test challenge',
            submission_guidelines='Submission guidelines for test challenge',
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False)

        try:
            os.makedirs('/tmp/evalai')
        except OSError:
            pass

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
                                                   b'Dummy file content', content_type='text/plain')
            )

        self.dataset_split = DatasetSplit.objects.create(name="Test Dataset Split", codename="test-split")

        self.leaderboard = Leaderboard.objects.create(schema=json.dumps({'hello': 'world'}))

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            dataset_split=self.dataset_split,
            challenge_phase=self.challenge_phase,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC
            )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status='submitted',
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        shutil.rmtree('/tmp/evalai')


class TestJobsUrls(BaseAPITestClass):

    def test_change_submisson_visibility_url(self):
        self.url = reverse_lazy('jobs:change_submission_data_and_visibility',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'submission_pk': self.submission.pk})
        self.assertEqual(self.url,
                         '/api/jobs/challenge/{}/challenge_phase/{}/submission/{}'.format(self.challenge.pk,
                                                                                          self.challenge_phase.pk,
                                                                                          self.submission.pk))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'jobs:change_submission_data_and_visibility')

    def test_challenge_submisson_url(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})
        self.assertEqual(self.url,
                         '/api/jobs/challenge/{}/challenge_phase/{}/submission/'.format(self.challenge.pk,
                                                                                        self.challenge_phase.pk))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'jobs:challenge_submission')

    def test_leaderboard(self):
        self.url = reverse_lazy('jobs:leaderboard',
                                kwargs={'challenge_phase_split_id': self.challenge_phase_split.pk})
        self.assertEqual(self.url,
                         '/api/jobs/challenge_phase_split/{}/leaderboard/'.format(self.challenge_phase_split.pk))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'jobs:leaderboard')

    def test_get_submission_by_pk(self):
        self.url = reverse_lazy('jobs:get_submission_by_pk',
                                kwargs={'submission_id': self.submission.pk})
        self.assertEqual(self.url,
                         '/api/jobs/submission/{}'.format(self.submission.pk))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'jobs:get_submission_by_pk')

    def test_get_remaining_submissons_for_all_phases_url(self):
        self.url = reverse_lazy('jobs:get_remaining_submissions',
                                kwargs={'challenge_pk': self.challenge.pk})
        self.assertEqual(self.url, '/api/jobs/{0}/remaining_submissions/'.format(self.challenge.pk))
        resolver = resolve(self.url)
        self.assertEqual(resolver.view_name, 'jobs:get_remaining_submissions')
