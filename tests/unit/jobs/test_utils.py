import os
import responses
import shutil
import tempfile

from unittest import mock
from unittest import TestCase

from jobs.utils import is_url_valid, get_file_from_url


class BaseTestClass(TestCase):
    def setUp(self):
        self.reachable_url = "http://httpstat.us/200"
        self.unreachable_url = "http://httpstat.us/404"
        self.file_url = "https://gist.githubusercontent.com/nikochiko/8572a636ed5049e658a5fe999eb6d031/raw/31edd0a6bf4c03392153294f178f33f38ad3737f/dummy"


class IsUrlValidTestClass(BaseTestClass):
    def setUp(self):
        super(IsUrlValidTestClass, self).setUp()

        responses.add(responses.HEAD,
                      self.reachable_url,
                      status=200)

        responses.add(responses.HEAD,
                      self.unreachable_url,
                      status=404)

    @responses.activate
    def test_is_url_valid_when_url_is_reachable(self):
        self.assertTrue(is_url_valid(self.reachable_url))

    @responses.activate
    def test_is_url_valid_when_url_is_unreachable(self):
        self.assertFalse(is_url_valid(self.unreachable_url))


class GetFileFromUrlTestClass(BaseTestClass):
    def setUp(self):
        super(GetFileFromUrlTestClass, self).setUp()

        self.temp_dir = tempfile.mkdtemp()
        self.file_name = "dummy"
        self.file_content = "Dummy File Content"

        responses.add(responses.GET, self.file_url,
                      body=self.file_content,
                      content_type="application/octet-stream")

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    @responses.activate
    @mock.patch("jobs.utils.tempfile.mkdtemp")
    def test_get_file_from_url(self, mock_tempdir):
        mock_tempdir.return_value = self.temp_dir
        file_path = os.path.join(self.temp_dir, self.file_name)

        expected = {"name": self.file_name, "temp_dir_path": self.temp_dir}
        file_obj = get_file_from_url(self.test_url)

        self.assertEqual(file_obj, expected)
        self.assertTrue(os.path.exists(file_path))

        with open(file_path, "rb") as f:
            self.assertEqual(f.read(), self.file_content)
