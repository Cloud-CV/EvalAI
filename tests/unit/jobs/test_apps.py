import unittest
from django.apps import apps
from jobs.apps import JobsConfig


class JobsConfigTest(unittest.TestCase):
    def test_apps_config(self):
        self.assertEqual(JobsConfig.name, "jobs")
        self.assertEqual(apps.get_app_config('jobs').name, 'jobs')

if __name__ == '__main__':
    unittest.main()
