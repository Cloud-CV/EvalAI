import mock
import os
import responses
import unittest

import scripts.workers.remote_submission_worker as remote_submission_worker


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

        try:
            os.makedirs(self.download_dir)
        except OSError:
            pass

    @responses.activate
    def test_download_and_extract_file_with_correct_url(self):
        remote_submission_worker.download_and_extract_file(self.url, self.download_path)

        with open(self.download_path, "r") as f:
            assert f.read() == self.body

    @mock.patch("scripts.workers.remote_submission_worker.logger.error")
    def test_download_and_extract_file_with_incorrect_url(self, mock_logger):
        self.url = "invalid-url"

        remote_submission_worker.download_and_extract_file(self.url, "")
        mock_logger.assert_called_with(
            "Failed to fetch file from {}, error "
            "Invalid URL 'invalid-url': No schema supplied. Perhaps you meant http://invalid-url?".format(self.url)
        )
