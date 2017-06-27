import os

from datetime import timedelta

from django.core.urlresolvers import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge, ChallengePhase
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam


class BaseAPITestClass(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            email='user@test.com',
            password='secret_password')

        EmailAddress.objects.create(
            user=self.user,
            email='user@test.com',
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

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team for Challenge',
            created_by=self.user)

        self.participant = Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team)

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN)

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
                                                   'Dummy file content', content_type='text/plain'),
                max_submissions_per_day=100000,
                max_submissions=100000,
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


class GetSubmissionStatsTest(BaseAPITestClass):

    def setUp(self):
        super(GetSubmissionStatsTest, self).setUp()
        self.url = reverse_lazy('analytics:get_submission_stats',
                                kwargs={'challenge_phase_pk': self.challenge_phase.pk})

    def test_get_submission_stats(self):
        expected = {
            "submission_total": 1
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
