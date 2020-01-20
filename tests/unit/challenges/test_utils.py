import os
import unittest
import mock

from challenges.models import Challenge
from django.conf import settings

import challenges.utils as utils


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.test_file_path = os.path.join(
            settings.BASE_DIR, "examples", "example1", "test_annotation.txt"
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description",
            description="Descriptione",
            terms_and_conditions="Terms and conditions",
            submission_guidelines="Submission guidelines",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            queue="test_queue",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
            aws_account_id="id",
            aws_access_key_id="accesskeyid",
            aws_secret_access-key="secretkey",
            use_host_credentials=True,
        )
        self.challenge.slug = "{}-{}".format(
            self.challenge.title.replace(" ", "-").lower(), self.challenge.pk
        )[:199]
        self.challenge.save()

        self.ecr_client = boto3.client("ecr", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"), aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"), aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),)
    def test_get_file_content(self):
        test_file_content = utils.get_file_content(self.test_file_path, "rb")
        expected = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n"
        self.assertEqual(test_file_content.decode(), expected)

    def test_convert_to_aws_ecr_compatible_format(self):
        input = "Test Convert to Compatible!"
        expected = "test-convert-to-compatible!"
        response = utils.convert_to_aws_ecr_compatible_format
        assert expected == response

    def test_convert_to_aws_federated_user_format(self):
        input = "1234asdf!@#$%^&*(),.-= "
        expected = "1234asdf@,.-=-"
        response = utils.convert_to_aws_federated_user_format(input)
        assert expected == response
        
    def test_get_aws_credentials_for_challenge_when_get_host_credentials_is_true(self):
        expected = {
            "AWS_ACCOUNT_ID": self.challenge.aws_account_id,
            "AWS_ACCESS_KEY_ID": self.challenge.aws_access_key_id,
            "AWS_SECRET_ACCESS_KEY": self.challenge.aws_secret_access_key,
            "AWS_REGION": self.challenge.aws_region,
        }
        response = utils.get_aws_credentials_for_challenge(self.challenge)
        assert expected == response

    @mock.patch("os.environ.get(\"AWS_ACCOUNT_ID\", \"aws_account_id\")")
    @mock.patch("os.environ.get(\"AWS_ACCESS_KEY_ID\", \"aws_access_key_id\")")
    @mock.patch
    def test_get_aws_credentials_for_challenge_when_get_host_credentials_is_true(self):
        
        
        
    def 
