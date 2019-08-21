import mock

from allauth.account.models import EmailAddress
from rest_framework.test import APITestCase, APIClient
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms.models import model_to_dict
from django.utils import timezone

from challenges.models import (
    Challenge,
    ChallengePhase,
)
from participants.models import Participant, ParticipantTeam
from hosts.models import ChallengeHostTeam

import scripts.workers.remote_submission_worker as rsw


class BaseTestClass(APITestCase):

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

        self.client.force_authenticate(user=self.user)

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team for Challenge',
            created_by=self.user)

        self.participant = Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team)

        self.challenge_object = Challenge.objects.create(
            title='Test Challenge',
            description='Description for test challenge',
            terms_and_conditions='Terms and conditions for test challenge',
            submission_guidelines='Submission guidelines for test challenge',
            creator=self.challenge_host_team,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            published=True,
            approved_by_admin=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            private_annotations=True,
            evaluation_script=SimpleUploadedFile(
                'evaluation_script.py',
                b"Dummy file content",
                content_type='text/x-python'
            ),
        )

        self.challenge = model_to_dict(self.challenge_object)

        self.challenge_phase_object_1 = ChallengePhase.objects.create(
            name='Challenge Phase 1',
            description='Description for Challenge Phase',
            leaderboard_public=False,
            is_public=True,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            challenge=self.challenge_object,
            codename="phase_1"
        )
        self.challenge_phase_object_2 = ChallengePhase.objects.create(
            name='Challenge Phase 2',
            description='Description for Challenge Phase',
            leaderboard_public=False,
            is_public=True,
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=3),
            challenge=self.challenge_object,
            codename="phase_2"
        )

        self.challenge_phase_1 = model_to_dict(self.challenge_phase_object_1)
        self.challenge_phase_2 = model_to_dict(self.challenge_phase_object_2)


@mock.patch("scripts.workers.remote_submission_worker.get_challenge_phases_by_challenge_pk")
@mock.patch("scripts.workers.remote_submission_worker.get_challenge_by_queue_name")
@mock.patch("scripts.workers.remote_submission_worker.requests.get")
class PrivateAnnotationTestClass(BaseTestClass):
    def setUp(self):
        super(PrivateAnnotationTestClass, self).setUp()

    @mock.patch("scripts.workers.remote_submission_worker.PRIVATE_ANNOTATION_PATH", "/code/tests/integration/remoteworker/data/annotations_correct.yaml")
    @mock.patch("scripts.workers.remote_submission_worker.logger.info")
    def test_load_challenge_with_private_annotation_succesfully_local_path(self, mock_logger, mock_get, mock_get_challenge, mock_get_phases):
        challenge = self.challenge
        phases = [self.challenge_phase_1, self.challenge_phase_2]
        mock_get_challenge.return_value = challenge
        mock_get_phases.return_value = phases

        with self.assertRaises(Exception):
            rsw.load_challenge()

        mock_logger.assert_called_with("Annotation files were loaded successfully.")
        expected_annotation_files = {challenge['id']: {phases[0]['id']: "test_annotations_devsplit.json", phases[1]['id']: "test_annotations_split_2.json"}}
        actual_annotation_files = rsw.PHASE_ANNOTATION_FILE_NAME_MAP
        self.assertEqual(actual_annotation_files, expected_annotation_files)

    @mock.patch("scripts.workers.remote_submission_worker.PRIVATE_ANNOTATION_PATH", "https://www.path/to/file")
    def test_load_challenge_with_private_annotation_succesfully_non_local_path(self, mock_get, mock_get_challenge, mock_get_phases):
        challenge = self.challenge
        phases = [self.challenge_phase_1, self.challenge_phase_2]
        mock_get_challenge.return_value = challenge
        mock_get_phases.return_value = phases
        annotation_path = "https://www.path/to/file"
        with self.assertRaises(Exception):
            rsw.load_challenge()

        self.assertEqual(mock_get.call_args_list[1], mock.call(annotation_path))

    @mock.patch("scripts.workers.remote_submission_worker.PRIVATE_ANNOTATION_PATH", "/code/tests/integration/remoteworker/data/annotations_corrupt_wrong_phase.yaml")
    @mock.patch("scripts.workers.remote_submission_worker.logger.exception")
    def test_load_challenge_with_private_annotation_with_wrong_number_of_phases(self, mock_logger, mock_get, mock_get_challenge, mock_get_phases):
        challenge = self.challenge
        phases = [self.challenge_phase_1, self.challenge_phase_2]
        mock_get_challenge.return_value = challenge
        mock_get_phases.return_value = phases
        exception_message = "Please ensure that num of phases in the yaml file are same as in the challenge."

        with self.assertRaises(Exception):
            rsw.load_challenge()

        mock_logger.assert_called_with(exception_message)

    @mock.patch("scripts.workers.remote_submission_worker.logger.exception")
    def test_load_challenge_with_private_annotation_with_wrong_phase_directory_names(self, mock_logger, mock_get, mock_get_challenge, mock_get_phases):
        challenge = self.challenge
        phases = [self.challenge_phase_1, self.challenge_phase_2]
        mock_get_challenge.return_value = challenge
        mock_get_phases.return_value = phases
        exception_message = "PRIVATE_ANNOTATION_PATH environment variable was not passed. Please restart."

        with self.assertRaises(Exception):
            rsw.load_challenge()

        mock_logger.assert_called_with(exception_message)

    @mock.patch("scripts.workers.remote_submission_worker.PRIVATE_ANNOTATION_PATH", "/code/tests/integration/remoteworker/data/annotations_corrupt_no_test_annotation_path.yaml")
    @mock.patch("scripts.workers.remote_submission_worker.logger.exception")
    def test_load_challenge_with_private_annotation_with_missing_annotation_file_path(self, mock_logger, mock_get, mock_get_challenge, mock_get_phases):
        challenge = self.challenge
        phases = [self.challenge_phase_1, self.challenge_phase_2]
        mock_get_challenge.return_value = challenge
        mock_get_phases.return_value = phases
        exception_message = "test_annotation_file path not present for phase {}".format(phases[0]["id"])

        with self.assertRaises(Exception):
            rsw.load_challenge()

        mock_logger.assert_called_with(exception_message)

    @mock.patch("scripts.workers.remote_submission_worker.PRIVATE_ANNOTATION_PATH", "/code/tests/integration/remoteworker/data/annotations_corrupt_no_phase_id.yaml")
    @mock.patch("scripts.workers.remote_submission_worker.logger.exception")
    def test_load_challenge_with_private_annotation_with_no_phase_ids(self, mock_logger, mock_get, mock_get_challenge, mock_get_phases):
        challenge = self.challenge
        phases = [self.challenge_phase_1, self.challenge_phase_2]
        mock_get_challenge.return_value = challenge
        mock_get_phases.return_value = phases
        exception_message = "Please mention the id number of the phases."

        with self.assertRaises(Exception):
            # import pdb; pdb.set_trace()
            rsw.load_challenge()

        mock_logger.assert_called_with(exception_message)
