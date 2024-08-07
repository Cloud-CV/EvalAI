import unittest
from django.apps import apps
from analytics.apps import AnalyticsConfig


class TestAnalyticsConfig(unittest.TestCase):
    def test_apps(self):
        self.assertEqual(AnalyticsConfig.name, "analytics")
        self.assertEqual(apps.get_app_config("analytics").name, "analytics")

if __name__ == '__main__':
    unittest.main()
