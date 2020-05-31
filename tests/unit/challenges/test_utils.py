import os
import unittest
import random
import string

from django.conf import settings

from challenges.utils import get_file_content
from base.utils import get_queue_name


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.test_file_path = os.path.join(
            settings.BASE_DIR, "examples", "example1", "test_annotation.txt"
        )
        self.sqs_valid_characters = string.ascii_lowercase + \
            string.ascii_uppercase + string.digits + '-' + '_'

    def test_get_file_content(self):
        test_file_content = get_file_content(self.test_file_path, "rb")
        expected = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n"
        self.assertEqual(test_file_content.decode(), expected)

    def test_sqs_queue_name_generator_long_title(self):
        title = ''.join([random.choice(self.sqs_valid_characters)
                         for i in range(256)])
        sqs_queue_name = get_queue_name(title)
        self.assertNotRegex(sqs_queue_name, "[^a-zA-Z0-9_-]")
        self.assertLessEqual(len(sqs_queue_name), 80)

    def test_sqs_queue_name_generator_title_has_special_char(self):
        title = ''.join([random.choice(string.printable) for i in range(80)])
        sqs_queue_name = get_queue_name(title)
        self.assertNotRegex(sqs_queue_name, "[^a-zA-Z0-9_-]")
        self.assertLessEqual(len(sqs_queue_name), 80)

    def test_sqs_queue_name_generator_title_has_special_char_and_long_title(self):
        title = ''.join([random.choice(string.printable) for i in range(256)])
        sqs_queue_name = get_queue_name(title)
        self.assertNotRegex(sqs_queue_name, "[^a-zA-Z0-9_-]")
        self.assertLessEqual(len(sqs_queue_name), 80)

    def test_sqs_queue_name_generator_empty_title(self):
        title = ""
        sqs_queue_name = get_queue_name(title)
        self.assertNotRegex(sqs_queue_name, "[^a-zA-Z0-9_-]")
        self.assertLessEqual(len(sqs_queue_name), 80)
