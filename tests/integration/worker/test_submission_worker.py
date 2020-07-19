import json
import mock
import os
import shutil
import time

from allauth.account.models import EmailAddress

from datetime import timedelta

from django.conf import settings
from django.core.files.base import ContentFile
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


class BaseTestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.user1 = User.objects.create(
            username="someuser1",
            email="user1@test.com",
            password="secret_password1",
        )

        self.client.force_authenticate(user=self.user)

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge", created_by=self.user
        )

        self.participant = Participant.objects.create(
            user=self.user, status=Participant.SELF, team=self.participant_team
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=1),
            published=True,
            approved_by_admin=True,
            enable_forum=True,
            anonymous_leaderboard=False,
        )

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
            )
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=SimpleUploadedFile(
                "user_annotation_file.txt",
                b"Dummy file content",
                content_type="text/plain",
            ),
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.WORKER_LOGS_PREFIX = "WORKER_LOG"
        self.SUBMISSION_LOGS_PREFIX = "SUBMISSION_LOG"

    def tearDown(self):
        try:
            shutil.rmtree("/tmp/evalai")
        except OSError:
            pass


class ProcessSubmissionCallbackTestClass(BaseTestClass):
    @mock.patch("scripts.workers.submission_worker.process_submission_message")
    def test_process_submission_callback(self, mock_psm):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": self.challenge_phase.pk,
            "submission_pk": self.submission.pk,
        }
        body = json.dumps(message)

        submission_worker.process_submission_callback(body)
        mock_psm.assert_called_with(message)

    @mock.patch("scripts.workers.submission_worker.logger.exception")
    @mock.patch("scripts.workers.submission_worker.process_submission_message")
    def test_process_submission_callback_with_exception(
        self, mock_psm, mock_logger
    ):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": self.challenge_phase.pk,
            "submission_pk": self.submission.pk,
        }
        body = json.dumps(message)

        mock_psm.side_effect = Exception("test error")

        submission_worker.process_submission_callback(body)

        mock_logger.assert_called_with(
            "{} Exception while receiving message from submission queue with error test error".format(self.SUBMISSION_LOGS_PREFIX)
        )

    @mock.patch(
        "scripts.workers.submission_worker.SUBMISSION_DATA_DIR",
        "mocked/dir/submission_{submission_id}",
    )
    @mock.patch(
        "scripts.workers.submission_worker.os.path.basename",
        return_value="user_annotation_file.txt",
    )
    @mock.patch("scripts.workers.submission_worker.run_submission")
    def test_process_submission_message_succesfully(
        self, mock_rs, mock_basename
    ):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": self.challenge_phase.pk,
            "submission_pk": self.submission.pk,
        }
        user_annotation_file_path = "mocked/dir/submission_{}/user_annotation_file.txt".format(
            self.submission.pk
        )

        with mock.patch(
            "scripts.workers.submission_worker.extract_submission_data"
        ) as mock_esd:
            submission_worker.process_submission_message(message)
            mock_esd.assert_called_with(self.submission.pk)

        submission_worker.process_submission_message(message)

        mock_rs.assert_called_with(
            self.challenge.pk,
            self.challenge_phase,
            self.submission,
            user_annotation_file_path,
        )

    @mock.patch("scripts.workers.submission_worker.extract_submission_data")
    def test_process_submission_message_when_submission_does_not_exist(
        self, mock_esd
    ):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": self.challenge_phase.pk,
            "submission_pk": self.submission.pk,
        }
        mock_esd.return_value = None

        submission_worker.process_submission_message(message)

        self.assertEqual(
            submission_worker.process_submission_message(message), None
        )

    @mock.patch("scripts.workers.submission_worker.extract_submission_data")
    @mock.patch("scripts.workers.submission_worker.logger.exception")
    def test_process_submission_message_when_challenge_phase_does_not_exist(
        self, mock_logger, mock_esd
    ):
        message = {
            "challenge_pk": self.challenge.pk,
            "phase_pk": self.challenge_phase.pk + 999,
            "submission_pk": self.submission.pk,
        }
        mock_esd.return_value = self.submission
        phase_pk = self.challenge_phase.pk + 999
        with self.assertRaises(Exception):
            submission_worker.process_submission_message(message)

        mock_logger.assert_called_with(
            "{} Challenge Phase {} does not exist".format(self.WORKER_LOGS_PREFIX, phase_pk)
        )


