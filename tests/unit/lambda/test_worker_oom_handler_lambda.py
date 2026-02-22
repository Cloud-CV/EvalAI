import importlib
import json
import os
import unittest
from unittest.mock import MagicMock, patch

from botocore.exceptions import ClientError

ENV_VARS = {
    "ECS_CLUSTER": "test-cluster",
    "AWS_REGION": "us-east-1",
    "EVALAI_API_SERVER": "https://eval.ai",
    "LAMBDA_AUTH_TOKEN": "test-token",
}


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
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
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
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
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
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
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
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
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


class TestGetNextMemoryCpuTier(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_increment_within_cpu_512_tier(self):
        self.assertEqual(
            self.module.get_next_memory_cpu_tier(1024, 512), (2048, 512)
        )
        self.assertEqual(
            self.module.get_next_memory_cpu_tier(2048, 512), (3072, 512)
        )
        self.assertEqual(
            self.module.get_next_memory_cpu_tier(3072, 512), (4096, 512)
        )

    def test_upgrade_from_cpu_512_to_1024(self):
        result = self.module.get_next_memory_cpu_tier(4096, 512)
        self.assertEqual(result, (5120, 1024))

    def test_increment_within_cpu_1024_tier(self):
        self.assertEqual(
            self.module.get_next_memory_cpu_tier(5120, 1024), (6144, 1024)
        )
        self.assertEqual(
            self.module.get_next_memory_cpu_tier(7168, 1024), (8192, 1024)
        )

    def test_upgrade_from_cpu_1024_to_2048(self):
        result = self.module.get_next_memory_cpu_tier(8192, 1024)
        self.assertEqual(result, (9216, 2048))

    def test_increment_within_cpu_2048_tier(self):
        self.assertEqual(
            self.module.get_next_memory_cpu_tier(9216, 2048), (10240, 2048)
        )
        self.assertEqual(
            self.module.get_next_memory_cpu_tier(15360, 2048), (16384, 2048)
        )

    def test_upgrade_from_cpu_2048_to_4096(self):
        result = self.module.get_next_memory_cpu_tier(16384, 2048)
        self.assertEqual(result, (17408, 4096))

    def test_increment_within_cpu_4096_tier(self):
        self.assertEqual(
            self.module.get_next_memory_cpu_tier(17408, 4096), (18432, 4096)
        )
        self.assertEqual(
            self.module.get_next_memory_cpu_tier(29696, 4096), (30720, 4096)
        )

    def test_uses_optimal_cpu_not_host_config(self):
        # Host over-provisioned CPU 4096 with 8192 MB; optimal for 9216 is 2048
        result = self.module.get_next_memory_cpu_tier(8192, 4096)
        self.assertEqual(result, (9216, 2048))

        # Host set CPU 2048 with 5120 MB; optimal for 6144 is 1024
        result = self.module.get_next_memory_cpu_tier(5120, 2048)
        self.assertEqual(result, (6144, 1024))

    def test_returns_none_at_max(self):
        result = self.module.get_next_memory_cpu_tier(30720, 4096)
        self.assertIsNone(result)

    def test_returns_none_beyond_max(self):
        result = self.module.get_next_memory_cpu_tier(31744, 4096)
        self.assertIsNone(result)


class TestIsStaleEvent(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_returns_false_when_task_def_matches(self):
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {
            "services": [{"taskDefinition": "arn:task-def:1"}]
        }
        result = self.module.is_stale_event(
            mock_client, "cluster", "svc", "arn:task-def:1"
        )
        self.assertFalse(result)

    def test_returns_true_when_task_def_differs(self):
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {
            "services": [{"taskDefinition": "arn:task-def:2"}]
        }
        result = self.module.is_stale_event(
            mock_client, "cluster", "svc", "arn:task-def:1"
        )
        self.assertTrue(result)

    def test_returns_false_when_no_services(self):
        mock_client = MagicMock()
        mock_client.describe_services.return_value = {"services": []}
        result = self.module.is_stale_event(
            mock_client, "cluster", "svc", "arn:task-def:1"
        )
        self.assertFalse(result)

    def test_returns_false_on_client_error(self):
        mock_client = MagicMock()
        mock_client.describe_services.side_effect = ClientError(
            error_response={"Error": {"Code": "Err"}},
            operation_name="DescribeServices",
        )
        result = self.module.is_stale_event(
            mock_client, "cluster", "svc", "arn:task-def:1"
        )
        self.assertFalse(result)


class TestCloneTaskDefinitionWithMemory(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_clones_and_updates_memory_and_cpu(self):
        mock_client = MagicMock()
        mock_client.describe_task_definition.return_value = {
            "taskDefinition": {
                "family": "worker-family",
                "taskDefinitionArn": "arn:old",
                "revision": 1,
                "status": "ACTIVE",
                "requiresAttributes": [],
                "compatibilities": ["FARGATE"],
                "registeredAt": "2026-01-01",
                "registeredBy": "arn:role",
                "memory": "2048",
                "cpu": "512",
                "containerDefinitions": [
                    {"name": "worker", "image": "img:latest"}
                ],
                "networkMode": "awsvpc",
                "requiresCompatibilities": ["FARGATE"],
            }
        }
        mock_client.register_task_definition.return_value = {
            "taskDefinition": {"taskDefinitionArn": "arn:new:2"}
        }

        result = self.module.clone_task_definition_with_memory(
            mock_client, "arn:old", 3072, 512
        )

        self.assertEqual(result, "arn:new:2")
        register_call = mock_client.register_task_definition.call_args
        task_def_arg = (
            register_call[1] if register_call[1] else register_call[0][0]
        )
        self.assertEqual(task_def_arg["memory"], "3072")
        self.assertEqual(task_def_arg["cpu"], "512")
        # Read-only fields should be stripped
        self.assertNotIn("taskDefinitionArn", task_def_arg)
        self.assertNotIn("revision", task_def_arg)
        self.assertNotIn("status", task_def_arg)
        self.assertNotIn("registeredAt", task_def_arg)
        self.assertNotIn("registeredBy", task_def_arg)
        self.assertNotIn("compatibilities", task_def_arg)
        self.assertNotIn("requiresAttributes", task_def_arg)

    def test_returns_none_on_describe_failure(self):
        mock_client = MagicMock()
        mock_client.describe_task_definition.side_effect = ClientError(
            error_response={"Error": {"Code": "Err"}},
            operation_name="DescribeTaskDefinition",
        )
        result = self.module.clone_task_definition_with_memory(
            mock_client, "arn:old", 3072, 512
        )
        self.assertIsNone(result)

    def test_returns_none_on_register_failure(self):
        mock_client = MagicMock()
        mock_client.describe_task_definition.return_value = {
            "taskDefinition": {
                "family": "worker-family",
                "memory": "2048",
                "cpu": "512",
                "containerDefinitions": [],
            }
        }
        mock_client.register_task_definition.side_effect = ClientError(
            error_response={"Error": {"Code": "Err"}},
            operation_name="RegisterTaskDefinition",
        )
        result = self.module.clone_task_definition_with_memory(
            mock_client, "arn:old", 3072, 512
        )
        self.assertIsNone(result)


class TestUpdateServiceWithNewTaskDef(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def test_success(self):
        mock_client = MagicMock()
        result = self.module.update_service_with_new_task_def(
            mock_client, "cluster", "svc", "arn:new"
        )
        self.assertTrue(result)
        mock_client.update_service.assert_called_once_with(
            cluster="cluster",
            service="svc",
            taskDefinition="arn:new",
            forceNewDeployment=True,
        )

    def test_failure(self):
        mock_client = MagicMock()
        mock_client.update_service.side_effect = ClientError(
            error_response={"Error": {"Code": "Err"}},
            operation_name="UpdateService",
        )
        result = self.module.update_service_with_new_task_def(
            mock_client, "cluster", "svc", "arn:new"
        )
        self.assertFalse(result)


def _make_oom_event(
    service_name="challenge-queue_service",
    task_def_arn="arn:aws:ecs:us-east-1:123:task-def/test:1",
):
    return {
        "detail": {
            "lastStatus": "STOPPED",
            "stoppedReason": "OutOfMemoryError: Container killed due to memory usage",
            "group": f"service:{service_name}",
            "taskDefinitionArn": task_def_arn,
            "containers": [{"exitCode": 137, "name": "worker"}],
        }
    }


def _mock_ecs_for_handler(
    mock_ecs,
    challenge_pk="42",
    current_memory="2048",
    current_cpu="512",
    service_task_def="arn:aws:ecs:us-east-1:123:task-def/test:1",
    new_task_def_arn="arn:aws:ecs:us-east-1:123:task-def/test:2",
):
    """Set up common mock responses for handler tests."""
    # describe_services: first call for is_stale_event, second for
    # get_challenge_pk
    mock_ecs.describe_services.return_value = {
        "services": [
            {
                "taskDefinition": service_task_def,
                "tags": [{"key": "challenge_pk", "value": challenge_pk}],
            }
        ]
    }
    mock_ecs.describe_task_definition.return_value = {
        "taskDefinition": {
            "family": "worker-family",
            "memory": current_memory,
            "cpu": current_cpu,
            "containerDefinitions": [
                {"name": "worker", "image": "img:latest"}
            ],
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
        }
    }
    mock_ecs.register_task_definition.return_value = {
        "taskDefinition": {"taskDefinitionArn": new_task_def_arn}
    }


class TestHandler(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
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
    def test_skips_stale_events(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        mock_ecs.describe_services.return_value = {
            "services": [{"taskDefinition": "arn:task-def:NEW"}]
        }

        event = _make_oom_event(task_def_arn="arn:task-def:OLD")
        result = self.module.handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        self.assertIn("Stale OOM event", result["body"])

    @patch("boto3.client")
    def test_handles_missing_challenge_pk_tag(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        task_def_arn = "arn:aws:ecs:us-east-1:123:task-def/test:1"
        mock_ecs.describe_services.return_value = {
            "services": [{"taskDefinition": task_def_arn, "tags": []}]
        }

        event = _make_oom_event(task_def_arn=task_def_arn)
        result = self.module.handler(event, None)

        self.assertEqual(result["statusCode"], 400)
        self.assertIn("No challenge_pk tag found", result["body"])

    @patch("boto3.client")
    def test_auto_retry_increases_memory(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        task_def_arn = "arn:aws:ecs:us-east-1:123:task-def/test:1"
        new_task_def_arn = "arn:aws:ecs:us-east-1:123:task-def/test:2"
        _mock_ecs_for_handler(
            mock_ecs,
            current_memory="2048",
            current_cpu="512",
            service_task_def=task_def_arn,
            new_task_def_arn=new_task_def_arn,
        )

        self.module.notify_evalai_api = MagicMock(return_value=True)

        event = _make_oom_event(task_def_arn=task_def_arn)
        result = self.module.handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["old_memory"], 2048)
        self.assertEqual(body["new_memory"], 3072)
        self.assertEqual(body["old_cpu"], 512)
        self.assertEqual(body["new_cpu"], 512)
        self.assertEqual(body["task_def_arn"], new_task_def_arn)

        # Verify service was updated with new task def (not scaled to 0)
        mock_ecs.update_service.assert_called_once_with(
            cluster="test-cluster",
            service="challenge-queue_service",
            taskDefinition=new_task_def_arn,
            forceNewDeployment=True,
        )

        # Verify API payload includes worker config fields
        api_call = self.module.notify_evalai_api.call_args[0]
        self.assertEqual(api_call[0], "42")
        payload = api_call[1]
        self.assertEqual(payload["worker_memory"], 3072)
        self.assertEqual(payload["worker_cpu_cores"], 512)
        self.assertEqual(payload["task_def_arn"], new_task_def_arn)
        self.assertTrue(payload["send_email"])
        self.assertIn(
            "Auto-increased memory", payload["evaluation_module_error"]
        )

    @patch("boto3.client")
    def test_auto_retry_upgrades_cpu_tier(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        task_def_arn = "arn:task-def:1"
        new_task_def_arn = "arn:task-def:2"
        _mock_ecs_for_handler(
            mock_ecs,
            current_memory="4096",
            current_cpu="512",
            service_task_def=task_def_arn,
            new_task_def_arn=new_task_def_arn,
        )

        self.module.notify_evalai_api = MagicMock(return_value=True)

        event = _make_oom_event(task_def_arn=task_def_arn)
        result = self.module.handler(event, None)

        body = json.loads(result["body"])
        self.assertEqual(body["new_memory"], 5120)
        self.assertEqual(body["new_cpu"], 1024)

    @patch("boto3.client")
    def test_max_memory_reached_scales_to_zero(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        task_def_arn = "arn:task-def:1"
        _mock_ecs_for_handler(
            mock_ecs,
            current_memory="30720",
            current_cpu="4096",
            service_task_def=task_def_arn,
        )

        self.module.notify_evalai_api = MagicMock(return_value=True)

        event = _make_oom_event(task_def_arn=task_def_arn)
        result = self.module.handler(event, None)

        body = json.loads(result["body"])
        self.assertIn("Max memory reached", body["message"])

        # Verify service was scaled to 0
        mock_ecs.update_service.assert_called_once_with(
            cluster="test-cluster",
            service="challenge-queue_service",
            desiredCount=0,
        )

        # Verify error message mentions max
        api_call = self.module.notify_evalai_api.call_args[0]
        payload = api_call[1]
        self.assertIn(
            "Maximum Fargate memory reached",
            payload["evaluation_module_error"],
        )
        self.assertTrue(payload["send_email"])

    @patch("boto3.client")
    def test_clone_failure_scales_to_zero(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        task_def_arn = "arn:task-def:1"
        _mock_ecs_for_handler(
            mock_ecs,
            current_memory="2048",
            current_cpu="512",
            service_task_def=task_def_arn,
        )
        mock_ecs.register_task_definition.side_effect = ClientError(
            error_response={"Error": {"Code": "Err"}},
            operation_name="RegisterTaskDefinition",
        )

        self.module.notify_evalai_api = MagicMock(return_value=True)

        event = _make_oom_event(task_def_arn=task_def_arn)
        result = self.module.handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        # Verify fallback: scaled to 0
        mock_ecs.update_service.assert_called_once_with(
            cluster="test-cluster",
            service="challenge-queue_service",
            desiredCount=0,
        )

    @patch("boto3.client")
    def test_service_update_failure_scales_to_zero(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        task_def_arn = "arn:task-def:1"
        _mock_ecs_for_handler(
            mock_ecs,
            current_memory="2048",
            current_cpu="512",
            service_task_def=task_def_arn,
        )
        # register succeeds, but update_service fails
        mock_ecs.update_service.side_effect = ClientError(
            error_response={"Error": {"Code": "Err"}},
            operation_name="UpdateService",
        )

        self.module.notify_evalai_api = MagicMock(return_value=True)

        event = _make_oom_event(task_def_arn=task_def_arn)
        result = self.module.handler(event, None)

        self.assertEqual(result["statusCode"], 500)
        self.assertIn("Failed to update service", result["body"])

    @patch("boto3.client")
    def test_exit_code_137_triggers_auto_retry(self, mock_boto3_client):
        mock_ecs = MagicMock()
        mock_boto3_client.return_value = mock_ecs

        task_def_arn = "arn:task-def:1"
        new_task_def_arn = "arn:task-def:2"
        _mock_ecs_for_handler(
            mock_ecs,
            challenge_pk="99",
            current_memory="1024",
            current_cpu="512",
            service_task_def=task_def_arn,
            new_task_def_arn=new_task_def_arn,
        )

        self.module.notify_evalai_api = MagicMock(return_value=True)

        event = {
            "detail": {
                "lastStatus": "STOPPED",
                "stoppedReason": "Essential container exited",
                "containers": [{"exitCode": 137, "name": "worker"}],
                "group": "service:queue_service",
                "taskDefinitionArn": task_def_arn,
            }
        }

        result = self.module.handler(event, None)

        self.assertEqual(result["statusCode"], 200)
        body = json.loads(result["body"])
        self.assertEqual(body["new_memory"], 2048)


if __name__ == "__main__":
    unittest.main()
