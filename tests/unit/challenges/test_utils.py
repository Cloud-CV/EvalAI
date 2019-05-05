import os
import unittest

from django.conf import settings

from challenges.utils import get_file_content


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.test_file_path = os.path.join(
            settings.BASE_DIR, "examples", "example1", "test_annotation.txt"
        )

    def test_get_file_content(self):
        test_file_content = get_file_content(self.test_file_path, "rb")
        expected = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n"
        self.assertEqual(test_file_content.decode(), expected)