class ExtractSubmissionDataTestClass(BaseTestClass):
    @mock.patch("scripts.workers.submission_worker.logger.critical")
    def test_extract_submission_data_when_submission_does_not_exist(
        self, mock_logger
    ):
        submission_pk = self.submission.pk - 999
        value = submission_worker.extract_submission_data(submission_pk)
        mock_logger.assert_called_with(
            "{} Submission {} does not exist".format(self.SUBMISSION_LOGS_PREFIX, submission_pk)
        )
        self.assertEqual(value, None)

    @mock.patch(
        "scripts.workers.submission_worker.SUBMISSION_DATA_DIR",
        "mocked/dir/submission_{submission_id}",
    )
    @mock.patch(
        "scripts.workers.submission_worker.SUBMISSION_INPUT_FILE_PATH",
        "mocked/dir/submission_{submission_id}/{input_file}",
    )
    @mock.patch("scripts.workers.submission_worker.download_and_extract_file")
    @mock.patch(
        "scripts.workers.submission_worker.create_dir_as_python_package"
    )
    def test_extract_submission_data_succesfully(
        self, mock_createdir, mock_down_ext
    ):
        with mock.patch(
            "scripts.workers.submission_worker.return_file_url_per_environment"
        ) as mock_url:
            submission_worker.extract_submission_data(self.submission.pk)

            submission_input_file = self.submission.input_file.url
            mock_url.assert_called_with(submission_input_file)

            submission_data_directory = "mocked/dir/submission_{}".format(
                self.submission.pk
            )
            mock_createdir.assert_called_with(submission_data_directory)

        submission_worker.extract_submission_data(self.submission.pk)

        name = os.path.basename(self.submission.input_file.name)
        submission_input_file_url = f"http://{settings.DJANGO_SERVER}:{settings.DJANGO_SERVER_PORT}{self.submission.input_file.url}"
        submission_input_file_path = "mocked/dir/submission_{}/{}".format(
            self.submission.pk, name
        )
        mock_down_ext.assert_called_with(
            submission_input_file_url, submission_input_file_path
        )


class ExtractChallengeDataTestClass(BaseTestClass):
    @mock.patch("scripts.workers.submission_worker.importlib.import_module")
    @mock.patch("scripts.workers.submission_worker.logger.exception")
    def test_extract_challenge_data_import_error(
        self, mock_logger, mock_import
    ):
        phases = [self.challenge_phase]
        challenge = self.challenge

        mock_import.side_effect = ImportError

        with self.assertRaises(Exception):
            submission_worker.extract_challenge_data(challenge, phases)
            mock_logger.assert_called_with(
                "Exception raised while creating Python module for challenge_id: {}".format(
                    self.challenge.pk
                )
            )


