import os
import random
import string
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch as mockpatch

import pytest
from base.utils import get_queue_name
from challenges.models import Challenge, ChallengePrize
from challenges.utils import (
    add_domain_to_challenge,
    add_prizes_to_challenge,
    add_sponsors_to_challenge,
    add_tags_to_challenge,
    generate_presigned_url,
    get_file_content,
    parse_submission_meta_attributes,
    send_emails,
)
from django.conf import settings
from django.contrib.auth.models import User
from hosts.models import ChallengeHostTeam


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.test_file_path = os.path.join(
            settings.BASE_DIR, "examples", "example1", "test_annotation.txt"
        )
        self.sqs_valid_characters = (
            string.ascii_lowercase
            + string.ascii_uppercase
            + string.digits
            + "-"
            + "_"
        )

    def test_get_file_content(self):
        test_file_content = get_file_content(self.test_file_path, "rb")
        expected = "1\n2\n3\n4\n5\n6\n7\n8\n9\n10\n"
        self.assertEqual(test_file_content.decode(), expected)

    def test_sqs_queue_name_generator_long_title(self):
        title = "".join(
            [random.choice(self.sqs_valid_characters) for i in range(256)]
        )
        challenge_pk = 1
        sqs_queue_name = get_queue_name(title, challenge_pk)
        self.assertNotRegex(sqs_queue_name, "[^a-zA-Z0-9_-]")
        self.assertLessEqual(len(sqs_queue_name), 80)

    def test_sqs_queue_name_generator_title_has_special_char(self):
        title = "".join([random.choice(string.printable) for i in range(80)])
        challenge_pk = 1
        sqs_queue_name = get_queue_name(title, challenge_pk)
        self.assertNotRegex(sqs_queue_name, "[^a-zA-Z0-9_-]")
        self.assertLessEqual(len(sqs_queue_name), 80)

    def test_sqs_queue_name_generator_title_has_special_char_and_long_title(
        self,
    ):
        title = "".join([random.choice(string.printable) for i in range(256)])
        challenge_pk = 1
        sqs_queue_name = get_queue_name(title, challenge_pk)
        self.assertNotRegex(sqs_queue_name, "[^a-zA-Z0-9_-]")
        self.assertLessEqual(len(sqs_queue_name), 80)

    def test_sqs_queue_name_generator_empty_title(self):
        title = ""
        challenge_pk = 1
        sqs_queue_name = get_queue_name(title, challenge_pk)
        self.assertNotRegex(sqs_queue_name, "[^a-zA-Z0-9_-]")
        self.assertLessEqual(len(sqs_queue_name), 80)


