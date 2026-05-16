import importlib
import os
import sys
import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

ENV_VARS = {
    "AWS_REGION": "us-east-1",
    "EVALAI_API_SERVER": "https://eval.ai",
    "LAMBDA_AUTH_TOKEN": "test-token",
}


def _import_lambda_module():
    spec = importlib.util.spec_from_file_location(
        "auto_scale_eks_nodes_lambda",
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "scripts",
            "lambda",
            "auto_scale_eks_nodes_lambda.py",
        ),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class TestAutoScaleEksNodesLambda(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_missing_challenge_pk(
        self, mock_call_evalai_api, mock_boto_client
    ):
        response = self.module.handler({}, None)
        self.assertEqual(response["statusCode"], 400)
        mock_call_evalai_api.assert_not_called()
        mock_boto_client.assert_not_called()

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_skips_non_target_challenge(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": False,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 3,
                "end_date": None,
            },
            {"pending_submissions": 3},
        ]

        response = self.module.handler({"challenge_pk": 1}, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertIn("Skipped", response["body"])
        mock_boto_client.assert_not_called()

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_scale_up_on_pending(self, mock_call_evalai_api, mock_boto_client):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 5,
                "end_date": None,
            },
            {"pending_submissions": 4},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 0, "desiredSize": 1, "maxSize": 1}
            }
        }
        mock_eks.update_nodegroup_config.return_value = {
            "update": {"id": "upd-123"}
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 3}, None)
        self.assertEqual(response["statusCode"], 200)
        kwargs = mock_eks.update_nodegroup_config.call_args.kwargs
        self.assertEqual(kwargs["scalingConfig"]["desiredSize"], 4)
        self.assertEqual(kwargs["scalingConfig"]["minSize"], 1)

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_no_change_when_scaling_matches(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 3,
                "end_date": None,
            },
            {"pending_submissions": 2},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 1, "desiredSize": 2, "maxSize": 2}
            }
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 6}, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["body"], "No change")
        mock_eks.update_nodegroup_config.assert_not_called()

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_returns_500_when_eks_update_fails(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 5,
                "end_date": None,
            },
            {"pending_submissions": 3},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 0, "desiredSize": 0, "maxSize": 1}
            }
        }
        mock_eks.update_nodegroup_config.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException"}},
            "UpdateNodegroupConfig",
        )
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 12}, None)
        self.assertEqual(response["statusCode"], 500)
        self.assertIn("Failed to update EKS nodegroup", response["body"])

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_no_non_zero_downscale_when_pending_drops(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 10,
                "end_date": None,
            },
            {"pending_submissions": 2},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 1, "desiredSize": 5, "maxSize": 5}
            }
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 55}, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["body"], "No change")
        mock_eks.update_nodegroup_config.assert_not_called()

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_no_non_zero_downscale_when_cap_below_current(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 3,
                "end_date": None,
            },
            {"pending_submissions": 20},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {
                    "minSize": 1,
                    "desiredSize": 10,
                    "maxSize": 20,
                }
            }
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 66}, None)
        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(response["body"], "No change")
        mock_eks.update_nodegroup_config.assert_not_called()

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_uses_challenge_aws_region_for_eks_client(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 10,
                "aws_region": "us-west-2",
                "end_date": None,
            },
            {"pending_submissions": 4},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 1, "desiredSize": 1, "maxSize": 1}
            }
        }
        mock_eks.update_nodegroup_config.return_value = {
            "update": {"id": "upd-xyz"}
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 56}, None)
        self.assertEqual(response["statusCode"], 200)
        mock_boto_client.assert_called_once_with(
            "eks", region_name="us-west-2"
        )

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_scale_down_when_challenge_has_ended(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 10,
                "end_date": "2000-01-01T00:00:00Z",
            },
            {"pending_submissions": 10},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 1, "desiredSize": 5, "maxSize": 5}
            }
        }
        mock_eks.update_nodegroup_config.return_value = {
            "update": {"id": "upd-end"}
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 99}, None)
        self.assertEqual(response["statusCode"], 200)
        kwargs = mock_eks.update_nodegroup_config.call_args.kwargs
        self.assertEqual(kwargs["scalingConfig"]["desiredSize"], 0)


class TestDesiredSizeLogic(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_desired_size_for_pending(self):
        self.assertEqual(self.module._desired_size_for_pending(0, 4), 0)
        self.assertEqual(self.module._desired_size_for_pending(2, 4), 2)
        self.assertEqual(self.module._desired_size_for_pending(10, 4), 4)

    def test_validate_env(self):
        with patch.dict(os.environ, {}, clear=True):
            module = _import_lambda_module()
            with self.assertRaises(RuntimeError):
                module._validate_env()
