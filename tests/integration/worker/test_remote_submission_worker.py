import responses
import mock
import os
import unittest

import scripts.workers.remote_submission_worker as remote_submission_worker


class BaseTestClass(unittest.TestCase):
    def setUp(self):
        self.download_dir = "/tmp/evalai/"
        self.download_filename = "file"
        self.download_path = "{}{}".format(self.download_dir, self.download_filename)

        try:
            os.makedirs(self.download_dir)
        except OSError:
            pass


class DownloadAndExtractFileWithProperURL(BaseTestClass):
    def setUp(self):
        super().setUp()

        self.url = "http://example.com"
        self.body = """{"content": "test-data"}"""
        responses.add(
            responses.GET,
            self.url,
            body=self.body,
            status=200
        )

    @responses.activate
    def test_download_and_extract_file_when_proper_url_is_given(self):
        remote_submission_worker.download_and_extract_file(self.url, self.download_path)

        with open(self.download_path, "r") as f:
            assert f.read() == self.body


class DownloadAndExtractFileTestClass(BaseTestClass):
    def setUp(self):
        super().setUp()

        self.url = "invalid-url"

    @mock.patch("scripts.workers.remote_submission_worker.logger.error")
    def test_download_and_extract_file_when_improper_url_is_given(self, mock_logger):
        remote_submission_worker.download_and_extract_file(self.url, "")
        mock_logger.assert_called_with(
            "Failed to fetch file from {}, error "
            "Invalid URL 'invalid-url': No schema supplied. Perhaps you meant http://invalid-url?".format(self.url)
        )
