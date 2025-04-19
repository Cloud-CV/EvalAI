import base64
import re
import unittest
from unittest.mock import MagicMock, patch

from jobs.aws_utils import generate_aws_eks_bearer_token


class TestGenerateAWSEksBearerToken(unittest.TestCase):

    @patch("jobs.aws_utils.get_aws_credentials_for_challenge")
    @patch("jobs.aws_utils.boto3.Session")
    @patch("jobs.aws_utils.RequestSigner")
    def test_generate_aws_eks_bearer_token(
        self, MockRequestSigner, MockSession, MockGetAwsCredentials
    ):
        # Mock AWS credentials
        MockGetAwsCredentials.return_value = {
            "AWS_ACCESS_KEY_ID": "fake_access_key",
            "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
            "AWS_REGION": "us-west-2",
        }

        # Mock the Session and its client method
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_client.meta.service_model.service_id = "STS"
        MockSession.return_value = mock_session

        # Mock RequestSigner and its generate_presigned_url method
        mock_signer = MagicMock()
        mock_signer.generate_presigned_url.return_value = "https://signed.url"
        MockRequestSigner.return_value = mock_signer

        # Define test input
        cluster_name = "test-cluster"

        class Challenge:
            id = "challenge-id"

        challenge = Challenge()

        # Call the function to test
        token = generate_aws_eks_bearer_token(cluster_name, challenge)

        # Expected results
        expected_signed_url = "https://signed.url"
        expected_base64_url = base64.urlsafe_b64encode(
            expected_signed_url.encode("utf-8")
        ).decode("utf-8")
        expected_bearer_token = "k8s-aws-v1." + re.sub(
            r"=*", "", expected_base64_url
        )

        # Assertions
        MockGetAwsCredentials.assert_called_once_with("challenge-id")
        MockSession.assert_called_once_with(
            aws_access_key_id="fake_access_key",
            aws_secret_access_key="fake_secret_key",
        )
        mock_session.client.assert_called_once_with(
            "sts", region_name="us-west-2"
        )
        MockRequestSigner.assert_called_once_with(
            "STS",
            "us-west-2",
            "sts",
            "v4",
            mock_session.get_credentials(),
            mock_session.events,
        )
        mock_signer.generate_presigned_url.assert_called_once_with(
            {
                "method": "GET",
                "url": "https://sts.us-west-2.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15",
                "body": {},
                "headers": {"x-k8s-aws-id": cluster_name},
                "context": {},
            },
            region_name="us-west-2",
            expires_in=60,
            operation_name="",
        )
        self.assertEqual(token, expected_bearer_token)
