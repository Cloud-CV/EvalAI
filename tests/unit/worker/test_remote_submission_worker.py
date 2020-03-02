import json
import mock
import os
import responses
import shutil
from unittest import TestCase

from tests.data import challenge_response, submission_response

from scripts.workers.worker_utils import EvalAI_Interface
import scripts.workers.remote_submission_worker as remote_submission_worker


class BaseTestClass(TestCase):
    def setUp(self):
        super(BaseTestClass, self).setUp()
        self.BASE_TEMP_DIR = remote_submission_worker.BASE_TEMP_DIR
        self.CHALLENGE_DATA_BASE_DIR = self.BASE_TEMP_DIR + "/compute/challenge_data"
        self.SUBMISSION_DATA_BASE_DIR = self.BASE_TEMP_DIR + "/compute/submission_files"
        try:
            os.makedirs(self.CHALLENGE_DATA_BASE_DIR)
            os.makedirs(self.SUBMISSION_DATA_BASE_DIR)
        except OSError:
            pass
        self.api = EvalAI_Interface(
            AUTH_TOKEN="test_token",
            EVALAI_API_SERVER="http://testserver",
            QUEUE_NAME="test_queue"
        )

    def tearDown(self):
        try:
            shutil.rmtree(self.BASE_TEMP_DIR)
        except OSError:
            pass


class ChallengeDataTestClass(BaseTestClass):
    def setUp(self):
        super(ChallengeDataTestClass, self).setUp()
        self.challenge = json.loads(challenge_response.challenge_details)
        self.phases = json.loads(challenge_response.challenge_phase_list).get("results")

    @mock.patch("scripts.workers.worker_utils.download_and_extract_file")
    @mock.patch("scripts.workers.worker_utils.create_dir_as_python_package")
    @mock.patch("scripts.workers.worker_utils.download_and_extract_zip_file")
    @mock.patch("scripts.workers.worker_utils.create_dir")
    @mock.patch("scripts.workers.remote_submission_worker.importlib.import_module")
    def test_extract_challenge_data_successfully(self, mock_import, mock_cd, mock_dezf, mock_cdapp, mock_def):
        remote_submission_worker.extract_challenge_data(self.challenge, self.phases)

        challenge_dir = self.CHALLENGE_DATA_BASE_DIR + "/challenge_1"
        mock_cdapp.assert_any_call(challenge_dir)

        evaluation_script_url = "evaluation_script.zip"
        challenge_zip_file = challenge_dir + "/challenge_1.zip"
        mock_dezf.assert_any_call(
            evaluation_script_url,
            challenge_zip_file,
            challenge_dir
        )

        challenge_phase_dir = challenge_dir + "/phase_data"
        mock_cd.assert_any_call(challenge_phase_dir)

        mock_cd.assert_any_call(challenge_phase_dir + "/phase_1")
        mock_def.assert_any_call("http://test_annotation.txt", challenge_phase_dir + "/phase_2/test_annotation.txt")

        mock_cd.assert_any_call(challenge_phase_dir + "/phase_2")
        mock_def.assert_any_call("http://test_annotation.txt", challenge_phase_dir + "/phase_2/test_annotation.txt")

        import_string = "challenge_data" + "." + "challenge_1"
        mock_import.assert_called_with(import_string)

    @responses.activate
    @mock.patch("scripts.workers.worker_utils.create_dir_as_python_package")
    @mock.patch("scripts.workers.remote_submission_worker.extract_challenge_data")
    def test_load_challenge_data_successfully(self, mock_ecd, mock_cdapp):
        responses.add(
            responses.GET,
            'http://testserver/api/challenges/challenge/queues/test_queue/',
            json=self.challenge
        )
        responses.add(
            responses.GET,
            'http://testserver/api/challenges/1/phases/',
            json=self.phases
        )
        remote_submission_worker.load_challenge(self.api)

        mock_cdapp(self.CHALLENGE_DATA_BASE_DIR)
        mock_ecd(self.challenge, self.phases)

    @responses.activate
    @mock.patch("scripts.workers.worker_utils.logger.critical")
    def test_load_challenge_fails(self, mock_logger):
        responses.add(
            responses.GET,
            'http://testserver/api/challenges/challenge/queues/non_existent_queue/',
            json={}
        )
        self.api.QUEUE_NAME = 'non_existent_queue'
        remote_submission_worker.load_challenge(self.api)
        self.api.QUEUE_NAME = 'test_queue'

        mock_logger.assert_called_with(
            "Challenge with queue name non_existent_queue does not exists"
        )

    @mock.patch("scripts.workers.remote_submission_worker.importlib.import_module")
    @mock.patch("scripts.workers.worker_utils.logger.exception")
    @mock.patch("scripts.workers.remote_submission_worker.CHALLENGE_IMPORT_STRING", "incorrect_string")
    def test_extract_challenge_data_import_error(self, mock_logger, mock_import):
        mock_import.side_effect = ImportError

        with self.assertRaises(Exception):
            remote_submission_worker.extract_challenge_data(self.challenge, self.phases)
            mock_logger.assert_called_with("Exception raised while creating Python module for challenge_id: {}".format(self.challenge.pk))


