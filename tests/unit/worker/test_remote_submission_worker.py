import io
import logging
import os
import signal
import sys
import unittest
from unittest.mock import MagicMock, Mock, mock_open, patch

import requests

import scripts.workers.remote_submission_worker as worker_mod
from scripts.workers.remote_submission_worker import (
    CHALLENGE_DATA_BASE_DIR,
    SUBMISSION_DATA_DIR,
    SUBMISSION_INPUT_FILE_PATH,
    ExecutionTimeLimitExceeded,
    GracefulKiller,
    alarm_handler,
    download_and_extract_zip_file,
    extract_challenge_data,
    extract_submission_data,
    load_challenge,
    make_request,
    process_submission_message,
    read_file_content,
    run_submission,
    stderr_redirect,
    stdout_redirect,
)

logger = logging.getLogger()


class TestGracefulKiller(unittest.TestCase):
    def test_initial_state(self):
        killer = GracefulKiller()
        self.assertFalse(killer.kill_now, "kill_now should be False initially")

    def test_exit_gracefully(self):
        killer = GracefulKiller()
        killer.exit_gracefully(signum=signal.SIGINT, frame=None)
        self.assertTrue(
            killer.kill_now, "kill_now should be True after signal is received"
        )

    def test_signal_handlers(self):
        killer = GracefulKiller()
        self.assertEqual(
            signal.getsignal(signal.SIGINT), killer.exit_gracefully
        )
        self.assertEqual(
            signal.getsignal(signal.SIGTERM), killer.exit_gracefully
        )


class TestContextManagers(unittest.TestCase):
    def test_stdout_redirect(self):
        with io.StringIO() as buf, stdout_redirect(buf):
            print("Hello, World!")
            self.assertEqual(buf.getvalue(), "Hello, World!\n")

    def test_stderr_redirect(self):
        with io.StringIO() as buf, stderr_redirect(buf):
            print("Error!", file=sys.stderr)
            self.assertEqual(buf.getvalue(), "Error!\n")


class TestAlarmHandler(unittest.TestCase):
    def test_alarm_handler(self):
        with self.assertRaises(ExecutionTimeLimitExceeded):
            alarm_handler(signum=signal.SIGALRM, frame=None)


class TestDownloadAndExtractZipFile(unittest.TestCase):
    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("zipfile.ZipFile")
    @patch("os.remove")
    def test_successful_download_and_extraction(
        self, mock_remove, mock_zipfile, mock_open, mock_get
    ):
        # Simulate a successful file download
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"Test content"

        download_and_extract_zip_file(
            "http://example.com/test.zip",
            "/path/to/download.zip",
            "/path/to/extract/",
        )

        mock_open.assert_called_once_with("/path/to/download.zip", "wb")
        mock_open().write.assert_called_once_with(b"Test content")
        mock_zipfile.assert_called_once_with("/path/to/download.zip", "r")
        mock_zipfile().extractall.assert_called_once_with("/path/to/extract/")
        mock_remove.assert_called_once_with("/path/to/download.zip")

    @patch("requests.get")
    @patch("os.remove")
    def test_download_failure(self, mock_remove, mock_get):
        # Simulate a failed file download
        mock_get.side_effect = Exception("Network error")

        with self.assertLogs(logger, level="ERROR") as log:
            download_and_extract_zip_file(
                "http://example.com/test.zip",
                "/path/to/download.zip",
                "/path/to/extract/",
            )
            self.assertIn(
                "Failed to fetch file from http://example.com/test.zip, error Network error",
                log.output[0],
            )

        mock_remove.assert_not_called()

    @patch("requests.get")
    @patch("builtins.open", new_callable=mock_open)
    @patch("zipfile.ZipFile")
    @patch("os.remove")
    def test_file_removal_failure(
        self, mock_remove, mock_zipfile, mock_open, mock_get
    ):
        # Simulate a successful file download and extraction, but removal fails
        mock_get.return_value.status_code = 200
        mock_get.return_value.content = b"Test content"
        mock_remove.side_effect = Exception("File removal error")

        with self.assertLogs(logger, level="ERROR") as log:
            download_and_extract_zip_file(
                "http://example.com/test.zip",
                "/path/to/download.zip",
                "/path/to/extract/",
            )
            self.assertIn(
                "Failed to remove zip file /path/to/download.zip, error File removal error",
                log.output[0],
            )

        mock_open().write.assert_called_once_with(b"Test content")
        mock_zipfile().extractall.assert_called_once_with("/path/to/extract/")


