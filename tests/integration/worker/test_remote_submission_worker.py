import mock
import responses
import shutil
import unittest

import scripts.workers.remote_submission_worker as remote_submission_worker


@mock.patch("scripts.workers.remote_submission_worker.logger.error")
class TestDownloadAndExtractFile(unittest.TestCase):
    def setUp(self):
        self.download_dir = "/tmp/evalai/"
        self.download_filename = "file"
        self.download_path = "{}{}".format(self.download_dir, self.download_filename)

        self.url = "http://example.com"
        self.body = """{"content": "test-data"}"""
        responses.add(
            responses.GET,
            self.url,
            body=self.body,
            status=200
        )

        remote_submission_worker.create_dir(self.download_dir)

    def tearDown(self):
        shutil.rmtree(self.download_dir)

    @responses.activate
    def test_download_and_extract_file_with_correct_url(self, mock_logger):
        mock_logger.assert_not_called()

        remote_submission_worker.download_and_extract_file(self.url, self.download_path)
        with open(self.download_path, "r") as f:
            assert f.read() == self.body

    def test_download_and_extract_file_with_incorrect_url(self, mock_logger):
        mock_logger.assert_not_called()

        self.url = "invalid-url"

        remote_submission_worker.download_and_extract_file(self.url, "")
        mock_logger.assert_called_with(
            "Failed to fetch file from {}, error "
            "Invalid URL 'invalid-url': No schema supplied. Perhaps you meant http://invalid-url?".format(self.url)
        )
