import os
import unittest

from django.conf import settings

from challenges.utils import get_file_content


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.test_file_path = os.path.join(settings.BASE_DIR, 'examples', 'EvalAI-Starters',
                                           'annotations/test_annotations_devsplit.json')

    def test_get_file_content(self):
        test_file_content = get_file_content(self.test_file_path, 'rb')
        expected = '{\n\t"foo": "bar"\n}'
        self.assertEqual(test_file_content.decode(), expected)