class TestGeneratePresignedUrl(unittest.TestCase):
    @mockpatch("challenges.utils.settings")
    def test_debug_or_test_mode(self, mock_settings):
        mock_settings.DEBUG = True
        mock_settings.TEST = False
        result = generate_presigned_url("file_key", 1)
        self.assertIsNone(result)

        mock_settings.DEBUG = False
        mock_settings.TEST = True
        result = generate_presigned_url("file_key", 1)
        self.assertIsNone(result)

    @mockpatch("challenges.utils.get_boto3_client")
    @mockpatch("challenges.utils.get_aws_credentials_for_challenge")
    @mockpatch("challenges.utils.settings")
    def test_generate_presigned_url_success(
        self, mock_settings, mock_get_aws_credentials, mock_get_boto3_client
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        mock_settings.PRESIGNED_URL_EXPIRY_TIME = 3600

        mock_get_aws_credentials.return_value = {
            "AWS_ACCESS_KEY_ID": "fake_access_key",
            "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
            "AWS_STORAGE_BUCKET_NAME": "fake_bucket",
        }

        mock_s3_client = MagicMock()
        mock_s3_client.generate_presigned_url.return_value = (
            "http://fake_presigned_url"
        )
        mock_get_boto3_client.return_value = mock_s3_client

        result = generate_presigned_url("file_key", 1)
        self.assertEqual(
            result, {"presigned_url": "http://fake_presigned_url"}
        )
        mock_s3_client.generate_presigned_url.assert_called_once_with(
            "put_object",
            Params={"Bucket": "fake_bucket", "Key": "file_key"},
            ExpiresIn=3600,
            HttpMethod="PUT",
        )


class TestChallengeUtils(unittest.TestCase):
    def test_parse_submission_meta_attributes(self):
        # Test with submission_metadata as None
        submission = {"submission_metadata": None}
        result = parse_submission_meta_attributes(submission)
        self.assertEqual(result, {})

        # Test with submission_metadata containing different types of attributes
        submission = {
            "submission_metadata": [
                {
                    "type": "checkbox",
                    "name": "attr1",
                    "values": ["val1", "val2"],
                },
                {"type": "text", "name": "attr2", "value": "val3"},
            ]
        }
        result = parse_submission_meta_attributes(submission)
        self.assertEqual(result, {"attr1": ["val1", "val2"], "attr2": "val3"})

    @mockpatch("challenges.models.Challenge")
    def test_add_tags_to_challenge(self, MockChallenge):
        challenge = MockChallenge()
        challenge.list_tags = ["tag1", "tag2"]

        # Test with tags present in yaml_file_data
        yaml_file_data = {"tags": ["tag2", "tag3"]}
        add_tags_to_challenge(yaml_file_data, challenge)
        self.assertEqual(challenge.list_tags, ["tag2", "tag3"])

        # Test with tags not present in yaml_file_data
        yaml_file_data = {}
        add_tags_to_challenge(yaml_file_data, challenge)
        self.assertEqual(challenge.list_tags, [])

    @mockpatch("challenges.models.Challenge")
    def test_add_domain_to_challenge(self, MockChallenge):
        challenge = MockChallenge()
        challenge.DOMAIN_OPTIONS = [
            ("domain1", "Domain 1"),
            ("domain2", "Domain 2"),
        ]

        # Test with valid domain in yaml_file_data
        yaml_file_data = {"domain": "domain1"}
        response = add_domain_to_challenge(yaml_file_data, challenge)
        self.assertIsNone(response)
        self.assertEqual(challenge.domain, "domain1")

        # Test with invalid domain in yaml_file_data
        yaml_file_data = {"domain": "invalid_domain"}
        response = add_domain_to_challenge(yaml_file_data, challenge)
        self.assertEqual(
            response,
            {
                "error": "Invalid domain value: invalid_domain, valid values are: ['domain1', 'domain2']"
            },
        )

        # Test with domain not present in yaml_file_data
        yaml_file_data = {}
        response = add_domain_to_challenge(yaml_file_data, challenge)
        self.assertIsNone(response)
        self.assertIsNone(challenge.domain)


class TestAddSponsorsToChallenge(unittest.TestCase):
    @mockpatch("challenges.utils.ChallengeSponsor")
    @mockpatch("challenges.utils.ChallengeSponsorSerializer")
    def test_add_sponsors_with_valid_data(
        self, MockChallengeSponsorSerializer, MockChallengeSponsor
    ):
        yaml_file_data = {
            "sponsors": [
                {"name": "Sponsor1", "website": "http://sponsor1.com"},
                {"name": "Sponsor2", "website": "http://sponsor2.com"},
            ]
        }
        challenge = MagicMock()
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        MockChallengeSponsor.objects.filter.return_value = mock_queryset
        mock_serializer = MockChallengeSponsorSerializer.return_value
        mock_serializer.is_valid.return_value = True

        response = add_sponsors_to_challenge(yaml_file_data, challenge)

        self.assertIsNone(response)
        self.assertTrue(challenge.has_sponsors)
        self.assertEqual(mock_serializer.save.call_count, 2)

    @mockpatch("challenges.utils.ChallengeSponsor")
    @mockpatch("challenges.utils.ChallengeSponsorSerializer")
    def test_add_sponsors_with_invalid_data(
        self, MockChallengeSponsorSerializer, MockChallengeSponsor
    ):
        yaml_file_data = {
            "sponsors": [
                {"name": "Sponsor1", "website": "http://sponsor1.com"},
                {"name": "Sponsor2"},  # Missing website
            ]
        }
        challenge = MagicMock()
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        MockChallengeSponsor.objects.filter.return_value = mock_queryset

        response = add_sponsors_to_challenge(yaml_file_data, challenge)

        self.assertEqual(
            response, {"error": "Sponsor name or url not found in YAML data."}
        )

    @mockpatch("challenges.utils.ChallengeSponsor")
    @mockpatch("challenges.utils.ChallengeSponsorSerializer")
    def test_add_sponsors_existing_in_database(
        self, MockChallengeSponsorSerializer, MockChallengeSponsor
    ):
        yaml_file_data = {
            "ponsors": [{"name": "Sponsor1", "website": "http://sponsor1.com"}]
        }
        challenge = MagicMock()
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        MockChallengeSponsor.objects.filter.return_value = mock_queryset

        response = add_sponsors_to_challenge(yaml_file_data, challenge)

        self.assertIsNone(response)
        self.assertFalse(MockChallengeSponsorSerializer.called)
        self.assertFalse(challenge.has_sponsors)


@pytest.mark.django_db
class AddPrizesToChallengeTests(unittest.TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="12345"
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short Description",
            description="Description",
            terms_and_conditions="Terms",
            submission_guidelines="Guidelines",
            creator=self.challenge_host_team,
            published=False,
        )

    def test_no_prizes_in_yaml(self):
        yaml_file_data = {}
        result = add_prizes_to_challenge(yaml_file_data, self.challenge)
        self.assertIsNone(result)
        self.assertFalse(self.challenge.has_prize)

    def test_missing_rank_or_amount_in_prize_data(self):
        yaml_file_data = {"prizes": [{"rank": 1}]}  # Missing 'amount'
        result = add_prizes_to_challenge(yaml_file_data, self.challenge)
        self.assertEqual(
            result, {"error": "Prize rank or amount not found in YAML data."}
        )
        self.assertFalse(self.challenge.has_prize)

    def test_duplicate_rank_in_prize_data(self):
        yaml_file_data = {
            "prizes": [
                {"rank": 1, "amount": 100, "description": "First Prize"},
                {
                    "rank": 1,
                    "amount": 200,
                    "description": "Duplicate First Prize",
                },
            ]
        }
        result = add_prizes_to_challenge(yaml_file_data, self.challenge)
        self.assertEqual(
            result, {"error": "Duplicate rank 1 found in YAML data."}
        )
        self.assertTrue(self.challenge.has_prize)

    @mockpatch(
        "challenges.serializers.ChallengePrizeSerializer.is_valid",
        return_value=True,
    )
    @mockpatch("challenges.serializers.ChallengePrizeSerializer.save")
    def test_valid_prize_data_new_prize(self, mock_save, mock_is_valid):
        yaml_file_data = {
            "prizes": [
                {"rank": 1, "amount": 100, "description": "First Prize"}
            ]
        }
        result = add_prizes_to_challenge(yaml_file_data, self.challenge)
        self.assertIsNone(result)
        mock_save.assert_called_once()
        self.assertTrue(self.challenge.has_prize)

    @mockpatch(
        "challenges.serializers.ChallengePrizeSerializer.is_valid",
        return_value=True,
    )
    @mockpatch("challenges.serializers.ChallengePrizeSerializer.save")
    def test_valid_prize_data_existing_prize(self, mock_save, mock_is_valid):
        prize = ChallengePrize.objects.create(
            rank=1,
            amount=100,
            description="Old Prize",
            challenge=self.challenge,
        )

        yaml_file_data = {
            "prizes": [
                {"rank": 1, "amount": 100, "description": "Updated Prize"}
            ]
        }
        result = add_prizes_to_challenge(yaml_file_data, self.challenge)
        self.assertIsNone(result)
        mock_save.assert_called_once()
        self.assertTrue(self.challenge.has_prize)
        prize.refresh_from_db()
        self.assertEqual(prize.amount, "100")


class SendEmailsTests(unittest.TestCase):
    @mockpatch("challenges.utils.send_email")
    @mockpatch("challenges.utils.settings")
    def test_send_emails_to_multiple_recipients(
        self, mock_settings, mock_send_email
    ):
        mock_settings.CLOUDCV_TEAM_EMAIL = "team@cloudcv.org"
        emails = ["user1@example.com", "user2@example.com"]
        template_id = "template-id"
        template_data = {"key": "value"}

        send_emails(emails, template_id, template_data)

        # Check if send_email was called for each email
        self.assertEqual(mock_send_email.call_count, len(emails))

        # Check that send_email was called with correct arguments for the first email
        mock_send_email.assert_any_call(
            sender="team@cloudcv.org",
            recipient="user1@example.com",
            template_id=template_id,
            template_data=template_data,
        )

        # Check that send_email was called with correct arguments for the second email
        mock_send_email.assert_any_call(
            sender="team@cloudcv.org",
            recipient="user2@example.com",
            template_id=template_id,
            template_data=template_data,
        )
