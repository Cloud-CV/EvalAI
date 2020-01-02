import os
import responses
import shutil
import tempfile

from unittest import mock
from unittest import TestCase

from jobs.utils import is_url_valid, get_file_from_url


class BaseTestClass(TestCase):
    def setUp(self):
        self.testserver = "http://testserver"


class IsUrlValidTestClass(TestCase):
    def setUp(self):
        super(IsUrlValidTestClass, self).setUp()

        self.reachable_url = "{0}{1}".format(self.testserver, "/test/reachable")
        self.unreachable_test_url = "{0}{1}".format(self.testserver, "/test/unreachable")

        responses.add(responses.HEAD,
                      self.reachable_url,
                      status=200)

        responses.add(responses.HEAD,
                      self.unreachable_test_url,
                      status=404)

    @responses.activate
    def test_is_url_valid_when_url_is_reachable(self):
        self.assertTrue(is_url_valid(self.test_url))

    @responses.activate
    def test_is_url_valid_when_url_is_unreachable(self):
        self.assertFalse(is_url_valid(self.unreachable_url))


class GetFileFromUrlTestClass(TestCase):
    def setUp(self):
        super(GetFileFromUrlTestClass, self).setUp()

        self.temp_dir = tempfile.mkdtemp()
        self.filename = "dummy_file"
        self.file_url = "{0}{1}".format(self.testserver, self.filename)
        self.file_content = b'file_content'

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
        filepath = os.path.join(self.temp_dir, self.file_name)

        expected = {"name": self.filename, "temp_dir_path": self.temp_dir}
        file_obj = get_file_from_url(self.test_url)

        self.assertEqual(file_obj, expected)
        self.assertTrue(os.path.exists(filepath))

        with open(filepath, "rb") as f:
            self.assertEqual(f.read(), self.file_content)