class TestLoadChallenge(unittest.TestCase):
    @patch(
        "scripts.workers.remote_submission_worker.get_challenge_by_queue_name"
    )
    @patch(
        "scripts.workers.remote_submission_worker.get_challenge_phases_by_challenge_pk"
    )
    @patch("scripts.workers.remote_submission_worker.extract_challenge_data")
    @patch(
        "scripts.workers.remote_submission_worker.create_dir_as_python_package"
    )
    def test_successful_load_challenge(
        self,
        mock_create_dir,
        mock_extract_data,
        mock_get_phases,
        mock_get_challenge,
    ):
        # Mock the challenge and phases data
        mock_challenge = {
            "id": 1,
            "evaluation_script": "http://example.com/evaluation_script.zip",
        }
        mock_get_challenge.return_value = mock_challenge
        mock_get_phases.return_value = [
            {"id": 1, "test_annotation": "http://example.com/annotation.txt"}
        ]

        load_challenge()

        mock_create_dir.assert_called_once_with(CHALLENGE_DATA_BASE_DIR)
        mock_get_challenge.assert_called_once()
        mock_get_phases.assert_called_once_with(1)
        mock_extract_data.assert_called_once_with(
            mock_challenge, mock_get_phases.return_value
        )

    @patch(
        "scripts.workers.remote_submission_worker.get_challenge_by_queue_name"
    )
    @patch(
        "scripts.workers.remote_submission_worker.create_dir_as_python_package"
    )
    def test_load_challenge_exception(
        self, mock_create_dir, mock_get_challenge
    ):
        # Simulate an exception when fetching the challenge
        mock_get_challenge.side_effect = Exception("Challenge not found")

        with self.assertLogs(logger, level="ERROR") as log:
            with self.assertRaises(Exception):
                load_challenge()
            self.assertIn("Challenge with queue name", log.output[0])

        mock_create_dir.assert_called_once_with(CHALLENGE_DATA_BASE_DIR)


