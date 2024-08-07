import unittest
from django.apps import apps
from web.apps import WebConfig


class TestWebConfig(unittest.TestCase):
    def test_apps(self):
        self.assertEqual(WebConfig.name, "web")
        self.assertEqual(apps.get_app_config("web").name, "web")

if __name__ == '__main__':
    unittest.main()
