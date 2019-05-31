import mock
import os
import shutil
import time
import json

from allauth.account.models import EmailAddress

from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.utils import timezone

from rest_framework.test import APITestCase, APIClient

from challenges.models import (
    Challenge,
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
)
from participants.models import Participant, ParticipantTeam
from hosts.models import ChallengeHostTeam
from jobs.models import Submission

import scripts.workers.submission_worker as submission_worker


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
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            published=True,
            evaluation_script=self.z,
            approved_by_admin=True,
            enable_forum=True,
            anonymous_leaderboard=False)

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge_phase = ChallengePhase.objects.create(
                name='Challenge Phase',
                description='Description for Challenge Phase',
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   b'Dummy file content',
                                                   content_type='text/plain')
            )

        self.url = reverse_lazy('jobs:challenge_submission',
                                kwargs={'challenge_id': self.challenge.pk,
                                        'challenge_phase_id': self.challenge_phase.pk})

        self.client.force_authenticate(user=self.user1)

        self.input_file = SimpleUploadedFile(
            "test_file.txt", b"file_content", content_type="text/plain")

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.input_file,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

    def tearDown(self):
        try:
            shutil.rmtree('/tmp/evalai')
        except OSError:
            pass


class NormalTestClass(BaseAPITestClass):

    def setUp(self):
        super(NormalTestClass, self).setUp()
        submission_worker.SUBMISSION_DATA_BASE_DIR = "mocked/dir"

    @mock.patch("scripts.workers.submission_worker.process_submission_message")
    def test_process_submission_callback(self, mock_psm):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": self.challenge_phase.pk,
            "submission_pk": self.submission.id
        }
        body = json.dumps(message)

        submission_worker.process_submission_callback(body)
        mock_psm.assert_called_with(message)

    @mock.patch("scripts.workers.submission_worker.logger.exception")
    @mock.patch("scripts.workers.submission_worker.process_submission_message")
    def test_process_submission_callback_unsuccesful(self, mock_psm, mock_logger):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": self.challenge_phase.pk,
            "submission_pk": self.submission.id
        }
        body = json.dumps(message)

        mock_psm.side_effect = Exception("test error")

        submission_worker.process_submission_callback(body)

        mock_logger.assert_called_with("Exception while receiving message from submission queue with error test error")

    @mock.patch("scripts.workers.submission_worker.SUBMISSION_DATA_DIR", "mocked/dir/submisison_{submission_id}")
    @mock.patch("scripts.workers.submission_worker.os.path.basename", return_value="test_file.txt")
    @mock.patch("scripts.workers.submission_worker.run_submission")
    def test_process_submission_message_succesfully(self, mock_rs, mock_basename):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": self.challenge_phase.pk,
            "submission_pk": self.submission.id
        }
        user_annotation_file_path = "mocked/dir/submission_{}/test_file.txt".format(self.submission.id)

        with mock.patch("scripts.workers.submission_worker.extract_submission_data") as mock_esd:
            submission_worker.process_submission_message(message)
            mock_esd.assert_called_with(self.submission.id)

        submission_worker.process_submission_message(message)

        mock_rs.assert_called_with(self.challenge.pk, self.challenge_phase, self.submission, user_annotation_file_path)

    @mock.patch("scripts.workers.submission_worker.extract_submission_data")
    def test_process_submission_message_when_submission_does_not_exist(self, mock_esd):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": self.challenge_phase.pk,
            "submission_pk": self.submission.id
        }
        mock_esd.return_value = None

        submission_worker.process_submission_message(message)

        self.assertEqual(submission_worker.process_submission_message(message), None)

    @mock.patch("scripts.workers.submission_worker.logger.exception")
    def test_process_submission_message_when_challenge_phase_does_not_exist(self, mock_logger):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": 1000,
            "submission_pk": self.submission.id
        }
        phase_id = 1000

        submission_worker.process_submission_message(message)

        mock_logger.assert_called_with("Challenge Phase {} does not exist".format(phase_id))

    @mock.patch("scripts.workers.submission_worker.logger.critical")
    def test_extract_submission_data_when_submission_does_not_exist(self, mock_logger):
        value = submission_worker.extract_submission_data(-1)
        submission_id = -1
        mock_logger.assert_called_with("Submission {} does not exist".format(submission_id))
        self.assertEqual(value, None)

    @mock.patch("scripts.workers.submission_worker.SUBMISSION_DATA_DIR", "mocked/dir/submisison_{submission_id}")
    @mock.patch("scripts.workers.submission_worker.download_and_extract_file")
    @mock.patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @mock.patch("scripts.workers.submission_worker.return_file_url_per_environment")
    def test_extract_submission_data_succesfully(self, mock_url, mock_createdir, mock_down_ext):
        submission_worker.extract_submission_data(self.submission.id)

        submission_input_file = self.submission.input_file.url
        mock_url.assert_called_with(submission_input_file)

        submission_data_directory = "mocked/dir/submission_{}".format(self.submission.id)
        mock_createdir.assert_called_with(submission_data_directory)

        submission_input_file_url = "http://testserver{}".format(self.submission.input_file.url)
        submission_input_file_path = "mocked/dir/submission_{}/test_file.txt".format(self.submission.id)
        mock_down_ext.assert_called_with(submission_input_file_url, submission_input_file_path)

    @mock.patch("scripts.workers.submission_worker.CHALLENGE_DATA_BASE_DIR", "mock/dir")
    @mock.patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @mock.patch("scripts.workers.submission_worker.extract_challenge_data")
    def test_load_challenge(self, mock_ecd, mock_create):
        submission_worker.load_challenge(self.challenge)
        mock_create.assert_called_with("mock/dir")
        phases = ChallengePhase.objects.filter(name="Challenge Phase")
        mock_ecd.assert_called_with(self.challenge, phases)

    @mock.patch("scripts.workers.submission_worker.CHALLENGE_DATA_DIR", "mocked/dir/challenge_data/challenge_{challenge_id}")
    @mock.patch("scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_PATH", "mocked/dir/challenge_data/challenge_{challenge_id}/phase_data/phase_{phase_id}/test_annotation_file.txt")
    @mock.patch("scripts.workers.submission_worker.importlib")
    @mock.patch("scripts.workers.submission_worker.download_and_extract_file")
    @mock.patch("scripts.workers.submission_worker.download_and_extract_zip_file")
    @mock.patch("scripts.workers.submission_worker.create_dir_as_python_package")
    @mock.patch("scripts.workers.submission_worker.create_dir")
    @mock.patch("scripts.workers.submission_worker.return_file_url_per_environment")
    def test_extract_challenge_data_succesfully(self, mock_url, mock_createdir,
                                                mock_pypackage, mock_down_ext,
                                                mock_down, mock_import):
        phases = [self.challenge_phase]
        challenge = self.challenge

        challenge_data_directory = "mock/dir/challenge_data/challenge_{challenge_id}".format(challenge_id=self.challenge.id)

        evaluation_script_url = self.challenge.evaluation_script.url
        challenge_zip_file = "mock/dir/challenge_data/challenge_{challenge_id}/challenge_{challenge_id}.zip".format(challenge_id=self.challenge.id)

        phase_data_base_directory = "mock/dir/challenge_data/challenge_{challenge_id}/phase_data".format(challenge_id=self.challenge.id)
        phase_data_directory = "mock/dir/challenge_data/challenge_{challenge_id}/phase_data/phase_{phase_id}".format(challenge_id=self.challenge.id, phase_id=self.challenge_phase.id)

        annotation_file_url = "http://testserver{}".format(self.challenge_phase.test_annotation.url)
        annotation_file_path = "mock/dir/challenge_data/challenge_{challenge_id}/phase_data/phase_{phase_id}/test_sample_file.txt".format(challenge_id=self.challenge.id, phase_id=self.challenge_phase.id)

        submission_worker.extract_challenge_data(challenge, phases)

        mock_pypackage.assert_called_with(challenge_data_directory)

        expected_mock_url_call_list = [mock.call(evaluation_script_url), mock.call(annotation_file_url)]
        expected_mock_createdir_call_list = [mock.call(phase_data_base_directory), mock.call(phase_data_directory)]
        expected_mock_down_ext_call_list = [mock.call(evaluation_script_url, challenge_zip_file, challenge_data_directory),
                                            mock.call(annotation_file_url, annotation_file_path)]

        self.assertEqual(mock_url.call_args_list, expected_mock_url_call_list)
        self.assertEqual(mock_createdir.call_args_list, expected_mock_createdir_call_list)
        self.assertEqual(mock_down_ext.call_args_list, expected_mock_down_ext_call_list)

        CHALLENGE_IMPORT_STRING = "challenge_data.challenge_{challenge_id}"
        mock_import.import_module.assert_called_with(CHALLENGE_IMPORT_STRING.format(challenge_id=self.challenge.id))

    @mock.patch("scripts.workers.submission_worker.importlib.import_module")
    @mock.patch("scripts.workers.submission_worker.logger.exception")
    def test_extract_challenge_data_import_error(self, mock_logger, mock_import):
        phases = [self.challenge_phase]
        challenge = self.challenge

        mock_import.side_effect = ImportError
        submission_worker.extract_challenge_data(challenge, phases)
        mock_logger.assert_called_with("Exception raised while creating Python module for challenge_id: {}".format(self.challene.id))


