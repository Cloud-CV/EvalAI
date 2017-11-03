import os
import shutil

from datetime import timedelta

from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge, ChallengePhase
from hosts.models import ChallengeHost, ChallengeHostTeam
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
            created_by=self.user2)

        self.participant = Participant.objects.create(
            user=self.user2,
            status=Participant.SELF,
            team=self.participant_team)

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

        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        shutil.rmtree('/tmp/evalai')


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


class GetSubmissionCountForChallengeTest(BaseAPITestClass):

    def setUp(self):
        super(GetSubmissionCountForChallengeTest, self).setUp()
        self.url = reverse_lazy('analytics:get_submission_count',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'duration': 'DAILY'})

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

    def test_get_participant_team_count_when_challenge_does_not_exist(self):

        self.url = reverse_lazy('analytics:get_submission_count',
                                kwargs={'challenge_pk': self.challenge.pk + 1,
                                        'duration': 'DAILY'})

        expected = {
            "detail": "Challenge {} does not exist".format(self.challenge.pk + 1)
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_incorrect_url_pattern_submission_count(self):
        self.url = reverse_lazy('analytics:get_submission_count',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'duration': 'INCORRECT'})
        expected = {
            'error': 'Wrong URL pattern!'
        }
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.data, expected)

    def test_get_daily_submission_count(self):
        self.url = reverse_lazy('analytics:get_submission_count',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'duration': 'DAILY'})
        expected = {
            "submission_count": 1
        }
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_get_weekly_submission_count(self):
        self.url = reverse_lazy('analytics:get_submission_count',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'duration': 'WEEKLY'})
        expected = {
            "submission_count": 1
        }
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_get_monthly_submission_count(self):
        self.url = reverse_lazy('analytics:get_submission_count',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'duration': 'MONTHLY'})
        expected = {
            "submission_count": 1
        }
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_get_all_submission_count(self):
        self.url = reverse_lazy('analytics:get_submission_count',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'duration': 'ALL'})
        expected = {
            "submission_count": 1
        }
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)


class ChallengePhaseSubmissionAnalysisTest(BaseAPITestClass):

    def setUp(self):
        super(ChallengePhaseSubmissionAnalysisTest, self).setUp()
        self.url = reverse_lazy('analytics:get_challenge_phase_submission_analysis',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk})

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

    def test_get_challenge_phase_submission_analysis_when_challenge_does_not_exist(self):
        self.url = reverse_lazy('analytics:get_challenge_phase_submission_analysis',
                                kwargs={'challenge_pk': self.challenge.pk+10,
                                        'challenge_phase_pk': self.challenge_phase.pk})

        expected = {
            "detail": "Challenge {} does not exist".format(self.challenge.pk+10)
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_challenge_phase_submission_analysis_when_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy('analytics:get_challenge_phase_submission_analysis',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk+10})

        expected = {
            "detail": "ChallengePhase {} does not exist".format(self.challenge_phase.pk+10)
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_challenge_phase_submission_analysis(self):
        self.url = reverse_lazy('analytics:get_challenge_phase_submission_analysis',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk})

        expected = {
                "submission_count": 1,
                "participant_team_count": 1,
                "challenge_phase": self.challenge_phase.pk
            }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GetLastSubmissionTimeTest(BaseAPITestClass):

    def setUp(self):
        super(GetLastSubmissionTimeTest, self).setUp()
        self.url = reverse_lazy('analytics:get_last_submission_time',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'submission_by': 'challenge'})

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

    def test_get_last_submission_time_when_challenge_does_not_exists(self):
        self.url = reverse_lazy('analytics:get_last_submission_time',
                                kwargs={'challenge_pk': self.challenge.pk+10,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'submission_by': 'challenge'})
        expected = {
            'detail': 'Challenge {} does not exist'.format(self.challenge.pk+10)
            }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_last_submission_time_when_challenge_phase_does_not_exists(self):
        self.url = reverse_lazy('analytics:get_last_submission_time',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk+10,
                                        'submission_by': 'challenge'})
        expected = {
            'detail': 'ChallengePhase {} does not exist'.format(self.challenge_phase.pk+10)
            }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_last_submission_time_when_submission_by_is_user(self):
        self.url = reverse_lazy('analytics:get_last_submission_time',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'submission_by': 'user'})
        expected = {
            'last_submission_datetime': "{0}{1}".format(self.submission.created_at.isoformat(), 'Z')
                                        .replace("+00:00", "")
            }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_last_submission_time_when_url_is_incorrect(self):
        self.url = reverse_lazy('analytics:get_last_submission_time',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'submission_by': 'other'})
        expected = {
            'error': 'Page not found!'
            }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetLastSubmissionDateTimeAnalysisTest(BaseAPITestClass):

    def setUp(self):
        super(GetLastSubmissionDateTimeAnalysisTest, self).setUp()
        self.url = reverse_lazy('analytics:get_last_submission_datetime_analysis',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk})

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

    def test_get_last_submission_datetime_when_challenge_does_not_exists(self):
        self.url = reverse_lazy('analytics:get_last_submission_datetime_analysis',
                                kwargs={'challenge_pk': self.challenge.pk+10,
                                        'challenge_phase_pk': self.challenge_phase.pk})
        expected = {
            'detail': 'Challenge {} does not exist'.format(self.challenge.pk+10)
            }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_last_submission_datetime_when_challenge_phase_does_not_exists(self):
        self.url = reverse_lazy('analytics:get_last_submission_datetime_analysis',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk+10})
        expected = {
            'detail': 'ChallengePhase {} does not exist'.format(self.challenge_phase.pk+10)
            }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_last_submission_datetime_analysis(self):
        self.url = reverse_lazy('analytics:get_last_submission_datetime_analysis',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk})

        datetime = self.submission.created_at.isoformat()
        expected = {
            'last_submission_timestamp_in_challenge_phase': "{0}{1}".format(datetime, 'Z').replace("+00:00", ""),
            'last_submission_timestamp_in_challenge': "{0}{1}".format(datetime, 'Z').replace("+00:00", ""),
            'challenge_phase': self.challenge_phase.pk
            }
        response = self.client.get(self.url, {})
        datetime = response.data['last_submission_timestamp_in_challenge_phase'].isoformat()
        response_data = {
            'last_submission_timestamp_in_challenge_phase': "{0}{1}".format(datetime, 'Z').replace("+00:00", ""),
            'last_submission_timestamp_in_challenge': "{0}{1}".format(datetime, 'Z').replace("+00:00", ""),
            'challenge_phase': self.challenge_phase.pk
        }
        self.assertEqual(response_data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
