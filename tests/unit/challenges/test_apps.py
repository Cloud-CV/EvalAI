from challenges.apps import ChallengesConfig
from django.apps import apps
from django.test import TestCase


class ChallengesConfigTest(TestCase):
    def test_app_name(self):
        self.assertEqual(ChallengesConfig.name, "challenges")

    def test_app_config(self):
        app_config = apps.get_app_config("challenges")
        self.assertEqual(app_config.name, "challenges")
