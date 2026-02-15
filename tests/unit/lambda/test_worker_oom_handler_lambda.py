import importlib
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError


def _import_lambda_module():
    """Import the Lambda module using importlib since 'lambda' is a Python keyword."""
    spec = importlib.util.spec_from_file_location(
        "worker_oom_handler_lambda",
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "scripts",
            "lambda",
            "worker_oom_handler_lambda.py",
        ),
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class TestIsOomEvent(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(
            os.environ,
            {
                "ECS_CLUSTER": "test-cluster",
                "AWS_REGION": "us-east-1",
                "EVALAI_API_SERVER": "https://eval.ai",
                "LAMBDA_AUTH_TOKEN": "test-token",
            },
        )
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_oom_via_stopped_reason(self):
        detail = {"stoppedReason": "OutOfMemory: Container killed"}
        self.assertTrue(self.module.is_oom_event(detail))

    def test_oom_via_exit_code_137(self):
        detail = {
            "stoppedReason": "Essential container exited",
            "containers": [{"exitCode": 137, "name": "worker"}],
        }
        self.assertTrue(self.module.is_oom_event(detail))

    def test_not_oom_normal_exit(self):
        detail = {
            "stoppedReason": "Essential container exited",
            "containers": [{"exitCode": 0, "name": "worker"}],
        }
        self.assertFalse(self.module.is_oom_event(detail))

    def test_not_oom_empty_detail(self):
        detail = {}
        self.assertFalse(self.module.is_oom_event(detail))


class TestGetServiceNameFromTask(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(
            os.environ,
            {
                "ECS_CLUSTER": "test-cluster",
                "AWS_REGION": "us-east-1",
                "EVALAI_API_SERVER": "https://eval.ai",
                "LAMBDA_AUTH_TOKEN": "test-token",
            },
        )
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_extracts_service_name(self):
        detail = {"group": "service:my-challenge-queue_service"}
        self.assertEqual(
            self.module.get_service_name_from_task(detail),
            "my-challenge-queue_service",
        )

    def test_returns_none_for_non_service(self):
        detail = {"group": "family:my-task-family"}
        self.assertIsNone(self.module.get_service_name_from_task(detail))

    def test_returns_none_for_empty_group(self):
        detail = {"group": ""}
        self.assertIsNone(self.module.get_service_name_from_task(detail))

    def test_returns_none_for_missing_group(self):
        detail = {}
        self.assertIsNone(self.module.get_service_name_from_task(detail))


class TestGetChallengePkFromService(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(
            os.environ,
            {
                "ECS_CLUSTER": "test-cluster",
                "AWS_REGION": "us-east-1",
                "EVALAI_API_SERVER": "https://eval.ai",
                "LAMBDA_AUTH_TOKEN": "test-token",
            },
        )
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_returns_challenge_pk_from_tags(self):
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {
            "services": [
                {
                    "serviceName": "test_service",
                    "tags": [
                        {"key": "challenge_pk", "value": "42"},
                        {"key": "managed_by", "value": "evalai"},
                    ],
                }
            ]
        }
        result = self.module.get_challenge_pk_from_service(
            mock_client, "test-cluster", "test_service"
        )
        self.assertEqual(result, "42")

    def test_returns_none_when_no_tag(self):
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {
            "services": [{"serviceName": "test_service", "tags": []}]
        }
        result = self.module.get_challenge_pk_from_service(
            mock_client, "test-cluster", "test_service"
        )
        self.assertIsNone(result)

    def test_returns_none_when_no_services(self):
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {"services": []}
        result = self.module.get_challenge_pk_from_service(
            mock_client, "test-cluster", "test_service"
        )
        self.assertIsNone(result)

    def test_returns_none_on_client_error(self):
        mock_client = MagicMock()
        mock_client.describe_services.side_effect = ClientError(
            error_response={"Error": {"Code": "ServiceNotFound"}},
            operation_name="DescribeServices",
        )
        result = self.module.get_challenge_pk_from_service(
            mock_client, "test-cluster", "test_service"
        )
        self.assertIsNone(result)


class TestScaleServiceToZero(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(
            os.environ,
            {
                "ECS_CLUSTER": "test-cluster",
                "AWS_REGION": "us-east-1",
                "EVALAI_API_SERVER": "https://eval.ai",
                "LAMBDA_AUTH_TOKEN": "test-token",
            },
        )
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_success(self):
        mock_client = MagicMock()
        result = self.module.scale_service_to_zero(
            mock_client, "test-cluster", "test_service"
        )
        self.assertTrue(result)
        mock_client.update_service.assert_called_once_with(
            cluster="test-cluster",
            service="test_service",
            desiredCount=0,
        )

    def test_failure(self):
        mock_client = MagicMock()
        mock_client.update_service.side_effect = ClientError(
            error_response={"Error": {"Code": "ServiceNotFound"}},
            operation_name="UpdateService",
        )
        result = self.module.scale_service_to_zero(
            mock_client, "test-cluster", "test_service"
        )
        self.assertFalse(result)


class TestHandler(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(
            os.environ,
            {
                "ECS_CLUSTER": "test-cluster",
                "AWS_REGION": "us-east-1",
                "EVALAI_API_SERVER": "https://eval.ai",
                "LAMBDA_AUTH_TOKEN": "test-token",
            },
        )
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_ignores_non_stopped_events(self):
        event = {"detail": {"lastStatus": "RUNNING"}}
        result = self.module.handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        self.assertIn("Not a STOPPED event", result["body"])

    def test_ignores_non_oom_events(self):
        event = {
            "detail": {
                "lastStatus": "STOPPED",
                "stoppedReason": "User initiated",
                "containers": [{"exitCode": 0}],
            }
        }
        result = self.module.handler(event, None)
        self.assertEqual(result["statusCode"], 200)
        self.assertIn("Not an OOM event", result["body"])

    def test_handles_missing_service_name(self):
        event = {
            "detail": {
                "lastStatus": "STOPPED",
                "stoppedReason": "OutOfMemory",
                "group": "family:something",
            }
        }
        result = self.module.handler(event, None)
        self.assertEqual(result["statusCode"], 400)
        self.assertIn("Could not determine service name", result["body"])

    @patch("boto3.client")
    def test_handles_oom_event_successfully(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        # Mock describe_services to return challenge_pk tag
        mock_ecs.describe_services.return_value = {
            "services": [
                {
                    "tags": [
                        {"key": "challenge_pk", "value": "42"},
                        {"key": "managed_by", "value": "evalai"},
                    ]
                }
            ]
        }

        # Mock describe_task_definition to return memory
        mock_ecs.describe_task_definition.return_value = {
            "taskDefinition": {"memory": "2048"}
        }

        # Patch notify_evalai_api on the module
        self.module.notify_evalai_api = MagicMock(return_value=True)

        event = {
            "detail": {
                "lastStatus": "STOPPED",
                "stoppedReason": "OutOfMemory",
                "group": "service:challenge-queue_service",
                "taskDefinitionArn": "arn:aws:ecs:us-east-1:123:task-def/test:1",
            }
        }

        result = self.module.handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "OOM handled for challenge 42")
        self.assertEqual(body["service"], "challenge-queue_service")
        self.assertEqual(body["worker_memory"], "2048")

        # Verify service was scaled to 0
        mock_ecs.update_service.assert_called_once_with(
            cluster="test-cluster",
            service="challenge-queue_service",
            desiredCount=0,
        )

        # Verify API was notified
        self.module.notify_evalai_api.assert_called_once()
        call_args = self.module.notify_evalai_api.call_args[0]
        self.assertEqual(call_args[0], "42")
        self.assertIn("OutOfMemoryError", call_args[1])
        self.assertIn("2048 MB", call_args[1])

    @patch("boto3.client")
    def test_handles_missing_challenge_pk_tag(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        # Mock describe_services to return no tags
        mock_ecs.describe_services.return_value = {"services": [{"tags": []}]}

        event = {
            "detail": {
                "lastStatus": "STOPPED",
                "stoppedReason": "OutOfMemory",
                "group": "service:challenge-queue_service",
            }
        }

        result = self.module.handler(event, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("No challenge_pk tag found", result["body"])

    @patch("boto3.client")
    def test_handles_exit_code_137(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        mock_ecs.describe_services.return_value = {
            "services": [{"tags": [{"key": "challenge_pk", "value": "99"}]}]
        }
        mock_ecs.describe_task_definition.return_value = {
            "taskDefinition": {"memory": "4096"}
        }

        self.module.notify_evalai_api = MagicMock(return_value=True)

        event = {
            "detail": {
                "lastStatus": "STOPPED",
                "stoppedReason": "Essential container exited",
                "containers": [{"exitCode": 137, "name": "worker"}],
                "group": "service:queue_service",
                "taskDefinitionArn": "arn:aws:ecs:us-east-1:123:task-def/test:1",
            }
        }

        result = self.module.handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["message"], "OOM handled for challenge 99")
        self.assertIn("4096", body["worker_memory"])


if __name__ == "__main__":
    unittest.main()
