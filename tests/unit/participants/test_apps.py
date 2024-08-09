import unittest
from django.apps import apps
from participants.apps import ParticipantsConfig


class TestParticipantsConfig(unittest.TestCase):
    def test_apps(self):
        self.assertEqual(ParticipantsConfig.name, "participants")
        self.assertEqual(apps.get_app_config("participants").name, "participants")