class TestExtractChallengeData(unittest.TestCase):
    @patch(
        "scripts.workers.remote_submission_worker.download_and_extract_file"
    )
    @patch("scripts.workers.remote_submission_worker.importlib.import_module")
    @patch("scripts.workers.remote_submission_worker.create_dir")
    @patch(
        "scripts.workers.remote_submission_worker.create_dir_as_python_package"
    )
    @patch(
        "scripts.workers.remote_submission_worker.download_and_extract_zip_file"
    )
    def test_extract_challenge_data_import_exception(
        self,
        mock_download_zip,
        mock_create_dir_as_pkg,
        mock_create_dir,
        mock_import_module,
        mock_download_file,
    ):
        # Mock the challenge and phases data
        mock_challenge = {
            "id": 1,
            "evaluation_script": "http://example.com/evaluation_script.zip",
        }
        mock_phases = [
            {"id": 1, "test_annotation": "http://example.com/annotation.txt"}
        ]

        # Mock the download functions to prevent actual HTTP requests
        mock_download_zip.return_value = None
        mock_download_file.return_value = None

        # Simulate an exception during import
        mock_import_module.side_effect = ImportError("Import failed")

        with self.assertLogs(logger, level="ERROR") as log:
            with self.assertRaises(ImportError):
                extract_challenge_data(mock_challenge, mock_phases)
            self.assertIn(
                "Exception raised while creating Python module for challenge_id: 1",
                log.output[0],
            )

        mock_create_dir_as_pkg.assert_called_once_with(
            os.path.join(CHALLENGE_DATA_BASE_DIR, "challenge_1")
        )

        mock_download_zip.assert_called_once()
        mock_download_file.assert_called_once()

    @patch(
        "scripts.workers.remote_submission_worker.download_and_extract_file"
    )
    @patch(
        "scripts.workers.remote_submission_worker.download_and_extract_zip_file"
    )
    @patch("scripts.workers.remote_submission_worker.importlib.import_module")
    @patch("scripts.workers.remote_submission_worker.create_dir")
    @patch(
        "scripts.workers.remote_submission_worker.create_dir_as_python_package"
    )
    def test_successful_extract_challenge_data(
        self,
        mock_create_dir_as_pkg,
        mock_create_dir,
        mock_import_module,
        mock_download_zip,
        mock_download_file,
    ):
        # Mock the challenge and phases data
        mock_challenge = {
            "id": 1,
            "evaluation_script": "http://example.com/evaluation_script.zip",
        }
        mock_phases = [
            {"id": 1, "test_annotation": "http://example.com/annotation.txt"}
        ]

        extract_challenge_data(mock_challenge, mock_phases)

        mock_create_dir_as_pkg.assert_called_once_with(
            os.path.join(CHALLENGE_DATA_BASE_DIR, "challenge_1")
        )

        mock_download_file.assert_called_once()
        mock_download_zip.assert_called_once()
        mock_import_module.assert_called_once()

    @patch(
        "scripts.workers.remote_submission_worker.get_challenge_by_queue_name"
    )
    @patch(
        "scripts.workers.remote_submission_worker.get_challenge_phase_by_pk"
    )
    @patch("scripts.workers.remote_submission_worker.extract_submission_data")
    @patch("scripts.workers.remote_submission_worker.run_submission")
    def test_process_submission_message_success(
        self,
        mock_run_submission,
        mock_extract_submission_data,
        mock_get_challenge_phase_by_pk,
        mock_get_challenge_by_queue_name,
    ):
        # Mock data
        mock_message = {"challenge_pk": 1, "phase_pk": 2, "submission_pk": 3}
        mock_submission_instance = {"input_file": "file.txt"}
        mock_challenge = {"remote_evaluation": True}
        mock_challenge_phase = Mock()

        # Mocking return values
        mock_extract_submission_data.return_value = mock_submission_instance
        mock_get_challenge_by_queue_name.return_value = mock_challenge
        mock_get_challenge_phase_by_pk.return_value = mock_challenge_phase

        # Call the function
        process_submission_message(mock_message)

        # Assertions to ensure all functions are called with correct parameters
        mock_extract_submission_data.assert_called_once_with(3)
        mock_get_challenge_by_queue_name.assert_called_once()
        mock_get_challenge_phase_by_pk.assert_called_once_with(1, 2)
        mock_run_submission.assert_called_once()  # Removed the incorrect assertion

    @patch("scripts.workers.remote_submission_worker.extract_submission_data")
    def test_process_submission_message_no_submission_instance(
        self, mock_extract_submission_data
    ):
        # Mock data
        mock_message = {"challenge_pk": 1, "phase_pk": 2, "submission_pk": 3}

        # Mocking return values
        mock_extract_submission_data.return_value = None

        # Call the function and expect it to return early
        result = process_submission_message(mock_message)
        self.assertIsNone(result)
        mock_extract_submission_data.assert_called_once_with(3)

    @patch("scripts.workers.remote_submission_worker.requests.get")
    @patch("scripts.workers.remote_submission_worker.get_request_headers")
    @patch("scripts.workers.remote_submission_worker.logger")
    def test_make_request_get_exception(
        self, mock_logger, mock_get_request_headers, mock_requests_get
    ):
        # Mock data
        url = "http://example.com"
        method = "GET"

        # Mock the request to raise an exception
        mock_requests_get.side_effect = requests.exceptions.RequestException(
            "Connection error"
        )

        # Ensure logger.info is called and exception is raised
        with self.assertRaises(requests.exceptions.RequestException):
            make_request(url, method)

        # Check if logger.info was called
        mock_logger.info.assert_called_once_with(
            "The worker is not able to establish connection with EvalAI"
        )

    @patch("scripts.workers.remote_submission_worker.requests.patch")
    @patch("scripts.workers.remote_submission_worker.get_request_headers")
    @patch("scripts.workers.remote_submission_worker.logger")
    def test_make_request_patch_request_exception(
        self, mock_logger, mock_get_request_headers, mock_requests_patch
    ):
        # Mock data
        url = "http://example.com"
        method = "PATCH"
        data = {"key": "value"}

        # Mock the request to raise an exception
        mock_requests_patch.side_effect = requests.exceptions.RequestException(
            "Connection error"
        )

        # Ensure logger.info is called and exception is raised
        with self.assertRaises(requests.exceptions.RequestException):
            make_request(url, method, data=data)

        # Check if logger.info was called
        mock_logger.info.assert_called_once_with(
            "The worker is not able to establish connection with EvalAI"
        )

    @patch("scripts.workers.remote_submission_worker.requests.post")
    @patch("scripts.workers.remote_submission_worker.get_request_headers")
    @patch("scripts.workers.remote_submission_worker.logger")
    def test_make_request_post_request_exception(
        self, mock_logger, mock_get_request_headers, mock_requests_post
    ):
        # Mock data
        url = "http://example.com"
        method = "POST"
        data = {"key": "value"}

        # Mock the request to raise an exception
        mock_requests_post.side_effect = requests.exceptions.RequestException(
            "Connection error"
        )

        # Ensure logger.info is called and exception is raised
        with self.assertRaises(requests.exceptions.RequestException):
            make_request(url, method, data=data)

        # Check if logger.info was called
        mock_logger.info.assert_called_once_with(
            "The worker is not able to establish connection with EvalAI"
        )

    @patch("builtins.open", new_callable=mock_open, read_data="some content")
    def test_read_file_content_normal(self, mock_open):
        # Test reading a file with some content
        file_path = "test_file.txt"
        result = read_file_content(file_path)
        self.assertEqual(result, "some content")
        mock_open.assert_called_once_with(file_path, "r")

    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_read_file_content_empty(self, mock_open):
        # Test reading an empty file
        file_path = "test_empty_file.txt"
        result = read_file_content(file_path)
        self.assertEqual(result, " ")
        mock_open.assert_called_once_with(file_path, "r")

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_read_file_content_file_not_found(self, mock_open):
        # Test reading a file that does not exist
        file_path = "non_existent_file.txt"
        with self.assertRaises(FileNotFoundError):
            read_file_content(file_path)


