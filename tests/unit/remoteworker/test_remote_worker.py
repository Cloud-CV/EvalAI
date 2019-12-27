import mock
import os
import responses
import shutil
import tempfile

from os.path import join

from unittest import TestCase

from scripts.workers.remote_submission_worker import (
    create_dir_as_python_package,
    make_request,
    get_message_from_sqs_queue,
    delete_message_from_sqs_queue,
    download_and_extract_file,
    get_submission_by_pk,
    get_challenge_phases_by_challenge_pk,
    get_challenge_by_queue_name,
    get_challenge_phase_by_pk,
    process_submission_message,
    update_submission_data,
    update_submission_status,
    return_url_per_environment,
)


class BaseTestClass(TestCase):
    def setUp(self):
        self.submission_pk = 1
        self.challenge_pk = 1
        self.challenge_phase_pk = 1
        self.data = {"test": "data"}
        self.headers = {"Authorization": "Token test_token"}
        self.testserver = "http://testserver"

    def make_request_url(self):
        return "/test/url"

    def get_message_from_sqs_queue_url(self, queue_name):
        return "/api/jobs/challenge/queues/{}/".format(queue_name)

    def delete_message_from_sqs_queue_url(self, queue_name):
        return "/api/jobs/queues/{}/".format(queue_name)

    def get_submission_by_pk_url(self, submission_pk):
        return "/api/jobs/submission/{}".format(submission_pk)

    def get_challenge_phases_by_challenge_pk_url(self, challenge_pk):
        return "/api/challenges/{}/phases/".format(challenge_pk)

    def get_challenge_by_queue_name_url(self, queue_name):
        return "/api/challenges/challenge/queues/{}/".format(queue_name)

    def get_challenge_phase_by_pk_url(self, challenge_pk, challenge_phase_pk):
        return "/api/challenges/challenge/{}/challenge_phase/{}".format(challenge_pk, challenge_phase_pk)

    def update_submission_data_url(self, challenge_pk):
        return "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)


@mock.patch("scripts.workers.remote_submission_worker.AUTH_TOKEN", "test_token")
@mock.patch("scripts.workers.remote_submission_worker.requests")
class MakeRequestTestClass(BaseTestClass):
    def setUp(self):
        super(MakeRequestTestClass, self).setUp()
        self.url = super(MakeRequestTestClass, self).make_request_url()

    def test_make_request_get(self, mock_make_request):
        make_request(self.url, "GET")
        mock_make_request.get.assert_called_with(url=self.url, headers=self.headers)

    def test_make_request_put(self, mock_make_request):
        make_request(self.url, "PUT", data=self.data)
        mock_make_request.put.assert_called_with(url=self.url, headers=self.headers, data=self.data)

    def test_make_request_patch(self, mock_make_request):
        make_request(self.url, "PATCH", data=self.data)
        mock_make_request.patch.assert_called_with(url=self.url, headers=self.headers, data=self.data)

    def test_make_request_post(self, mock_make_request):
        make_request(self.url, "POST", data=self.data)
        mock_make_request.post.assert_called_with(url=self.url, headers=self.headers, data=self.data)


