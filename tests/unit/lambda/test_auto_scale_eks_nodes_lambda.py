import importlib
import importlib.util
import json
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
    def test_raises_when_eks_update_fails(
        self, mock_call_evalai_api, mock_boto_client
    ):
        """
        Async invocations only retry and reach the DLQ when the handler
        raises. Returning a 500 body would be recorded as a success.
        """
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

        with self.assertRaises(self.module.AutoscaleError) as ctx:
            self.module.handler({"challenge_pk": 12}, None)
        self.assertIn("Failed to update EKS nodegroup", str(ctx.exception))

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_raises_when_describe_nodegroup_fails(
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
        mock_eks.list_nodegroups.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException"}}, "ListNodegroups"
        )
        mock_boto_client.return_value = mock_eks

        with self.assertRaises(self.module.AutoscaleError) as ctx:
            self.module.handler({"challenge_pk": 13}, None)
        self.assertIn("Failed to fetch EKS nodegroup", str(ctx.exception))

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_caps_max_size_at_scale_up_cap(
        self, mock_call_evalai_api, mock_boto_client
    ):
        """
        maxSize must not exceed the challenge's configured cap, even when a
        burst of pending submissions far exceeds it.
        """
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 2,
                "end_date": None,
            },
            {"pending_submissions": 50},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 0, "desiredSize": 0, "maxSize": 1}
            }
        }
        mock_eks.update_nodegroup_config.return_value = {
            "update": {"id": "upd-cap"}
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 14}, None)
        self.assertEqual(response["statusCode"], 200)
        scaling_config = mock_eks.update_nodegroup_config.call_args.kwargs[
            "scalingConfig"
        ]
        self.assertEqual(scaling_config["desiredSize"], 2)
        self.assertEqual(scaling_config["maxSize"], 2)

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_uses_recorded_nodegroup_name(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "nodegroup_name": "recorded-ng",
                "scale_up_cap": 5,
                "end_date": None,
            },
            {"pending_submissions": 3},
        ]
        mock_eks = MagicMock()
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 0, "desiredSize": 0, "maxSize": 1}
            }
        }
        mock_eks.update_nodegroup_config.return_value = {
            "update": {"id": "upd-ng"}
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 15}, None)
        self.assertEqual(response["statusCode"], 200)
        # The recorded name is authoritative, so no lookup should happen.
        mock_eks.list_nodegroups.assert_not_called()
        self.assertEqual(
            mock_eks.update_nodegroup_config.call_args.kwargs["nodegroupName"],
            "recorded-ng",
        )

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_warns_when_host_credentials_missing_account_id(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "challenge_pk": 16,
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 5,
                "use_host_credentials": True,
                "aws_account_id": None,
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
        mock_eks.update_nodegroup_config.return_value = {
            "update": {"id": "upd-warn"}
        }
        mock_boto_client.return_value = mock_eks

        with self.assertLogs(self.module.logger, level="WARNING") as logs:
            response = self.module.handler({"challenge_pk": 16}, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertTrue(
            any("aws_account_id" in message for message in logs.output)
        )
        # Falls back to the Lambda's own account rather than assuming a role.
        for call in mock_boto_client.call_args_list:
            self.assertNotEqual(call.args[0], "sts")

    @patch("auto_scale_eks_nodes_lambda._scale_challenge")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_sweep_scales_every_eligible_challenge(
        self, mock_call_evalai_api, mock_scale_challenge
    ):
        mock_call_evalai_api.return_value = {
            "challenge_pks": [1, 2, 3],
            "count": 3,
        }

        response = self.module.handler({"sweep": True}, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(mock_scale_challenge.call_count, 3)
        self.assertEqual(json.loads(response["body"])["swept"], 3)

    @patch("auto_scale_eks_nodes_lambda._scale_challenge")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_sweep_continues_past_failures_then_raises(
        self, mock_call_evalai_api, mock_scale_challenge
    ):
        module = self.module
        mock_call_evalai_api.return_value = {"challenge_pks": [1, 2, 3]}

        def scale(challenge_pk):
            if challenge_pk == 2:
                raise module.AutoscaleError("boom")
            return {"statusCode": 200, "body": "No change"}

        mock_scale_challenge.side_effect = scale

        with self.assertRaises(module.AutoscaleError) as ctx:
            module.handler({"sweep": True}, None)

        # Every challenge is attempted even though the second one fails.
        self.assertEqual(mock_scale_challenge.call_count, 3)
        self.assertIn("2", str(ctx.exception))

    @patch("auto_scale_eks_nodes_lambda._scale_challenge")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_sweep_isolates_non_autoscale_errors(
        self, mock_call_evalai_api, mock_scale_challenge
    ):
        """
        Malformed API data raises a bare ValueError rather than an
        AutoscaleError. One such challenge must not skip the rest of the
        sweep.
        """
        module = self.module
        mock_call_evalai_api.return_value = {"challenge_pks": [1, 2, 3]}

        def scale(challenge_pk):
            if challenge_pk == 1:
                raise ValueError("invalid literal for int()")
            return {"statusCode": 200, "body": "No change"}

        mock_scale_challenge.side_effect = scale

        with self.assertRaises(module.AutoscaleError) as ctx:
            module.handler({"sweep": True}, None)

        self.assertEqual(mock_scale_challenge.call_count, 3)
        self.assertIn("1", str(ctx.exception))

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_scale_down_when_challenge_disabled(
        self, mock_call_evalai_api, mock_boto_client
    ):
        """
        A disabled challenge holds zero nodes. It stays in the sweep rather
        than being filtered out, so a challenge disabled while scaled up still
        gets reconciled back down.
        """
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 10,
                "is_disabled": True,
                "end_date": None,
            },
            {"pending_submissions": 8},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 1, "desiredSize": 5, "maxSize": 5}
            }
        }
        mock_eks.update_nodegroup_config.return_value = {
            "update": {"id": "upd-disabled"}
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 88}, None)

        self.assertEqual(response["statusCode"], 200)
        self.assertEqual(
            mock_eks.update_nodegroup_config.call_args.kwargs["scalingConfig"][
                "desiredSize"
            ],
            0,
        )

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

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_assumes_cross_account_role_for_host_credentials(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 5,
                "use_host_credentials": True,
                "aws_account_id": "123456789012",
                "end_date": None,
            },
            {"pending_submissions": 4},
        ]
        mock_sts = MagicMock()
        mock_sts.assume_role.return_value = {
            "Credentials": {
                "AccessKeyId": "AKIATEST",
                "SecretAccessKey": "secret",
                "SessionToken": "token",
            }
        }
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 0, "desiredSize": 0, "maxSize": 1}
            }
        }
        mock_eks.update_nodegroup_config.return_value = {
            "update": {"id": "upd-xacct"}
        }

        def client_factory(service, *args, **kwargs):
            return mock_sts if service == "sts" else mock_eks

        mock_boto_client.side_effect = client_factory

        response = self.module.handler({"challenge_pk": 42}, None)

        self.assertEqual(response["statusCode"], 200)
        mock_sts.assume_role.assert_called_once_with(
            RoleArn="arn:aws:iam::123456789012:role/evalai-autoscale-crossaccount",
            RoleSessionName="evalai-eks-autoscale",
        )
        mock_boto_client.assert_any_call(
            "eks",
            region_name="us-east-1",
            aws_access_key_id="AKIATEST",
            aws_secret_access_key="secret",
            aws_session_token="token",
        )
        self.assertEqual(
            mock_eks.update_nodegroup_config.call_args.kwargs["scalingConfig"][
                "desiredSize"
            ],
            4,
        )

    @patch("boto3.client")
    @patch("auto_scale_eks_nodes_lambda._call_evalai_api")
    def test_uses_default_client_without_host_credentials(
        self, mock_call_evalai_api, mock_boto_client
    ):
        mock_call_evalai_api.side_effect = [
            {
                "is_docker_based": True,
                "remote_evaluation": False,
                "cluster_name": "cluster-1",
                "scale_up_cap": 5,
                "use_host_credentials": False,
                "aws_account_id": "123456789012",
                "end_date": None,
            },
            {"pending_submissions": 4},
        ]
        mock_eks = MagicMock()
        mock_eks.list_nodegroups.return_value = {"nodegroups": ["ng-1"]}
        mock_eks.describe_nodegroup.return_value = {
            "nodegroup": {
                "scalingConfig": {"minSize": 0, "desiredSize": 0, "maxSize": 1}
            }
        }
        mock_eks.update_nodegroup_config.return_value = {
            "update": {"id": "upd-same"}
        }
        mock_boto_client.return_value = mock_eks

        response = self.module.handler({"challenge_pk": 77}, None)

        self.assertEqual(response["statusCode"], 200)
        # No cross-account assume when use_host_credentials is False.
        for call in mock_boto_client.call_args_list:
            self.assertNotEqual(call.args[0], "sts")
        mock_boto_client.assert_called_once_with(
            "eks", region_name="us-east-1"
        )


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