@mock.patch("scripts.workers.submission_worker.SubmissionSerializer.data", "")
@mock.patch(
    "scripts.workers.submission_worker.SUBMISSION_DATA_DIR",
    "mocked/dir/submission_{submission_id}",
)
@mock.patch(
    "scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_PATH",
    "mocked/dir/challenge_data/challenge_{challenge_id}/phase_data/phase_{phase_id}/test_annotation_file.txt",
)
@mock.patch("scripts.workers.submission_worker.ContentFile")
@mock.patch("scripts.workers.submission_worker.open")
@mock.patch("scripts.workers.submission_worker.timezone")
@mock.patch("scripts.workers.submission_worker.shutil")
@mock.patch(
    "scripts.workers.submission_worker.LeaderboardData.objects.bulk_create"
)
@mock.patch("scripts.workers.submission_worker.create_dir")
@mock.patch("scripts.workers.submission_worker.EVALUATION_SCRIPTS")
@mock.patch("scripts.workers.submission_worker.PHASE_ANNOTATION_FILE_NAME_MAP")
class RunSubmissionTestClass(BaseTestClass):
    def setUp(self):
        super(RunSubmissionTestClass, self).setUp()
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
        self.metric = 10
        self.leaderboard_data = LeaderboardData.objects.create(
            challenge_phase_split=self.challenge_phase_split,
            submission=self.submission,
            leaderboard=self.leaderboard,
            result={"metric1": self.metric},
        )

    def test_run_submission_when_result_key_is_not_present_in_output(
        self,
        mock_map,
        mock_script_dict,
        mock_createdir,
        mock_lb,
        mock_shutil,
        mock_timezone,
        mock_open,
        mock_cf,
    ):
        challenge_pk = self.challenge.pk
        phase_pk = self.challenge_phase.pk
        user_annotation_file_path = (
            "tests/integration/worker/data/user_annotation.txt"
        )
        temp_run_dir = "mocked/dir/submission_{}/run".format(
            self.submission.pk
        )

        mock_map[challenge_pk] = mock.Mock()
        mock_map.get(
            challenge_pk
        ).get.return_value = "test_annotation_file.txt"
        mock_script_dict[challenge_pk] = mock.Mock()
        mock_script_dict[challenge_pk].evaluate.return_value = {
            "split1": {"metric1": self.metric}
        }

        starting_time = timezone.now()
        time.sleep(0.5)
        ending_time = timezone.now()
        mock_timezone.now.side_effect = [starting_time, ending_time]

        if not os.path.exists(temp_run_dir):
            os.makedirs(temp_run_dir)

        patcher = mock.patch("scripts.workers.submission_worker.ContentFile")
        mock_cf = patcher.start()
        mock_cf.return_value = ContentFile("")

        submission_worker.run_submission(
            challenge_pk,
            self.challenge_phase,
            self.submission,
            user_annotation_file_path,
        )

        annotation_file_path = "mocked/dir/challenge_data/challenge_{}/phase_data/phase_{}/test_annotation_file.txt".format(
            challenge_pk, phase_pk
        )

        mock_createdir.assert_called_with(temp_run_dir)

        mock_script_dict[challenge_pk].evaluate.assert_called_with(
            annotation_file_path,
            user_annotation_file_path,
            self.challenge_phase.codename,
            submission_metadata="",
        )

        mock_lb.assert_not_called()

        self.assertEqual(self.submission.started_at, starting_time)
        self.assertEqual(self.submission.status, Submission.FAILED)
        self.assertEqual(self.submission.completed_at, ending_time)

        mock_shutil.rmtree.assert_called_with(temp_run_dir)

    def test_run_submission_when_challenge_phase_split_does_not_exist(
        self,
        mock_map,
        mock_script_dict,
        mock_createdir,
        mock_lb,
        mock_shutil,
        mock_timezone,
        mock_open,
        mock_cf,
    ):
        challenge_pk = self.challenge.pk
        phase_pk = self.challenge_phase.pk
        user_annotation_file_path = (
            "tests/integration/worker/data/user_annotation.txt"
        )
        temp_run_dir = "mocked/dir/submission_{}/run".format(
            self.submission.pk
        )

        mock_map[challenge_pk] = mock.Mock()
        mock_map.get(
            challenge_pk
        ).get.return_value = "test_annotation_file.txt"
        mock_script_dict[challenge_pk] = mock.Mock()
        mock_script_dict[challenge_pk].evaluate.return_value = {
            "result": [{"split2": {"metric1": self.metric}}]
        }

        starting_time = timezone.now()
        time.sleep(0.5)
        ending_time = timezone.now()
        mock_timezone.now.side_effect = [starting_time, ending_time]

        if not os.path.exists(temp_run_dir):
            os.makedirs(temp_run_dir)

        patcher = mock.patch("scripts.workers.submission_worker.ContentFile")
        mock_cf = patcher.start()
        mock_cf.return_value = ContentFile("")

        submission_worker.run_submission(
            challenge_pk,
            self.challenge_phase,
            self.submission,
            user_annotation_file_path,
        )

        self.assertEqual(
            mock_open.return_value.write.call_args_list[0],
            mock.call(
                "ORGINIAL EXCEPTION: No such relation between Challenge Phase and DatasetSplit"
                " specified by Challenge Host \n"
            ),
        )

        annotation_file_path = "mocked/dir/challenge_data/challenge_{}/phase_data/phase_{}/test_annotation_file.txt".format(
            challenge_pk, phase_pk
        )

        mock_createdir.assert_called_with(temp_run_dir)

        mock_script_dict[challenge_pk].evaluate.assert_called_with(
            annotation_file_path,
            user_annotation_file_path,
            self.challenge_phase.codename,
            submission_metadata="",
        )

        mock_lb.objects.bulk_create.assert_not_called()

        self.assertEqual(self.submission.started_at, starting_time)
        self.assertEqual(self.submission.status, Submission.FAILED)
        self.assertEqual(self.submission.completed_at, ending_time)

        mock_shutil.rmtree.assert_called_with(temp_run_dir)
        patcher.stop()
