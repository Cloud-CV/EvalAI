import mock
import os
import responses
import shutil
import tempfile
from io import BytesIO
from os.path import join
from unittest import TestCase
import zipfile

from scripts.workers.worker_utils import EvalAI_Interface, FileHandler


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


@mock.patch("scripts.workers.worker_utils.requests")
class MakeRequestTestClass(BaseTestClass):
    def setUp(self):
        super(MakeRequestTestClass, self).setUp()
        AUTH_TOKEN = "test_token"
        QUEUE_NAME = "test_queue"
        EVALAI_API_SERVER = "http://testserver"
        self.url = super(MakeRequestTestClass, self).make_request_url()
        self.api = EvalAI_Interface(AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME)

    def test_make_request_get(self, mock_make_request):
        self.api.make_request(self.url, "GET", data=None)
        mock_make_request.request.assert_called_with(method="GET", url=self.url, headers=self.headers, data=None)

    def test_make_request_put(self, mock_make_request):
        self.api.make_request(self.url, "PUT", data=self.data)
        mock_make_request.request.assert_called_with(method="PUT", url=self.url, headers=self.headers, data=self.data)

    def test_make_request_patch(self, mock_make_request):
        self.api.make_request(self.url, "PATCH", data=self.data)
        mock_make_request.request.assert_called_with(method="PATCH", url=self.url, headers=self.headers, data=self.data)

    def test_make_request_post(self, mock_make_request):
        self.api.make_request(self.url, "POST", data=self.data)
        mock_make_request.request.assert_called_with(method="POST", url=self.url, headers=self.headers, data=self.data)