class TestExtractSubmissionDataNoSubmission(unittest.TestCase):
    @patch("scripts.workers.remote_submission_worker.get_submission_by_pk")
    @patch("scripts.workers.remote_submission_worker.logger")
    @patch("scripts.workers.remote_submission_worker.traceback")
    def test_extract_submission_data_no_submission(
        self, mock_traceback, mock_logger, mock_get_submission_by_pk
    ):
        mock_get_submission_by_pk.return_value = None

        result = extract_submission_data(123)

        mock_logger.critical.assert_called_once_with(
            "Submission {} does not exist".format(123)
        )
        mock_traceback.print_exc.assert_called_once()
        assert result is None


class TestExtractSubmissionDataHappyPath(unittest.TestCase):
    @patch(
        "scripts.workers.remote_submission_worker.download_and_extract_file"
    )
    @patch(
        "scripts.workers.remote_submission_worker.create_dir_as_python_package"
    )
    @patch("scripts.workers.remote_submission_worker.get_submission_by_pk")
    def test_extract_submission_data_happy_path(
        self, mock_get_submission_by_pk, mock_create_dir, mock_download_file
    ):
        submission = {"id": 42, "input_file": "/tmp/input.txt"}
        mock_get_submission_by_pk.return_value = submission

        result = extract_submission_data(42)

        submission_data_directory = SUBMISSION_DATA_DIR.format(
            submission_id=42
        )
        submission_input_file_name = os.path.basename("/tmp/input.txt")
        submission_input_file_path = SUBMISSION_INPUT_FILE_PATH.format(
            submission_id=42, input_file=submission_input_file_name
        )

        mock_create_dir.assert_called_once_with(submission_data_directory)
        mock_download_file.assert_called_once_with(
            "/tmp/input.txt", submission_input_file_path
        )
        assert result == submission


class TestMakeRequestExceptions(unittest.TestCase):
    @patch("scripts.workers.remote_submission_worker.logger")
    @patch("scripts.workers.remote_submission_worker.requests.put")
    def test_make_request_put_request_exception(self, mock_put, mock_logger):
        mock_put.side_effect = requests.exceptions.RequestException()
        with self.assertRaises(UnboundLocalError):
            make_request("http://test-url", "PUT", data={})

    @patch("scripts.workers.remote_submission_worker.logger")
    @patch("scripts.workers.remote_submission_worker.requests.put")
    def test_make_request_put_http_error(self, mock_put, mock_logger):
        mock_put.side_effect = requests.exceptions.HTTPError()
        with self.assertRaises(UnboundLocalError):
            make_request("http://test-url", "PUT", data={})


class TestMakeRequestPatchHttpError(unittest.TestCase):
    @patch("scripts.workers.remote_submission_worker.logger")
    @patch("scripts.workers.remote_submission_worker.requests.patch")
    def test_make_request_patch_http_error(self, mock_patch, mock_logger):
        mock_patch.side_effect = requests.exceptions.HTTPError()
        with self.assertRaises(requests.exceptions.HTTPError):
            make_request("http://test-url", "PATCH", data={})