class SubmissionDataTestClass(BaseTestClass):
    def setUp(self):
        super(SubmissionDataTestClass, self).setUp()
        self.submission = json.loads(submission_response.submission_result)

    @responses.activate
    @mock.patch("scripts.workers.worker_utils.download_and_extract_file")
    @mock.patch("scripts.workers.worker_utils.create_dir_as_python_package")
    def test_extract_submission_data_successfully(self, mock_cdpp, mock_def):
        responses.add(
            responses.GET,
            'http://testserver/api/jobs/submission/1',
            json=self.submission
        )
        self.submission_pk = 1
        remote_submission_worker.extract_submission_data(self.submission_pk, self.api)

        submission_data_directory = self.SUBMISSION_DATA_BASE_DIR + "/submission_1"
        mock_cdpp.assert_called_with(submission_data_directory)

        submission_input_file = "http://testserver/media/submission_files/submission_1/2224fb89-6828-47f4-b170-1279290ad900.json"
        submission_input_file_path = submission_data_directory + "/2224fb89-6828-47f4-b170-1279290ad900.json"
        mock_def.assert_called_with(
            submission_input_file,
            submission_input_file_path
        )

    @responses.activate
    @mock.patch("scripts.workers.worker_utils.logger.critical")
    def test_extract_submission_not_exist(self, mock_logger):
        responses.add(
            responses.GET,
            'http://testserver/api/jobs/submission/2',
            json={}
        )
        self.submission_pk = 2
        remote_submission_worker.extract_submission_data(self.submission_pk, self.api)
        mock_logger("Submission {} does not exist".format(self.submission_pk))


class ProcessSubmissionTestClass(BaseTestClass):
    def setUp(self):
        super(ProcessSubmissionTestClass, self).setUp()
        self.challenge = json.loads(challenge_response.challenge_details)
        self.phase = json.loads(challenge_response.challenge_phase_details)
        self.submission = json.loads(submission_response.submission_result)
        self.queue_message = {
            "challenge_pk": 1,
            "phase_pk": 1,
            "submission_pk": 2
        }

    @mock.patch("scripts.workers.worker_utils.logger.info")
    @mock.patch("scripts.workers.remote_submission_worker.process_submission_message")
    def test_process_submission_callback_success(self, mock_psm, mock_logger):
        remote_submission_worker.process_submission_callback(self.queue_message, self.api)
        mock_logger.assert_called_with("[x] Received submission message %s" % self.queue_message)
        mock_psm.assert_called_with(self.queue_message, self.api)

    @responses.activate
    @mock.patch("scripts.workers.remote_submission_worker.run_submission")
    def test_process_submission_message_success(self, mock_rs):
        responses.add(
            responses.GET,
            'http://testserver/api/challenges/challenge/queues/test_queue/',
            json=self.challenge
        )
        responses.add(
            responses.GET,
            'http://testserver/api/jobs/challenge/queues/test_queue/',
            json=self.queue_message
        )
        responses.add(
            responses.GET,
            'http://testserver/api/challenges/challenge/1/challenge_phase/1',
            json=self.phase
        )
        responses.add(
            responses.GET,
            'http://testserver/api/jobs/submission/2',
            json=self.submission
        )

        remote_submission_worker.process_submission_message(self.queue_message, self.api)

        user_annotation_file_path = self.SUBMISSION_DATA_BASE_DIR + "/submission_2" + \
            "/2224fb89-6828-47f4-b170-1279290ad900.json"

        remote_evaluation = True

        mock_rs.assert_called_with(
            self.queue_message.get("challenge_pk"),
            self.phase,
            self.submission,
            user_annotation_file_path,
            remote_evaluation,
            self.api
        )
