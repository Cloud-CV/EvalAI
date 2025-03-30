import base64
from unittest import mock
import re
from django.test import TestCase
from challenges.models import Challenge

from jobs.aws_utils import generate_aws_eks_bearer_token


class GenerateAwsEksBearerTokenTest(TestCase):
    def setUp(self):
        self.challenge = mock.MagicMock(spec=Challenge)
        self.challenge.id = 1
        self.cluster_name = "test-cluster"
        
        self.aws_credentials = {
            "AWS_ACCESS_KEY_ID": "test_access_key",
            "AWS_SECRET_ACCESS_KEY": "test_secret_key",
            "AWS_REGION": "us-west-2"
        }
        
        self.mock_signed_url = "https://sts.us-west-2.amazonaws.com/?Action=GetCallerIdentity&Version=2011-06-15&X-Amz-Algorithm=AWS4-HMAC-SHA256&X-Amz-Credential=test"

    @mock.patch('jobs.aws_utils.get_aws_credentials_for_challenge')
    @mock.patch('jobs.aws_utils.boto3.Session')
    def test_generate_aws_eks_bearer_token(self, mock_session, mock_get_credentials):
        mock_get_credentials.return_value = self.aws_credentials
        
        mock_session_instance = mock.MagicMock()
        mock_session.return_value = mock_session_instance
        
        mock_client = mock.MagicMock()
        mock_session_instance.client.return_value = mock_client
        
        mock_client.meta.service_model.service_id = "sts"
        
        mock_signer = mock.MagicMock()
        mock_signer.generate_presigned_url.return_value = self.mock_signed_url
        
        with mock.patch('jobs.aws_utils.RequestSigner', return_value=mock_signer):
            result = generate_aws_eks_bearer_token(self.cluster_name, self.challenge)
            
            mock_get_credentials.assert_called_once_with(self.challenge.id)
            
            mock_session.assert_called_once_with(
                aws_access_key_id=self.aws_credentials["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=self.aws_credentials["AWS_SECRET_ACCESS_KEY"]
            )
            
            mock_session_instance.client.assert_called_once_with(
                "sts", region_name=self.aws_credentials["AWS_REGION"]
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
                operation_name=""
            )

            expected_base64 = base64.urlsafe_b64encode(self.mock_signed_url.encode("utf-8")).decode("utf-8")
            expected_token = "k8s-aws-v1." + re.sub(r"=*", "", expected_base64)
            
            self.assertEqual(result, expected_token)
