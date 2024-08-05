from django.test import TestCase
from base.apps import BaseConfig


class BaseConfigTest(TestCase):
    def test_base_config(self):
        self.assertEqual(BaseConfig.name, "base")