@mock.patch.object(EvalAI_Interface, "return_url_per_environment")
@mock.patch.object(EvalAI_Interface, "make_request")
class APICallsTestClass(BaseTestClass):
    def setUp(self):
        super(APICallsTestClass, self).setUp()
        AUTH_TOKEN = "test_token"
        QUEUE_NAME = "test_submission_queue"
        EVALAI_API_SERVER = "http://testserver"
        self.api = EvalAI_Interface(AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME)

    def test_get_message_from_sqs_queue(self, mock_make_request, mock_url):
        url = self.get_message_from_sqs_queue_url("test_submission_queue")
        self.api.get_message_from_sqs_queue()
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_delete_message_from_sqs_queue(self, mock_make_request, mock_url):
        test_receipt_handle = "test_receipt_handle"
        url = self.delete_message_from_sqs_queue_url("test_submission_queue")
        self.api.delete_message_from_sqs_queue(test_receipt_handle)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        expected_data = {"receipt_handle": "test_receipt_handle"}
        mock_make_request.assert_called_with(url, "POST", expected_data)

    def test_get_challenge_by_queue_name(self, mock_make_request, mock_url):
        url = self.get_challenge_by_queue_name_url("test_submission_queue")
        self.api.get_challenge_by_queue_name()
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_submission_by_pk(self, mock_make_request, mock_url):
        self.api.get_submission_by_pk(self.submission_pk)
        url = self.get_submission_by_pk_url(self.submission_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phases_by_challenge_pk(self, mock_make_request, mock_url):
        self.api.get_challenge_phases_by_challenge_pk(self.challenge_pk)
        url = self.get_challenge_phases_by_challenge_pk_url(self.challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phase_by_pk(self, mock_make_request, mock_url):
        self.api.get_challenge_phase_by_pk(self.challenge_pk, self.challenge_phase_pk)
        url = self.get_challenge_phase_by_pk_url(self.challenge_pk, self.challenge_phase_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_update_submission_data(self, mock_make_request, mock_url):
        self.api.update_submission_data(self.data, self.challenge_pk, self.submission_pk)
        url = self.update_submission_data_url(self.challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PUT", data=self.data)

    def test_update_submission_status(self, mock_make_request, mock_url):
        self.api.update_submission_status(self.data, self.challenge_pk)
        url = self.update_submission_data_url(self.challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PATCH", data=self.data)


class URLFormatTestCase(BaseTestClass):
    def setUp(self):
        super(URLFormatTestCase, self).setUp()
        AUTH_TOKEN = "test_token"
        QUEUE_NAME = "test_submission_queue"
        EVALAI_API_SERVER = "http://testserver"
        self.api = EvalAI_Interface(AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME)

    def test_return_url_per_environment(self):
        url = "/test/url"
        expected_url = "http://testserver{}".format(url)
        returned_url = self.api.return_url_per_environment(url)
        self.assertEqual(returned_url, expected_url)


class CreateDirAsPythonPackageTest(BaseTestClass):
    def setUp(self):
        super(CreateDirAsPythonPackageTest, self).setUp()

        self.BASE_TEMP_DIR = tempfile.mkdtemp()
        self.temp_directory = join(self.BASE_TEMP_DIR, "temp_dir")
        self.file_handle = FileHandler()

    def test_create_dir_as_python_package(self):
        self.file_handle.create_dir_as_python_package(self.temp_directory)
        self.assertTrue(os.path.isfile(join(self.temp_directory, "__init__.py")))

        with open(join(self.temp_directory, "__init__.py")) as f:
            self.assertEqual(f.read(), "")

        shutil.rmtree(self.temp_directory)
        self.assertFalse(os.path.exists(self.temp_directory))


class DownloadAndExtractFileTest(BaseTestClass):
    def setUp(self):
        super(DownloadAndExtractFileTest, self).setUp()
        self.file_handle = FileHandler()
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

        self.file_handle.download_and_extract_file(self.req_url, self.download_location)

        self.assertTrue(os.path.exists(self.download_location))
        with open(self.download_location, "rb") as f:
            self.assertEqual(f.read(), self.file_content)

    @responses.activate
    @mock.patch("scripts.workers.worker_utils.logger.error")
    def test_download_and_extract_file_when_download_fails(self, mock_logger):
        error = "ExampleError: Example Error description"
        responses.add(responses.GET, self.req_url, body=Exception(error))
        expected = "Failed to fetch file from {}, error {}".format(self.req_url, error)

        self.file_handle.download_and_extract_file(self.req_url, self.download_location)

        mock_logger.assert_called_with(expected)
        self.assertFalse(os.path.exists(self.download_location))


class DownloadAndExtractZipFileTest(BaseTestClass):
    def setUp(self):
        super(DownloadAndExtractZipFileTest, self).setUp()
        self.zip_name = "test"
        self.BASE_TEMP_DIR = tempfile.mkdtemp()
        self.SUBMISSION_DATA_DIR = join(
            self.BASE_TEMP_DIR, "compute/submission_files/submission_{submission_id}"
        )
        self.temp_directory = join(self.BASE_TEMP_DIR, "temp_dir")
        self.req_url = "{}/{}".format(self.testserver, self.zip_name)
        self.extract_location = join(self.BASE_TEMP_DIR, "test-dir")
        self.download_location = join(self.extract_location, "{}.zip".format(self.zip_name))
        self.file_handle = FileHandler()
        self.file_handle.create_dir(self.extract_location)

        self.file_name = "test_file.txt"
        self.file_content = b"file_content"

        self.zip_file = BytesIO()
        with zipfile.ZipFile(self.zip_file, mode="w", compression=zipfile.ZIP_DEFLATED) as zipper:
            zipper.writestr(self.file_name, self.file_content)

    def tearDown(self):
        if os.path.exists(self.extract_location):
            shutil.rmtree(self.extract_location)

    @responses.activate
    @mock.patch.object(FileHandler, "delete_zip_file")
    @mock.patch.object(FileHandler, "extract_zip_file")
    def test_download_and_extract_zip_file_success(self, mock_extract_zip, mock_delete_zip):
        responses.add(
            responses.GET, self.req_url,
            content_type="application/zip",
            body=self.zip_file.getvalue(), status=200)

        self.file_handle.download_and_extract_zip_file(self.req_url, self.download_location, self.extract_location)

        with open(self.download_location, "rb") as downloaded:
            self.assertEqual(downloaded.read(), self.zip_file.getvalue())
        mock_extract_zip.assert_called_with(self.download_location, self.extract_location)
        mock_delete_zip.assert_called_with(self.download_location)

    @responses.activate
    @mock.patch("scripts.workers.worker_utils.logger.error")
    def test_download_and_extract_zip_file_when_download_fails(self, mock_logger):
        e = "Error description"
        responses.add(
            responses.GET, self.req_url,
            body=Exception(e))
        error_message = "Failed to fetch file from {}, error {}".format(self.req_url, e)

        self.file_handle.download_and_extract_zip_file(self.req_url, self.download_location, self.extract_location)

        mock_logger.assert_called_with(error_message)

    def test_extract_zip_file(self):
        with open(self.download_location, "wb") as zf:
            zf.write(self.zip_file.getvalue())

        self.file_handle.extract_zip_file(self.download_location, self.extract_location)
        extracted_path = join(self.extract_location, self.file_name)
        self.assertTrue(os.path.exists(extracted_path))
        with open(extracted_path, "rb") as extracted:
            self.assertEqual(extracted.read(), self.file_content)

    def test_delete_zip_file(self):
        with open(self.download_location, "wb") as zf:
            zf.write(self.zip_file.getvalue())

        self.file_handle.delete_zip_file(self.download_location)

        self.assertFalse(os.path.exists(self.download_location))

    @mock.patch("scripts.workers.worker_utils.logger.error")
    @mock.patch("scripts.workers.worker_utils.os.remove")
    def test_delete_zip_file_error(self, mock_remove, mock_logger):
        e = "Error description"
        mock_remove.side_effect = Exception(e)
        error_message = "Failed to remove zip file {}, error {}".format(self.download_location, e)

        self.file_handle.delete_zip_file(self.download_location)
        mock_logger.assert_called_with(error_message)


class CreateDirectoryTests(BaseTestClass):
    def setUp(self):
        super(CreateDirectoryTests, self).setUp()
        self.BASE_TEMP_DIR = tempfile.mkdtemp()
        self.temp_directory = join(self.BASE_TEMP_DIR, "temp_dir")
        self.file_handle = FileHandler()

    def tearDown(self):
        if os.path.exists(self.temp_directory):
            shutil.rmtree(self.temp_directory)

    def test_create_dir(self):
        self.file_handle.create_dir(self.temp_directory)
        self.assertTrue(os.path.isdir(self.temp_directory))
        shutil.rmtree(self.temp_directory)

    def test_create_dir_as_python_package(self):
        self.file_handle.create_dir_as_python_package(self.temp_directory)
        self.assertTrue(os.path.isfile(join(self.temp_directory, "__init__.py")))
        shutil.rmtree(self.temp_directory)
