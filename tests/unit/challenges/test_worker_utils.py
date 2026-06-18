from challenges.constants import get_ecr_env_name
from challenges.worker_utils import (
    is_allowed_worker_image_url,
    normalize_worker_python_version,
)
from django.test import SimpleTestCase


class TestChallengeWorkerUtils(SimpleTestCase):
    def test_get_ecr_env_name_maps_prod_to_production(self):
        self.assertEqual(get_ecr_env_name("prod"), "production")
        self.assertEqual(get_ecr_env_name("staging"), "staging")

    def test_get_ecr_env_name_honors_override(self):
        self.assertEqual(get_ecr_env_name("prod", override="custom"), "custom")

    def test_is_allowed_worker_image_url_allows_empty_and_ami(self):
        self.assertTrue(is_allowed_worker_image_url(""))
        self.assertTrue(
            is_allowed_worker_image_url(
                "ami-0747bdcabd34c712a",
                aws_account_id="123456789012",
            )
        )

    def test_is_allowed_worker_image_url_allows_evalai_ecr(self):
        image = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-worker-py3.9:latest"
        )
        self.assertTrue(
            is_allowed_worker_image_url(
                image,
                aws_account_id="123456789012",
                aws_region="us-east-1",
            )
        )

    def test_is_allowed_worker_image_url_rejects_external_registry(self):
        self.assertFalse(
            is_allowed_worker_image_url(
                "docker.io/library/nginx:latest",
                aws_account_id="123456789012",
                aws_region="us-east-1",
            )
        )

    def test_is_allowed_worker_image_url_rejects_non_evalai_ecr_repo(self):
        image = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            + "other-repo:latest"
        )
        self.assertFalse(
            is_allowed_worker_image_url(
                image,
                aws_account_id="123456789012",
                aws_region="us-east-1",
            )
        )

    def test_is_allowed_worker_image_url_rejects_missing_account_id(self):
        image = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-worker-py3.9:latest"
        )
        self.assertFalse(
            is_allowed_worker_image_url(
                image,
                aws_account_id=None,
                aws_region="us-east-1",
            )
        )

    def test_normalize_worker_python_version(self):
        self.assertEqual(normalize_worker_python_version("3.8"), "3.8")
        self.assertEqual(normalize_worker_python_version("3.11"), "3.9")
