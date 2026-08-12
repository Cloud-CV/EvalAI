import importlib.util
import json
import os
import sys
import unittest
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from botocore.exceptions import ClientError

ENV_VARS = {
    "AWS_REGION": "us-east-1",
    "ECS_CLUSTER": "evalai-prod-cluster",
    "ENVIRONMENT": "production",
    "EVALAI_API_SERVER": "https://eval.ai",
    "LAMBDA_AUTH_TOKEN": "test-token",
    "EVENTBRIDGE_SCHEDULER_ROLE_ARN": "arn:aws:iam::123:role/scheduler",
    "CHALLENGE_CLEANUP_LAMBDA_ARN": (
        "arn:aws:lambda:us-east-1:123:function:cleanup"
    ),
}


def _import_lambda_module():
    spec = importlib.util.spec_from_file_location(
        "challenge_cleanup_lambda",
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "scripts",
            "lambda",
            "challenge_cleanup_lambda.py",
        ),
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _client_error(code):
    return ClientError(
        {"Error": {"Code": code, "Message": code}},
        "DeleteService",
    )


class TestChallengeCleanupLambda(unittest.TestCase):
    def setUp(self):
        self.env_patcher = patch.dict(os.environ, ENV_VARS)
        self.env_patcher.start()
        self.module = _import_lambda_module()

    def tearDown(self):
        self.env_patcher.stop()

    def _mock_aws_clients(self, mock_boto_client, *, delete_error=None):
        mock_ecs = MagicMock()
        mock_autoscaling = MagicMock()
        mock_cloudwatch = MagicMock()
        mock_logs = MagicMock()
        mock_scheduler = MagicMock()

        if delete_error is not None:
            mock_ecs.delete_service.side_effect = delete_error
        else:
            mock_ecs.delete_service.return_value = {
                "service": {
                    "taskDefinition": (
                        "arn:aws:ecs:us-east-1:123:task-definition/chal:1"
                    )
                }
            }

        def client_factory(service_name, **kwargs):
            return {
                "ecs": mock_ecs,
                "application-autoscaling": mock_autoscaling,
                "cloudwatch": mock_cloudwatch,
                "logs": mock_logs,
                "scheduler": mock_scheduler,
            }[service_name]

        mock_boto_client.side_effect = client_factory
        return mock_ecs

    @patch("boto3.client")
    @patch("challenge_cleanup_lambda.clear_challenge_worker_state")
    @patch("challenge_cleanup_lambda.get_pending_submission_count")
    def test_cleanup_clears_db_worker_state_after_delete(
        self, mock_pending, mock_clear_state, mock_boto_client
    ):
        mock_pending.return_value = 0
        self._mock_aws_clients(mock_boto_client)

        response = self.module.handler(
            {"challenge_pk": 42, "queue_name": "chal-queue"}, None
        )

        self.assertEqual(response["statusCode"], 200)
        mock_clear_state.assert_called_once_with(42)

    @patch("boto3.client")
    @patch("challenge_cleanup_lambda.clear_challenge_worker_state")
    @patch("challenge_cleanup_lambda.get_pending_submission_count")
    def test_cleanup_clears_db_when_service_already_gone(
        self, mock_pending, mock_clear_state, mock_boto_client
    ):
        mock_pending.return_value = 0
        self._mock_aws_clients(
            mock_boto_client,
            delete_error=_client_error("ServiceNotFoundException"),
        )

        response = self.module.handler(
            {"challenge_pk": 42, "queue_name": "chal-queue"}, None
        )

        self.assertEqual(response["statusCode"], 200)
        mock_clear_state.assert_called_once_with(42)

    @patch("boto3.client")
    @patch("challenge_cleanup_lambda.clear_challenge_worker_state")
    @patch("challenge_cleanup_lambda.get_pending_submission_count")
    def test_cleanup_skips_db_clear_when_delete_fails(
        self, mock_pending, mock_clear_state, mock_boto_client
    ):
        mock_pending.return_value = 0
        self._mock_aws_clients(
            mock_boto_client,
            delete_error=_client_error("AccessDeniedException"),
        )

        with self.assertRaises(RuntimeError) as ctx:
            self.module.handler(
                {"challenge_pk": 42, "queue_name": "chal-queue"}, None
            )

        self.assertIn("still exists", str(ctx.exception))
        mock_clear_state.assert_not_called()

    @patch("boto3.client")
    @patch("challenge_cleanup_lambda.clear_challenge_worker_state")
    @patch("challenge_cleanup_lambda.get_pending_submission_count")
    def test_cleanup_raises_when_db_sync_fails(
        self, mock_pending, mock_clear_state, mock_boto_client
    ):
        mock_pending.return_value = 0
        self._mock_aws_clients(mock_boto_client)
        mock_clear_state.side_effect = RuntimeError("API down")

        with self.assertRaises(RuntimeError) as ctx:
            self.module.handler(
                {"challenge_pk": 42, "queue_name": "chal-queue"}, None
            )

        self.assertIn("failed to clear DB worker state", str(ctx.exception))

    @patch("boto3.client")
    @patch("challenge_cleanup_lambda.clear_challenge_worker_state")
    @patch("challenge_cleanup_lambda.get_pending_submission_count")
    def test_pending_submissions_skip_cleanup_and_db_clear(
        self, mock_pending, mock_clear_state, mock_boto_client
    ):
        mock_pending.return_value = 3
        mock_scheduler = MagicMock()
        mock_boto_client.return_value = mock_scheduler

        response = self.module.handler(
            {"challenge_pk": 42, "queue_name": "chal-queue"}, None
        )

        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("pending", body["message"])
        mock_clear_state.assert_not_called()
        mock_scheduler.create_schedule.assert_called_once()

    @patch("boto3.client")
    def test_reschedule_cleanup_uses_unique_schedule_name(
        self, mock_boto_client
    ):
        """
        ActionAfterCompletion=DELETE only removes the invoking schedule
        after the Lambda finishes. create_schedule with the fixed base
        name therefore conflicts; retries must use a distinct name.
        """
        mock_scheduler = MagicMock()
        mock_boto_client.return_value = mock_scheduler

        ok = self.module.reschedule_cleanup(42, "chal-queue")

        self.assertTrue(ok)
        mock_scheduler.create_schedule.assert_called_once()
        kwargs = mock_scheduler.create_schedule.call_args.kwargs
        schedule_name = kwargs["Name"]
        base_name = "evalai-cleanup-challenge-production-42"
        self.assertNotEqual(schedule_name, base_name)
        self.assertTrue(schedule_name.startswith(base_name + "-r"))
        self.assertLessEqual(len(schedule_name), 64)
        self.assertEqual(kwargs["ActionAfterCompletion"], "DELETE")
        self.assertIn("chal-queue", kwargs["Target"]["Input"])

    @patch("boto3.client")
    @patch("challenge_cleanup_lambda.clear_challenge_worker_state")
    @patch("challenge_cleanup_lambda.get_pending_submission_count")
    def test_pending_check_failure_reschedules_with_unique_name(
        self, mock_pending, mock_clear_state, mock_boto_client
    ):
        mock_pending.side_effect = RuntimeError("API down")
        mock_scheduler = MagicMock()
        mock_boto_client.return_value = mock_scheduler

        response = self.module.handler(
            {"challenge_pk": 42, "queue_name": "chal-queue"}, None
        )

        self.assertEqual(response["statusCode"], 200)
        mock_clear_state.assert_not_called()
        kwargs = mock_scheduler.create_schedule.call_args.kwargs
        self.assertNotEqual(
            kwargs["Name"],
            "evalai-cleanup-challenge-production-42",
        )

    @patch("challenge_cleanup_lambda.urlopen")
    def test_clear_challenge_worker_state_posts_to_api(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(
            {"message": "ok", "workers": None, "task_def_arn": ""}
        ).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_response.__exit__.return_value = False
        mock_urlopen.return_value = mock_response

        payload = self.module.clear_challenge_worker_state(7)

        self.assertEqual(payload["workers"], None)
        request = mock_urlopen.call_args[0][0]
        self.assertEqual(request.get_method(), "POST")
        self.assertIn("/clear_worker_state/", request.full_url)
        self.assertEqual(
            request.get_header("Authorization"), "Bearer test-token"
        )

    @patch("challenge_cleanup_lambda.urlopen")
    def test_clear_challenge_worker_state_surfaces_http_error(
        self, mock_urlopen
    ):
        mock_urlopen.side_effect = HTTPError(
            url="https://eval.ai/api/...",
            code=500,
            msg="server error",
            hdrs=None,
            fp=MagicMock(read=MagicMock(return_value=b"boom")),
        )

        with self.assertRaises(RuntimeError) as ctx:
            self.module.clear_challenge_worker_state(7)

        self.assertIn("HTTP 500", str(ctx.exception))
