import os
import shutil

from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from challenges.models import Challenge, ChallengePhase
from hosts.models import ChallengeHostTeam


class BaseTestCase(TestCase):

    def setUp(self):

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
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            anonymous_leaderboard=False)


class ChalengeTestCase(BaseTestCase):

    def setUp(self):
        super(ChalengeTestCase, self).setUp()

        try:
            os.makedirs('/tmp/evalai')
        except OSError:
            pass

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge.image = SimpleUploadedFile('test_sample_file.jpg',
                                                      'Dummy image content', content_type='image')
            self.challenge.evaluation_script = SimpleUploadedFile('test_sample_file.zip',
                                                                  'Dummy zip content', content_type='zip')
        self.challenge.save()

    def tearDown(self):
        shutil.rmtree('/tmp/evalai')

    def test__str__(self):
        self.assertEqual(self.challenge.title, self.challenge.__str__())

    def test_is_active_when_challenge_is_active(self):
        self.assertEqual(True, self.challenge.is_active)

    def test_is_active_when_challenge_is_not_active(self):
        self.challenge.end_date = timezone.now() - timedelta(days=1)
        self.challenge.save()
        self.assertEqual(False, self.challenge.is_active)

    def test_get_evaluation_script_path(self):
        self.assertEqual(self.challenge.evaluation_script.url,
                         self.challenge.get_evaluation_script_path())

    def test_get_evaluation_script_path_when_file_is_none(self):
        self.challenge.evaluation_script = None
        self.challenge.save()
        self.assertEqual(None, self.challenge.get_evaluation_script_path(), )

    def test_get_image_url(self):
        self.assertEqual(self.challenge.image.url,
                         self.challenge.get_image_url())

    def test_get_image_url_when_image_is_none(self):
        self.challenge.image = None
        self.challenge.save()
        self.assertEqual(None, self.challenge.get_image_url())

    def test_get_start_date(self):
        self.assertEqual(self.challenge.start_date,
                         self.challenge.get_start_date())

    def test_get_end_date(self):
        self.assertEqual(self.challenge.end_date,
                         self.challenge.get_end_date())


class ChallengePhaseTestCase(BaseTestCase):

    def setUp(self):
        super(ChallengePhaseTestCase, self).setUp()
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
                                                   'Dummy file content', content_type='text/plain')
            )

    def tearDown(self):
        shutil.rmtree('/tmp/evalai')

    def test__str__(self):
        self.assertEqual(self.challenge_phase.name,
                         self.challenge_phase.__str__())

    def test_is_active(self):
        self.assertEqual(True, self.challenge_phase.is_active)

    def test_is_active_when_challenge_phase_is_not_active(self):
        self.challenge_phase.end_date = timezone.now() - timedelta(days=1)
        self.challenge_phase.save()
        self.assertEqual(False, self.challenge_phase.is_active)

    def test_get_start_date(self):
        self.assertEqual(self.challenge_phase.start_date,
                         self.challenge_phase.get_start_date())

    def test_get_end_date(self):
        self.assertEqual(self.challenge_phase.end_date,
                         self.challenge_phase.get_end_date())