class RunSubmissionTestClass(APITestCase):

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
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            published=True,
            evaluation_script="tests/integration/worker/data/evaluation_script.zip",
            approved_by_admin=True,
            enable_forum=True,
            anonymous_leaderboard=False)

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        self.test_annotation_file = open("tests/integration/worker/data/test_annotation.txt", "rb")
        self.user_annotation_file = open("tests/integration/worker/data/user_annotation.txt", "rb")

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge_phase = ChallengePhase.objects.create(
                name='Challenge Phase',
                description='Description for Challenge Phase',
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile('test_annotation_file.txt',
                                                   b"Dummy file content",
                                                   content_type='text/plain')
            )

        self.leaderboard_schema = {
            "labels": ["score", "test-score"],
            "default_order_by": "score",
        }
        self.leaderboard = Leaderboard.objects.create(
            schema=self.leaderboard_schema
        )

        self.dataset_split = DatasetSplit.objects.create(
            name="Split 1", codename="split1"
        )

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            challenge_phase=self.challenge_phase,
            dataset_split=self.dataset_split,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC,
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=SimpleUploadedFile(
                'user_annotation_file.txt',
                b"Dummy file content",
                content_type='text/plain'
            ),
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.leaderboard_data = LeaderboardData.objects.create(
            challenge_phase_split=self.challenge_phase_split,
            submission=self.submission,
            leaderboard=self.leaderboard,
            result={"metric1": 10},
        )

    def tearDown(self):
        try:
            shutil.rmtree('/tmp/evalai')
        except OSError:
            pass

    @mock.patch("scripts.workers.submission_worker.SUBMISSION_DATA_DIR", "mocked/dir/submisison_{submission_id}")
    @mock.patch("scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_PATH", "mocked/dir/challenge_data/challenge_{challenge_id}/phase_data/phase_{phase_id}/test_annotation_file.txt")
    @mock.patch("scripts.workers.submission_worker.timezone")
    @mock.patch("scripts.workers.submission_worker.shutil")
    @mock.patch("scripts.workers.submission_worker.LeaderboardData")
    @mock.patch("scripts.workers.submission_worker.create_dir")
    @mock.patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @mock.patch("scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_NAME_MAP")
    def test_run_submission_when_result_key_is_not_there_in_output(self, mock_map, mock_script_dict,
                                                                   mock_createdir, mock_lb,
                                                                   mock_shutil, mock_timezone):
        challenge_id = self.challenge.id
        phase_id = self.challenge_phase.id
        user_annotation_file_path = "tests/integration/worker/data/user_annotation.txt"
        temp_run_dir = "mocked/dir/submission_{}/run".format(self.submission.id)

        mock_map[challenge_id] = mock.Mock()
        mock_map.get(challenge_id).get.return_value = "test_annotation_file.txt"
        mock_script_dict[challenge_id] = mock.Mock()
        mock_script_dict[challenge_id].evaluate.return_value = {"split1": {"metric1": 10}}

        starting_time = timezone.now()
        time.sleep(0.5)
        ending_time = timezone.now()
        mock_timezone.now.side_effect = [starting_time, ending_time]

        if not os.path.exists(temp_run_dir):  # to account for the fact that create_dir is mocked out.
            os.makedirs(temp_run_dir)

        submission_worker.run_submission(challenge_id, self.challenge_phase, self.submission, user_annotation_file_path)

        annotation_file_path = "mocked/dir/challenge_data/challenge_{}/phase_data/phase_{}/test_annotation_file.txt".format(
            challenge_id, phase_id)

        mock_createdir.assert_called_with(temp_run_dir)

        mock_script_dict[challenge_id].evaluate.assert_called_with(
            annotation_file_path,
            user_annotation_file_path,
            self.challenge_phase.codename,
        )

        mock_lb.objects.bulk_create.assert_not_called()

        self.assertEqual(self.submission.started_at, starting_time)
        self.assertEqual(self.submission.status, Submission.FAILED)
        self.assertEqual(self.submission.completed_at, ending_time)

        expected_output = {"result": ""}
        self.assertEqual(self.submission.output, expected_output)

        mock_shutil.rmtree.assert_called_with(temp_run_dir)

    @mock.patch("scripts.workers.submission_worker.SUBMISSION_DATA_DIR", "mocked/dir/submisison_{submission_id}")
    @mock.patch("scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_PATH", "mocked/dir/challenge_data/challenge_{challenge_id}/phase_data/phase_{phase_id}/test_annotation_file.txt")
    @mock.patch("scripts.workers.submission_worker.timezone")
    @mock.patch("scripts.workers.submission_worker.shutil")
    @mock.patch("scripts.workers.submission_worker.LeaderboardData")
    @mock.patch("scripts.workers.submission_worker.create_dir")
    @mock.patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @mock.patch("scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_NAME_MAP")
    def test_run_submission_when_challenge_phase_split_does_not_exist(self, mock_map, mock_script_dict,
                                                                      mock_createdir, mock_lb,
                                                                      mock_shutil, mock_timezone):
        challenge_id = self.challenge.id
        phase_id = self.challenge_phase.id
        user_annotation_file_path = "tests/integration/worker/data/user_annotation.txt"
        temp_run_dir = "mocked/dir/submission_{}/run".format(self.submission.id)

        mock_map[challenge_id] = mock.Mock()
        mock_map.get(challenge_id).get.return_value = "test_annotation_file.txt"
        mock_script_dict[challenge_id] = mock.Mock()
        mock_script_dict[challenge_id].evaluate.return_value = {"result": {"split2": {"metric1": 10}}}

        starting_time = timezone.now()
        time.sleep(0.5)
        ending_time = timezone.now()
        mock_timezone.now.side_effect = [starting_time, ending_time]

        if not os.path.exists(temp_run_dir):  # to account for the fact that create_dir is mocked out.
            os.makedirs(temp_run_dir)

        submission_worker.run_submission(challenge_id, self.challenge_phase, self.submission, user_annotation_file_path)

        annotation_file_path = "mocked/dir/challenge_data/challenge_{}/phase_data/phase_{}/test_annotation_file.txt".format(
            challenge_id, phase_id)

        mock_createdir.assert_called_with(temp_run_dir)

        mock_script_dict[challenge_id].evaluate.assert_called_with(
            annotation_file_path,
            user_annotation_file_path,
            self.challenge_phase.codename,
        )

        '''
        self.assertEqual(mock_open.write.call_args_list[0],
                         mock.call("ORGINIAL EXCEPTION: No such relation between Challenge Phase and DatasetSplit"
                                   " specified by Challenge Host \n")
        )
        '''

        mock_lb.objects.bulk_create.assert_not_called()

        self.assertEqual(self.submission.started_at, starting_time)
        self.assertEqual(self.submission.status, Submission.FAILED)
        self.assertEqual(self.submission.completed_at, ending_time)

        expected_output = {"result": {"split2": {"metric1": 10}}}
        self.assertEqual(self.submission.output, expected_output)

        mock_shutil.rmtree.assert_called_with(temp_run_dir)

    @mock.patch("scripts.workers.submission_worker.SUBMISSION_DATA_DIR", "mocked/dir/submisison_{submission_id}")
    @mock.patch("scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_PATH", "mocked/dir/challenge_data/challenge_{challenge_id}/phase_data/phase_{phase_id}/test_annotation_file.txt")
    @mock.patch("scripts.workers.submission_worker.SubmissionSerializer.data", {'metadata': 'fake data'})
    @mock.patch("scripts.workers.submission_worker.timezone")
    @mock.patch("scripts.workers.submission_worker.shutil")
    @mock.patch("scripts.workers.submission_worker.LeaderboardData")
    @mock.patch("scripts.workers.submission_worker.create_dir")
    @mock.patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
    @mock.patch("scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_NAME_MAP")
    def test_run_submission_succesful(self, mock_map, mock_script_dict, mock_createdir, mock_lb, mock_shutil, mock_timezone):
        challenge_id = self.challenge.id
        phase_id = self.challenge_phase.id
        user_annotation_file_path = "tests/integration/worker/data/user_annotation.txt"
        leaderboard_data_list = [self.leaderboard_data]
        temp_run_dir = "mocked/dir/submission_{}/run".format(self.submission.id)

        mock_map[challenge_id] = mock.Mock()
        mock_map.get(challenge_id).get.return_value = "test_annotation_file.txt"
        mock_script_dict[challenge_id] = mock.Mock()
        mock_script_dict[challenge_id].evaluate.return_value = {"result": {"split1": {"metric1": 10}}}

        starting_time = timezone.now()
        time.sleep(0.5)
        ending_time = timezone.now()
        mock_timezone.now.side_effect = [starting_time, ending_time]

        if not os.path.exists(temp_run_dir):  # to account for the fact that create_dir is mocked out.
            os.makedirs(temp_run_dir)

        submission_worker.run_submission(challenge_id, self.challenge_phase, self.submission, user_annotation_file_path)

        annotation_file_path = "mocked/dir/challenge_data/challenge_{}/phase_data/phase_{}/test_annotation_file.txt".format(
            challenge_id, phase_id)

        test_metadata = {"metadata": "fake data"}

        mock_createdir.assert_called_with(temp_run_dir)

        mock_script_dict[challenge_id].evaluate.assert_called_with(
            annotation_file_path,
            user_annotation_file_path,
            self.challenge_phase.codename,
            submission_metadata=test_metadata,
        )

        mock_lb.objects.bulk_create.assert_called_with(leaderboard_data_list)

        self.assertEqual(self.submission.started_at, starting_time)
        self.assertEqual(self.submission.status, Submission.FINISHED)
        self.assertEqual(self.submission.completed_at, ending_time)

        expected_output = {"result": {"split1": {"metric1": 10}}}
        self.assertEqual(self.submission.output, expected_output)

        mock_shutil.rmtree.assert_called_with(temp_run_dir)
