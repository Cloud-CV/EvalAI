from base.apps import BaseConfig
from django.test import TestCase


class BaseConfigTest(TestCase):
    def test_base_config(self):
        self.assertEqual(BaseConfig.name, "base")
