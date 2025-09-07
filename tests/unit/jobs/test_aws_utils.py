import base64
import re
from unittest.mock import MagicMock, patch

from challenges.models import Challenge
from django.test import TestCase
from jobs.aws_utils import generate_aws_eks_bearer_token


class TestGenerateAWSEksBearerToken(TestCase):
    def setUp(self):
        """Set up common test data and mock objects"""
        self.cluster_name = "test-cluster"
        self.challenge = MagicMock(spec=Challenge)
        self.challenge.id = "challenge-id"

        self.aws_credentials = {
            "AWS_ACCESS_KEY_ID": "fake_access_key",
            "AWS_SECRET_ACCESS_KEY": "fake_secret_key",
            "AWS_REGION": "us-west-2",
        }

        self.mock_signed_url = "https://sts.us-west-2.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=test"

    @patch("jobs.aws_utils.get_aws_credentials_for_challenge")
    @patch("jobs.aws_utils.boto3.Session")
    @patch("jobs.aws_utils.RequestSigner")
    def test_generate_aws_eks_bearer_token(
        self, MockRequestSigner, MockSession, MockGetAwsCredentials
    ):
        MockGetAwsCredentials.return_value = self.aws_credentials
        mock_session = MagicMock()
        mock_client = MagicMock()
        mock_session.client.return_value = mock_client
        mock_client.meta.service_model.service_id = "STS"
        MockSession.return_value = mock_session

        mock_signer = MagicMock()
        mock_signer.generate_presigned_url.return_value = self.mock_signed_url
        MockRequestSigner.return_value = mock_signer

        token = generate_aws_eks_bearer_token(
            self.cluster_name, self.challenge
        )

        expected_base64_url = base64.urlsafe_b64encode(
            self.mock_signed_url.encode("utf-8")
        ).decode("utf-8")
        expected_bearer_token = "k8s-aws-v1." + re.sub(
            r"=*", "", expected_base64_url
        )

        MockGetAwsCredentials.assert_called_once_with(self.challenge.id)
        MockSession.assert_called_once_with(
            aws_access_key_id=self.aws_credentials["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=self.aws_credentials[
                "AWS_SECRET_ACCESS_KEY"
            ],
        )
        mock_session.client.assert_called_once_with(
            "sts", region_name=self.aws_credentials["AWS_REGION"]
        )
        MockRequestSigner.assert_called_once_with(
            "STS",
            self.aws_credentials["AWS_REGION"],
            "sts",
            "v4",
            mock_session.get_credentials(),
            mock_session.events,
        )

        expected_params = {
            "method": "GET",
            "url": f"https://sts.{self.aws_credentials['AWS_REGION']}.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15",
            "body": {},
            "headers": {"x-k8s-aws-id": self.cluster_name},
            "context": {},
        }

        mock_signer.generate_presigned_url.assert_called_once_with(
            expected_params,
            region_name=self.aws_credentials["AWS_REGION"],
            expires_in=60,
            operation_name="",
        )

        self.assertEqual(token, expected_bearer_token)

    @patch("jobs.aws_utils.get_aws_credentials_for_challenge")
    @patch("jobs.aws_utils.boto3.Session")
    def test_generate_aws_eks_bearer_token_with_context_manager(
        self, MockSession, MockGetAwsCredentials
    ):
        """Test using context manager approach from test-jobs-aws-utils branch"""
        MockGetAwsCredentials.return_value = self.aws_credentials

        mock_session_instance = MagicMock()
        MockSession.return_value = mock_session_instance

        mock_client = MagicMock()
        mock_session_instance.client.return_value = mock_client
        mock_client.meta.service_model.service_id = "sts"

        mock_signer = MagicMock()
        mock_signer.generate_presigned_url.return_value = self.mock_signed_url

        with patch("jobs.aws_utils.RequestSigner", return_value=mock_signer):
            result = generate_aws_eks_bearer_token(
                self.cluster_name, self.challenge
            )

            expected_base64 = base64.urlsafe_b64encode(
                self.mock_signed_url.encode("utf-8")
            ).decode("utf-8")
            expected_token = "k8s-aws-v1." + re.sub(r"=*", "", expected_base64)

            self.assertEqual(result, expected_token)