@mock.patch("scripts.workers.remote_submission_worker.QUEUE_NAME", "evalai_submission_queue")
@mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
@mock.patch("scripts.workers.remote_submission_worker.make_request")
class APICallsTestClass(BaseTestClass):

    def test_get_message_from_sqs_queue(self, mock_make_request, mock_url):
        url = self.get_message_from_sqs_queue_url("evalai_submission_queue")
        get_message_from_sqs_queue()
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_delete_message_from_sqs_queue(self, mock_make_request, mock_url):
        test_receipt_handle = "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"
        url = self.delete_message_from_sqs_queue_url("evalai_submission_queue")
        delete_message_from_sqs_queue(test_receipt_handle)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        expected_data = {"receipt_handle": "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"}
        mock_make_request.assert_called_with(url, "POST", data=expected_data)

    def test_get_challenge_by_queue_name(self, mock_make_request, mock_url):
        url = self.get_challenge_by_queue_name_url("evalai_submission_queue")
        get_challenge_by_queue_name()
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_submission_by_pk(self, mock_make_request, mock_url):
        get_submission_by_pk(self.submission_pk)
        url = self.get_submission_by_pk_url(self.submission_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phases_by_challenge_pk(self, mock_make_request, mock_url):
        get_challenge_phases_by_challenge_pk(self.challenge_pk)
        url = self.get_challenge_phases_by_challenge_pk_url(self.challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phase_by_pk(self, mock_make_request, mock_url):
        get_challenge_phase_by_pk(self.challenge_pk, self.challenge_phase_pk)
        url = self.get_challenge_phase_by_pk_url(self.challenge_pk, self.challenge_phase_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_update_submission_data(self, mock_make_request, mock_url):
        update_submission_data(self.data, self.challenge_pk, self.submission_pk)
        url = self.update_submission_data_url(self.challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PUT", data=self.data)

    def test_update_submission_status(self, mock_make_request, mock_url):
        update_submission_status(self.data, self.challenge_pk)
        url = self.update_submission_data_url(self.challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PATCH", data=self.data)


@mock.patch("scripts.workers.remote_submission_worker.DJANGO_SERVER_PORT", "80")
@mock.patch("scripts.workers.remote_submission_worker.DJANGO_SERVER", "testserver")
class URLFormatTestCase(BaseTestClass):

    def test_return_url_per_environment(self):
        url = "/test/url"
        expected_url = "http://testserver:80{}".format(url)
        returned_url = return_url_per_environment(url)
        self.assertEqual(returned_url, expected_url)


class CreateDirAsPythonPackageTest(BaseTestClass):
    def setUp(self):
        super(CreateDirAsPythonPackageTest, self).setUp()

        self.BASE_TEMP_DIR = tempfile.mkdtemp()
        self.temp_directory = join(self.BASE_TEMP_DIR, "temp_dir")

    def test_create_dir_as_python_package(self):
        create_dir_as_python_package(self.temp_directory)
        self.assertTrue(os.path.isfile(join(self.temp_directory, "__init__.py")))

        with open(join(self.temp_directory, "__init__.py")) as f:
            self.assertEqual(f.read(), "")

        shutil.rmtree(self.temp_directory)
        self.assertFalse(os.path.exists(self.temp_directory))


class DownloadAndExtractFileTest(BaseTestClass):
    def setUp(self):
        super(DownloadAndExtractFileTest, self).setUp()
        self.req_url = "{}{}".format(self.testserver, self.make_request_url())
        self.file_content = b'file content'

        self.temp_directory = tempfile.mkdtemp()
        self.download_location = join(self.temp_directory, "dummy_file")

    def tearDown(self):
        if os.path.exists(self.temp_directory):
            shutil.rmtree(self.temp_directory)

    @responses.activate
    def test_download_and_extract_file_success(self):
        responses.add(responses.GET, self.req_url,
                      body=self.file_content,
                      content_type='application/octet-stream',
                      status=200)

        download_and_extract_file(self.req_url, self.download_location)

        self.assertTrue(os.path.exists(self.download_location))
        with open(self.download_location, "rb") as f:
            self.assertEqual(f.read(), self.file_content)

    @responses.activate
    @mock.patch("scripts.workers.remote_submission_worker.logger.error")
    def test_download_and_extract_file_when_download_fails(self, mock_logger):
        error = "ExampleError: Example Error description"
        responses.add(responses.GET, self.req_url, body=Exception(error))
        expected = "Failed to fetch file from {}, error {}".format(self.req_url, error)

        download_and_extract_file(self.req_url, self.download_location)

        mock_logger.assert_called_with(expected)
        self.assertFalse(os.path.exists(self.download_location))


class ProcessSubmissionMessageTest(BaseTestClass):
    def setUp(self):
        super(ProcessSubmissionMessageTest, self).setUp()
        self.queue_name = "evalai_submission_queue"
        self.submission_data_dir = "tmp/test-dir/submission_{}".format(self.submission_pk)
        self.input_file = "user_annotation_file.txt"
        self.remote_evaluation = "Test Remote Evaluation"

        # Creating sample outputs with minimal data for mocked functions
        self.message = {
            "challenge_pk": self.challenge_pk,
            "phase_pk": self.challenge_phase_pk,
            "submission_pk": self.submission_pk,
        }
        self.submission = {"id": self.submission_pk, "input_file": self.input_file}
        self.challenge = {"id": self.challenge_id, "remote_evaluation": self.remote_evaluation}
        self.challenge_phase = {"id": self.challenge_phase_pk}

        self.patcher = mock.patch.multiple(
            "scripts.workers.remote_submission_worker",
            QUEUE_NAME=self.queue_name, SUBMISSION_DATA_DIR=self.submission_data_dir,
        )

        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    @mock.patch("scripts.workers.remote_submission_worker.run_submission")
    @mock.patch("scripts.workers.remote_submission_worker.get_challenge_phase_by_pk")
    @mock.patch("scripts.workers.remote_submission_worker.get_challenge_by_queue_name")
    @mock.patch("scripts.workers.remote_submission_worker.extract_submission_data")
    def test_process_submission_message_success(self, mock_extract_submission_data, mock_get_challenge_by_queue_name,
                                                mock_get_challenge_phase_by_pk, mock_run_submission):
        mock_extract_submission_data.return_value =  self.submission
        mock_get_challenge_by_queue_name.return_value = self.challenge
        mock_get_challenge_phase_by_pk.return_value = self.challenge_phase

        user_annotation_file_path = join(self.submission_data_dir, self.input_file)

        process_submission_message(self.message)

        mock_extract_submission_data.assert_called_with(self.submission_pk)
        mock_get_challenge_by_queue_name.assert_called()
        mock_get_challenge_phase_by_pk.assert_called_with(self.challenge_pk, self.challenge_phase_pk)
        mock_run_submission.assert_called_with(
            self.challenge_pk,
            self.challenge_phase,
            self.submission,
            user_annotation_file_path,
            self.remote_evaluation,
        )

    @mock.patch("scripts.workers.remote_submission_worker.run_submission")
    @mock.patch("scripts.workers.remote_submission_worker.get_challenge_phase_by_pk")
    @mock.patch("scripts.workers.remote_submission_worker.extract_submission_data")
    def test_process_submission_message_when_submission_does_not_exist(self,
                                                                       mock_extract_submission_data,
                                                                       mock_get_challenge_phase_by_pk,
                                                                       mock_run_submission):
        mock_extract_submission_data.return_value = None

        process_submission_message(self.message)

        mock_extract_submission_data.assert_called_with(self.submission_pk)
        mock_get_challenge_phase_by_pk.assert_not_called()  # Avoid false positives when challenge phase does not exist
        mock_run_submission.assert_not_called()

    @mock.patch("scripts.workers.remote_submission_worker.run_submission")
    @mock.patch("scripts.workers.remote_submission_worker.get_challenge_phase_by_pk")
    @mock.patch("scripts.workers.remote_submission_worker.get_challenge_by_queue_name")
    @mock.patch("scripts.workers.remote_submission_worker.extract_submission_data")
    @mock.patch("scripts.workers.remote_submission_worker.logger.exception")
    def test_process_submission_message_when_challenge_phase_does_not_exist(self,
                                                                            mock_logger,
                                                                            mock_extract_submission_data,
                                                                            mock_get_challenge_by_queue_name,
                                                                            mock_get_challenge_phase_by_pk,
                                                                            mock_run_submission):
        mock_extract_submission_data.return_value = self.submission
        mock_get_challenge_by_queue_name.return_value =  self.challenge
        mock_get_challenge_phase_by_pk.return_value = None

        with self.assertRaises(Exception):
            process_submission_message(self.message)

        mock_extract_submission_data.assert_called_with(self.submission_pk)
        mock_get_challenge_by_queue_name.assert_called()
        mock_get_challenge_phase_by_pk.assert_called_with(self.challenge_pk, self.challenge_phase_pk)
        mock_logger.assert_called_with(
            "Challenge Phase {} does not exist for queue {}".format(self.challenge_phase_pk, self.queue_name)
        )
        mock_run_submission.assert_not_called()
