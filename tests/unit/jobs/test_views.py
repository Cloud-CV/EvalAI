import os
import shutil

from datetime import timedelta

from django.core.urlresolvers import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge, ChallengePhase
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
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   'Dummy file content', content_type='text/plain')
            )

        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.client.force_authenticate(user=self.user1)

        self.input_file = SimpleUploadedFile(
            "dummy_input.txt", "file_content", content_type="text/plain")

    def tearDown(self):
        shutil.rmtree('/tmp/evalai')

    def test_challenge_submission_when_challenge_does_not_exist(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge.delete()

        expected = {
            'error': 'Challenge does not exist'
        }

        response = self.client.post(self.url, {
                                    'status': 'submitting', 'input_file': self.input_file}, format="multipart")
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_challenge_is_not_active(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge.end_date = timezone.now() - timedelta(days=1)
        self.challenge.save()

        expected = {
            'error': 'Challenge is not active'
        }

        response = self.client.post(self.url, {
                                    'status': 'submitting', 'input_file': self.input_file}, format="multipart")
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_challenge_submission_when_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge_phase.delete()

        expected = {
            'error': 'Challenge Phase does not exist'
        }

        response = self.client.post(self.url, {
                                    'status': 'submitting', 'input_file': self.input_file}, format="multipart")
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_challenge_phase_is_not_public(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge_phase.is_public = False
        self.challenge_phase.save()

        expected = {
            'error': 'Sorry, cannot accept submissions since challenge phase is not public'
        }

        response = self.client.post(self.url, {
                                    'status': 'submitting', 'input_file': self.input_file}, format="multipart")
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_challenge_submission_when_participant_team_is_none(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.participant_team.delete()

        expected = {
            'error': 'You haven\'t participated in the challenge'
        }

        response = self.client.post(self.url, {
                                    'status': 'submitting', 'input_file': self.input_file}, format="multipart")
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_submission_when_participant_team_hasnt_participated_in_challenge(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        # Note that we haven't added the self.participant_team to Challenge
        expected = {
            'error': 'You haven\'t participated in the challenge'
        }

        response = self.client.post(self.url, {
                                    'status': 'submitting', 'input_file': self.input_file}, format="multipart")
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_submission_when_status_and_file_is_not_submitted(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()

        expected = {
            'status': ['This field is required.'],
            'input_file': ['No file was submitted.']
        }

        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_form_encoding_is_wrong(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()

        expected = {
            'input_file': ['The submitted data was not a file. Check the encoding type on the form.']
        }

        response = self.client.post(
            self.url, {'status': 'submitting', 'input_file': self.input_file})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_status_is_not_correct(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()

        expected = {
            'status': ['"XYZ" is not a valid choice.']
        }

        response = self.client.post(
            self.url, {'status': 'XYZ', 'input_file': self.input_file}, format="multipart")
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_for_successful_submission(self):
        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()

        response = self.client.post(self.url, {
                                    'status': 'submitting', 'input_file': self.input_file}, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class GetChallengeSubmittedTest(BaseAPITestClass):

    def setUp(self):
        super(GetChallengeSubmittedTest, self).setUp()
        self.url = reverse_lazy('jobs:get_challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status='submitted',
            input_file=self.challenge_phase.test_annotation
        )

    def test_challenge_submission_when_challenge_does_not_exist(self):
        self.url = reverse_lazy('jobs:get_challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge.delete()

        expected = {
            'error': 'Challenge does not exist'
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy('jobs:get_challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.challenge_phase.delete()

        expected = {
            'error': 'Challenge Phase does not exist'
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_participant_team_is_none(self):
        self.url = reverse_lazy('jobs:get_challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.participant_team.delete()

        expected = {
            'error': 'You haven\'t participated in the challenge'
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_submission_when_participant_team_hasnt_participated_in_challenge(self):
        self.url = reverse_lazy('jobs:get_challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        # Note that we haven't added the self.participant_team to Challenge
        expected = {
            'error': 'You haven\'t participated in the challenge'
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_challenge_submitted(self):
        self.url = reverse_lazy('jobs:get_challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})
        expected = [
            {
                'participant_team': self.submission.participant_team.pk,
                'challenge_phase': self.submission.challenge_phase.pk,
                'created_by': self.submission.created_by.pk,
                'status': self.submission.status,
                'input_file': self.submission.input_file
            }
        ]
        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        print "response********", response.data
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