class TestRunSubmission(unittest.TestCase):
    @patch("scripts.workers.remote_submission_worker.read_file_content")
    @patch("scripts.workers.remote_submission_worker.update_submission_data")
    @patch("scripts.workers.remote_submission_worker.update_submission_status")
    @patch("scripts.workers.remote_submission_worker.create_dir")
    @patch(
        "scripts.workers.remote_submission_worker.open", new_callable=mock_open
    )
    @patch(
        "scripts.workers.remote_submission_worker.EVALUATION_SCRIPTS",
        new_callable=dict,
    )
    @patch("scripts.workers.remote_submission_worker.shutil.rmtree")
    def test_run_submission_success(
        self,
        mock_rmtree,
        mock_evaluation_scripts,
        mock_open_func,
        mock_create_dir,
        mock_update_status,
        mock_update_data,
        mock_read_file_content,
    ):
        # Setup
        challenge_pk = 1
        phase_pk = 2
        submission_pk = 3
        challenge_phase = {"id": phase_pk, "codename": "phase-code"}
        submission = {"id": submission_pk}
        user_annotation_file_path = "/tmp/user.txt"
        remote_evaluation = False

        worker_mod.PHASE_ANNOTATION_FILE_NAME_MAP[challenge_pk] = {
            phase_pk: "ann.txt"
        }
        mock_eval = MagicMock()
        mock_eval.evaluate.return_value = {
            "result": [1, 2, 3],
            "submission_metadata": {"foo": "bar"},
        }
        worker_mod.EVALUATION_SCRIPTS[challenge_pk] = mock_eval

        mock_read_file_content.return_value = "file content"

        # Act
        run_submission(
            challenge_pk,
            challenge_phase,
            submission,
            user_annotation_file_path,
            remote_evaluation,
        )

        mock_update_status.assert_called()
        mock_update_data.assert_called()
        mock_rmtree.assert_called()

    @patch("scripts.workers.remote_submission_worker.read_file_content")
    @patch("scripts.workers.remote_submission_worker.update_submission_data")
    @patch("scripts.workers.remote_submission_worker.update_submission_status")
    @patch("scripts.workers.remote_submission_worker.create_dir")
    @patch(
        "scripts.workers.remote_submission_worker.open", new_callable=mock_open
    )
    @patch(
        "scripts.workers.remote_submission_worker.EVALUATION_SCRIPTS",
        new_callable=dict,
    )
    @patch("scripts.workers.remote_submission_worker.shutil.rmtree")
    def test_run_submission_no_result(
        self,
        mock_rmtree,
        mock_evaluation_scripts,
        mock_open_func,
        mock_create_dir,
        mock_update_status,
        mock_update_data,
        mock_read_file_content,
    ):
        challenge_pk = 1
        phase_pk = 2
        submission_pk = 3
        challenge_phase = {"id": phase_pk, "codename": "phase-code"}
        submission = {"id": submission_pk}
        user_annotation_file_path = "/tmp/user.txt"
        remote_evaluation = False

        worker_mod.PHASE_ANNOTATION_FILE_NAME_MAP[challenge_pk] = {
            phase_pk: "ann.txt"
        }
        mock_eval = MagicMock()
        mock_eval.evaluate.return_value = {"foo": "bar"}
        worker_mod.EVALUATION_SCRIPTS[challenge_pk] = mock_eval

        mock_read_file_content.return_value = "file content"

        run_submission(
            challenge_pk,
            challenge_phase,
            submission,
            user_annotation_file_path,
            remote_evaluation,
        )

        mock_update_status.assert_called()
        mock_update_data.assert_called()
        mock_rmtree.assert_called()

    @patch("scripts.workers.remote_submission_worker.read_file_content")
    @patch("scripts.workers.remote_submission_worker.update_submission_data")
    @patch("scripts.workers.remote_submission_worker.update_submission_status")
    @patch("scripts.workers.remote_submission_worker.create_dir")
    @patch(
        "scripts.workers.remote_submission_worker.open", new_callable=mock_open
    )
    @patch(
        "scripts.workers.remote_submission_worker.EVALUATION_SCRIPTS",
        new_callable=dict,
    )
    @patch("scripts.workers.remote_submission_worker.shutil.rmtree")
    def test_run_submission_exception(
        self,
        mock_rmtree,
        mock_evaluation_scripts,
        mock_open_func,
        mock_create_dir,
        mock_update_status,
        mock_update_data,
        mock_read_file_content,
    ):
        challenge_pk = 1
        phase_pk = 2
        submission_pk = 3
        challenge_phase = {"id": phase_pk, "codename": "phase-code"}
        submission = {"id": submission_pk}
        user_annotation_file_path = "/tmp/user.txt"
        remote_evaluation = False

        import scripts.workers.remote_submission_worker as worker_mod

        worker_mod.PHASE_ANNOTATION_FILE_NAME_MAP[challenge_pk] = {
            phase_pk: "ann.txt"
        }
        mock_eval = MagicMock()
        mock_eval.evaluate.side_effect = Exception("Eval failed")
        worker_mod.EVALUATION_SCRIPTS[challenge_pk] = mock_eval

        mock_read_file_content.return_value = "file content"

        run_submission(
            challenge_pk,
            challenge_phase,
            submission,
            user_annotation_file_path,
            remote_evaluation,
        )

        mock_update_status.assert_called()
        mock_update_data.assert_called()
        mock_rmtree.assert_called()
