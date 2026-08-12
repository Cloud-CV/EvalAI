import json
import os
import unittest
from http import HTTPStatus
from unittest import TestCase, mock
from unittest.mock import MagicMock, mock_open, patch

import pytest
from botocore.exceptions import ClientError, NoCredentialsError, WaiterError
from celery.exceptions import MaxRetriesExceededError
from challenges.aws_utils import (
    _file_content_changed,
    _get_challenge_cluster,
    _get_ecs_service_task_definition_arn,
    _is_inactive_task_definition_error,
    _resolve_nodegroup_name,
    _sync_challenge_task_def_from_service,
    _version_at_least,
    build_task_definition_dict,
    challenge_approval_callback,
    cleanup_auto_scaling_for_service,
    create_ec2_instance,
    create_eks_cluster,
    create_eks_cluster_subnets,
    create_eks_nodegroup,
    create_nodegroup_for_challenge,
    create_service_by_challenge_pk,
    delete_challenge_cleanup_schedule,
    delete_log_group,
    delete_service_by_challenge_pk,
    delete_workers,
    describe_ec2_instance,
    eks_nodegroup_config_change_callback,
    ensure_workers_for_submission,
    get_capacity_provider_strategy,
    get_code_upload_setup_meta_for_challenge,
    get_current_ecr_env,
    get_deployed_worker_image_urls,
    get_ecs_service_name,
    get_evalai_code_upload_worker_ecr_image,
    get_evalai_submission_worker_ecr_image,
    get_evalai_submission_worker_ecr_prefixes,
    get_image_settings_for_challenge,
    get_logs_from_cloudwatch,
    get_worker_image_for_challenge,
    is_evalai_managed_submission_worker_image,
    load_aws_api_kwargs,
    recreate_eks_nodegroup,
    refresh_task_definition_for_challenge,
    refresh_worker_task_definitions,
    register_task_def_by_challenge_pk,
    restart_ec2_instance,
    restart_workers,
    restart_workers_signal_callback,
    sanitize_ecs_resource_name,
    scale_resources,
    scale_workers,
    schedule_challenge_cleanup,
    service_manager,
    setup_auto_scaling_for_service,
    setup_ec2,
    setup_eks_autoscale_cross_account_role,
    setup_eks_cluster,
    start_ec2_instance,
    start_workers,
    stop_ec2_instance,
    stop_workers,
    strip_fifo_suffix,
    terminate_ec2_instance,
    trigger_eks_node_autoscale,
    update_challenge_cleanup_schedule,
    update_eks_nodegroup_scaling,
    update_evalai_worker_image_tag,
    update_service_by_challenge_pk,
    update_sqs_retention_period,
    update_sqs_retention_period_task,
    validate_eks_nodegroup_config,
)
from challenges.models import Challenge, ChallengeEvaluationCluster
from challenges.worker_utils import (
    ensure_challenge_worker_python_version,
    normalize_worker_python_version,
)
from django.conf import settings
from django.contrib.auth.models import User
from django.core import serializers
from django.db import DatabaseError
from django.test import override_settings
from hosts.models import ChallengeHostTeam


class AWSUtilsTestCase(TestCase):
    @mock.patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @mock.patch("challenges.utils.get_challenge_model")
    def test_get_code_upload_setup_meta_for_challenge_with_host_credentials(
        self, mock_get_challenge_model, mock_get_cluster
    ):
        # Mock the return value of get_challenge_model
        mock_challenge = mock_get_challenge_model.return_value
        mock_challenge.use_host_credentials = True

        mock_challenge_evaluation_cluster = mock_get_cluster.return_value
        mock_challenge_evaluation_cluster.subnet_1_id = "subnet1"
        mock_challenge_evaluation_cluster.subnet_2_id = "subnet2"
        mock_challenge_evaluation_cluster.security_group_id = "sg"
        mock_challenge_evaluation_cluster.node_group_arn_role = (
            "node_group_arn_role"
        )
        mock_challenge_evaluation_cluster.eks_arn_role = "eks_arn_role"

        # Call the function under test
        result = get_code_upload_setup_meta_for_challenge(1)

        # Expected result
        expected_result = {
            "SUBNET_1": "subnet1",
            "SUBNET_2": "subnet2",
            "SUBNET_SECURITY_GROUP": "sg",
            "EKS_NODEGROUP_ROLE_ARN": "node_group_arn_role",
            "EKS_CLUSTER_ROLE_ARN": "eks_arn_role",
        }

        # Assertions
        self.assertEqual(result, expected_result)
        mock_get_cluster.assert_called_once_with(challenge=mock_challenge)

    @mock.patch("challenges.utils.get_challenge_model")
    @mock.patch(
        "challenges.aws_utils.VPC_DICT",
        {
            "SUBNET_1": "vpc_subnet1",
            "SUBNET_2": "vpc_subnet2",
            "SUBNET_SECURITY_GROUP": "vpc_sg",
        },
    )
    @mock.patch("challenges.aws_utils.settings")
    def test_get_code_upload_setup_meta_for_challenge_without_host_credentials(
        self, mock_settings, mock_get_challenge_model
    ):
        # Mock the return value of get_challenge_model
        mock_challenge = mock_get_challenge_model.return_value
        mock_challenge.use_host_credentials = False

        # Mock settings for the else case
        mock_settings.EKS_NODEGROUP_ROLE_ARN = "vpc_node_group_arn_role"
        mock_settings.EKS_CLUSTER_ROLE_ARN = "vpc_eks_arn_role"

        # Call the function under test
        result = get_code_upload_setup_meta_for_challenge(1)

        # Expected result
        expected_result = {
            "SUBNET_1": "vpc_subnet1",
            "SUBNET_2": "vpc_subnet2",
            "SUBNET_SECURITY_GROUP": "vpc_sg",
            "EKS_NODEGROUP_ROLE_ARN": "vpc_node_group_arn_role",
            "EKS_CLUSTER_ROLE_ARN": "vpc_eks_arn_role",
        }

        # Assertions
        self.assertEqual(result, expected_result)


@pytest.fixture
def mock_client():
    return MagicMock()


@pytest.fixture
def mock_challenge():
    return MagicMock(queue="dummy_queue")


@pytest.fixture
def client_token():
    return "dummy_client_token"


@pytest.fixture
def num_of_tasks():
    return 3


class TestCreateServiceByChallengePk:
    def test_create_service_success(
        self, mock_client, mock_challenge, client_token
    ):
        mock_challenge.workers = None
        mock_challenge.task_def_arn = "valid_task_def_arn"
        mock_challenge.use_fargate_spot = False  # Uses launchType FARGATE path

        response_metadata = {"HTTPStatusCode": HTTPStatus.OK}
        mock_client.create_service.return_value = {
            "ResponseMetadata": response_metadata
        }

        with patch(
            "challenges.aws_utils.register_task_def_by_challenge_pk",
            return_value={"ResponseMetadata": response_metadata},
        ), patch(
            "challenges.aws_utils.setup_auto_scaling_for_service",
        ) as mock_auto_scaling, patch(
            "challenges.aws_utils.schedule_challenge_cleanup",
        ) as mock_schedule:
            response = create_service_by_challenge_pk(
                mock_client, mock_challenge, client_token
            )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
        mock_challenge.save.assert_called_once()
        assert mock_challenge.workers == 1
        mock_auto_scaling.assert_called_once_with(mock_challenge)
        mock_schedule.assert_called_once_with(mock_challenge)

    def test_create_service_client_error(
        self, mock_client, mock_challenge, client_token
    ):
        mock_challenge.workers = None
        mock_challenge.task_def_arn = "valid_task_def_arn"
        mock_challenge.use_fargate_spot = False  # Uses launchType FARGATE path

        mock_client.create_service.side_effect = ClientError(
            error_response={
                "Error": {"Code": "SomeError"},
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            },
            operation_name="CreateService",
        )

        with patch(
            "challenges.aws_utils.register_task_def_by_challenge_pk",
            return_value={
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
            },
        ), patch(
            "challenges.aws_utils.setup_auto_scaling_for_service",
        ), patch(
            "challenges.aws_utils.schedule_challenge_cleanup",
        ):
            response = create_service_by_challenge_pk(
                mock_client, mock_challenge, client_token
            )

        assert (
            response["ResponseMetadata"]["HTTPStatusCode"]
            == HTTPStatus.BAD_REQUEST
        )

    def test_service_already_exists(
        self, mock_client, mock_challenge, client_token
    ):
        mock_challenge.workers = 1

        response = create_service_by_challenge_pk(
            mock_client, mock_challenge, client_token
        )

        assert (
            response["ResponseMetadata"]["HTTPStatusCode"]
            == HTTPStatus.BAD_REQUEST
        )
        assert "Worker service for challenge" in response["Error"]

    def test_register_task_def_fails(
        self, mock_client, mock_challenge, client_token
    ):
        mock_challenge.workers = None
        mock_challenge.task_def_arn = (
            None  # Simulate task definition is not yet registered
        )

        register_task_response = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST}
        }

        with patch(
            "challenges.aws_utils.register_task_def_by_challenge_pk",
            return_value=register_task_response,
        ):
            response = create_service_by_challenge_pk(
                mock_client, mock_challenge, client_token
            )

        assert (
            response["ResponseMetadata"]["HTTPStatusCode"]
            == HTTPStatus.BAD_REQUEST
        )


def test_update_service_success(mock_client, mock_challenge, num_of_tasks):
    mock_challenge.queue = "dummy_queue"
    mock_challenge.task_def_arn = "valid_task_def_arn"

    response_metadata = {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
    mock_client.update_service.return_value = response_metadata
    mock_client.describe_services.return_value = {
        "services": [
            {
                "status": "ACTIVE",
                "taskDefinition": "valid_task_def_arn",
            }
        ]
    }

    response = update_service_by_challenge_pk(
        mock_client, mock_challenge, num_of_tasks
    )

    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    mock_challenge.save.assert_called_once()
    assert mock_challenge.workers == num_of_tasks


def test_update_service_client_error(
    mock_client, mock_challenge, num_of_tasks
):
    mock_challenge.queue = "dummy_queue"
    mock_challenge.task_def_arn = "valid_task_def_arn"

    mock_client.update_service.side_effect = ClientError(
        error_response={
            "Error": {"Code": "ServiceError"},
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        },
        operation_name="UpdateService",
    )

    response = update_service_by_challenge_pk(
        mock_client, mock_challenge, num_of_tasks
    )

    assert (
        response["ResponseMetadata"]["HTTPStatusCode"]
        == HTTPStatus.BAD_REQUEST
    )
    assert "ServiceError" in response["Error"]["Code"]


def test_update_service_force_new_deployment(
    mock_client, mock_challenge, num_of_tasks
):
    mock_challenge.queue = "dummy_queue"
    mock_challenge.task_def_arn = "valid_task_def_arn"

    response_metadata = {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
    mock_client.update_service.return_value = response_metadata

    response = update_service_by_challenge_pk(
        mock_client, mock_challenge, num_of_tasks, force_new_deployment=True
    )

    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    mock_challenge.save.assert_called_once()
    assert mock_challenge.workers == num_of_tasks


def test_update_service_scale_only_omits_task_definition(
    mock_client, mock_challenge, num_of_tasks
):
    mock_challenge.queue = "dummy_queue"
    mock_challenge.task_def_arn = "inactive_task_def_arn"

    response_metadata = {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
    mock_client.update_service.return_value = response_metadata
    mock_client.describe_services.return_value = {
        "services": [
            {
                "status": "ACTIVE",
                "taskDefinition": "active_task_def_arn",
            }
        ]
    }

    response = update_service_by_challenge_pk(
        mock_client, mock_challenge, num_of_tasks
    )

    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    mock_client.update_service.assert_called_once_with(
        cluster=mock.ANY,
        service="dummy_queue_service",
        desiredCount=num_of_tasks,
    )
    assert mock_challenge.task_def_arn == "active_task_def_arn"


def test_update_service_success_when_sync_describe_services_fails(
    mock_client, mock_challenge, num_of_tasks
):
    """A describe_services hiccup during self-heal must not mask a
    successful scale (previously this returned describe_services'
    ClientError instead of the real success response)."""
    mock_challenge.queue = "dummy_queue"
    mock_challenge.task_def_arn = "valid_task_def_arn"

    response_metadata = {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
    mock_client.update_service.return_value = response_metadata
    mock_client.describe_services.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "ThrottlingException",
                "Message": "Rate exceeded",
            },
            "ResponseMetadata": {
                "HTTPStatusCode": HTTPStatus.TOO_MANY_REQUESTS
            },
        },
        operation_name="DescribeServices",
    )

    response = update_service_by_challenge_pk(
        mock_client, mock_challenge, num_of_tasks
    )

    assert response is response_metadata
    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    assert mock_challenge.workers == num_of_tasks
    assert mock_challenge.task_def_arn == "valid_task_def_arn"
    mock_client.describe_services.assert_called_once()


def test_update_service_inactive_task_def_retries_after_sync_on_redeploy(
    mock_client, mock_challenge, num_of_tasks
):
    mock_challenge.queue = "dummy_queue"
    mock_challenge.task_def_arn = "inactive_task_def_arn"

    inactive_error = ClientError(
        error_response={
            "Error": {
                "Code": "ClientException",
                "Message": (
                    "An error occurred (ClientException) when calling the "
                    "UpdateService operation: TaskDefinition is inactive"
                ),
            },
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        },
        operation_name="UpdateService",
    )
    response_metadata = {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
    mock_client.update_service.side_effect = [
        inactive_error,
        response_metadata,
    ]
    mock_client.describe_services.return_value = {
        "services": [
            {
                "status": "ACTIVE",
                "taskDefinition": "active_task_def_arn",
            }
        ]
    }

    response = update_service_by_challenge_pk(
        mock_client, mock_challenge, num_of_tasks, force_new_deployment=True
    )

    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    assert mock_client.update_service.call_count == 2
    assert mock_challenge.task_def_arn == "active_task_def_arn"
    retry_call_kwargs = mock_client.update_service.call_args_list[1].kwargs
    assert retry_call_kwargs["taskDefinition"] == "active_task_def_arn"


def test_update_service_redeploy_does_not_raise_when_sync_describe_services_fails(
    mock_client, mock_challenge, num_of_tasks
):
    """A describe_services hiccup while syncing before the forced-redeploy
    retry must not propagate unhandled out of update_service_by_challenge_pk
    (this call sits directly inside the except block with no nested try)."""
    mock_challenge.queue = "dummy_queue"
    mock_challenge.task_def_arn = "inactive_task_def_arn"

    inactive_error = ClientError(
        error_response={
            "Error": {
                "Code": "ClientException",
                "Message": (
                    "An error occurred (ClientException) when calling the "
                    "UpdateService operation: TaskDefinition is inactive"
                ),
            },
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        },
        operation_name="UpdateService",
    )
    mock_client.update_service.side_effect = inactive_error
    mock_client.describe_services.side_effect = ClientError(
        error_response={
            "Error": {
                "Code": "ThrottlingException",
                "Message": "Rate exceeded",
            },
            "ResponseMetadata": {
                "HTTPStatusCode": HTTPStatus.TOO_MANY_REQUESTS
            },
        },
        operation_name="DescribeServices",
    )

    response = update_service_by_challenge_pk(
        mock_client, mock_challenge, num_of_tasks, force_new_deployment=True
    )

    assert (
        response["ResponseMetadata"]["HTTPStatusCode"]
        == HTTPStatus.BAD_REQUEST
    )
    assert mock_client.update_service.call_count == 1
    assert mock_challenge.task_def_arn == "inactive_task_def_arn"
    mock_client.describe_services.assert_called_once()


def test_update_service_redeploy_retry_client_error_returns_retry_response(
    mock_client, mock_challenge, num_of_tasks
):
    """If the retried update_service call (after a successful sync) itself
    fails with a ClientError, that error's response must be returned."""
    mock_challenge.queue = "dummy_queue"
    mock_challenge.task_def_arn = "inactive_task_def_arn"

    inactive_error = ClientError(
        error_response={
            "Error": {
                "Code": "ClientException",
                "Message": (
                    "An error occurred (ClientException) when calling the "
                    "UpdateService operation: TaskDefinition is inactive"
                ),
            },
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        },
        operation_name="UpdateService",
    )
    retry_error = ClientError(
        error_response={
            "Error": {
                "Code": "ThrottlingException",
                "Message": "Rate exceeded",
            },
            "ResponseMetadata": {
                "HTTPStatusCode": HTTPStatus.TOO_MANY_REQUESTS
            },
        },
        operation_name="UpdateService",
    )
    mock_client.update_service.side_effect = [inactive_error, retry_error]
    mock_client.describe_services.return_value = {
        "services": [
            {
                "status": "ACTIVE",
                "taskDefinition": "active_task_def_arn",
            }
        ]
    }

    response = update_service_by_challenge_pk(
        mock_client, mock_challenge, num_of_tasks, force_new_deployment=True
    )

    assert (
        response["ResponseMetadata"]["HTTPStatusCode"]
        == HTTPStatus.TOO_MANY_REQUESTS
    )
    assert mock_client.update_service.call_count == 2


def test_is_inactive_task_definition_error_with_plain_dict():
    error_response = {
        "Error": {
            "Code": "ClientException",
            "Message": "TaskDefinition is inactive",
        }
    }
    assert _is_inactive_task_definition_error(error_response) is True
    assert (
        _is_inactive_task_definition_error({"Error": {"Code": "Other"}})
        is False
    )


def test_get_ecs_service_task_definition_arn_no_services(mock_client):
    mock_client.describe_services.return_value = {"services": []}
    assert (
        _get_ecs_service_task_definition_arn(mock_client, "dummy_service")
        is None
    )


def test_get_ecs_service_task_definition_arn_inactive_service(mock_client):
    mock_client.describe_services.return_value = {
        "services": [{"status": "INACTIVE", "taskDefinition": "some_arn"}]
    }
    assert (
        _get_ecs_service_task_definition_arn(mock_client, "dummy_service")
        is None
    )


def test_sync_challenge_task_def_from_service_no_active_service(
    mock_client, mock_challenge
):
    mock_challenge.task_def_arn = "inactive_task_def_arn"
    mock_client.describe_services.return_value = {"services": []}

    result = _sync_challenge_task_def_from_service(
        mock_client, mock_challenge, "dummy_service"
    )

    assert result is False
    assert mock_challenge.task_def_arn == "inactive_task_def_arn"


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_delete_service_continues_when_task_def_inactive(
    mock_cleanup, mock_challenge, mock_client
):
    mock_challenge.workers = 0
    mock_challenge.task_def_arn = "inactive_task_def_arn"
    response_metadata_ok = {
        "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
    }
    inactive_error = ClientError(
        error_response={
            "Error": {
                "Code": "ClientException",
                "Message": (
                    "An error occurred (ClientException) when calling the "
                    "DeregisterTaskDefinition operation: TaskDefinition is "
                    "inactive"
                ),
            },
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        },
        operation_name="DeregisterTaskDefinition",
    )

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        mock_client.delete_service.return_value = response_metadata_ok
        mock_client.deregister_task_definition.side_effect = inactive_error

        response = delete_service_by_challenge_pk(mock_challenge)

    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    assert mock_challenge.task_def_arn == ""


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_delete_service_success_when_workers_zero(
    mock_cleanup, mock_challenge, mock_client
):
    mock_challenge.workers = 0
    mock_challenge.task_def_arn = (
        "valid_task_def_arn"  # Ensure task_def_arn is set to a valid string
    )
    response_metadata_ok = {
        "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
    }

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        mock_client.delete_service.return_value = response_metadata_ok

        response = delete_service_by_challenge_pk(mock_challenge)

    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    mock_challenge.save.assert_called()
    mock_client.deregister_task_definition.assert_called_once_with(
        taskDefinition="valid_task_def_arn"
    )
    mock_cleanup.assert_called_once_with(mock_challenge)


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_delete_service_success_when_workers_not_zero(
    mock_cleanup, mock_challenge, mock_client
):
    mock_challenge.workers = 3
    mock_challenge.task_def_arn = "valid_task_def_arn"
    response_metadata_ok = {
        "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
    }

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        with patch(
            "challenges.aws_utils.update_service_by_challenge_pk",
            return_value=response_metadata_ok,
        ):
            mock_client.delete_service.return_value = response_metadata_ok

            response = delete_service_by_challenge_pk(mock_challenge)

    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    mock_challenge.save.assert_called()
    mock_client.deregister_task_definition.assert_called_once_with(
        taskDefinition="valid_task_def_arn"
    )
    mock_cleanup.assert_called_once_with(mock_challenge)


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_update_service_failure(mock_cleanup, mock_challenge, mock_client):
    mock_challenge.workers = 3
    response_metadata_error = {
        "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST}
    }

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        with patch(
            "challenges.aws_utils.update_service_by_challenge_pk",
            return_value=response_metadata_error,
        ):
            response = delete_service_by_challenge_pk(mock_challenge)

    assert (
        response["ResponseMetadata"]["HTTPStatusCode"]
        == HTTPStatus.BAD_REQUEST
    )
    mock_client.delete_service.assert_not_called()


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_delete_service_failure(mock_cleanup, mock_challenge, mock_client):
    mock_challenge.workers = 0
    response_metadata_error = {
        "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST}
    }

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        mock_client.delete_service.return_value = response_metadata_error

        response = delete_service_by_challenge_pk(mock_challenge)

    assert (
        response["ResponseMetadata"]["HTTPStatusCode"]
        == HTTPStatus.BAD_REQUEST
    )
    mock_challenge.save.assert_not_called()


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_deregister_task_definition_failure(
    mock_cleanup, mock_challenge, mock_client
):
    mock_challenge.workers = 0
    response_metadata_ok = {
        "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
    }

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        mock_client.delete_service.return_value = response_metadata_ok
        mock_client.deregister_task_definition.side_effect = ClientError(
            error_response={
                "Error": {"Code": "DeregisterError"},
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            },
            operation_name="DeregisterTaskDefinition",
        )

        response = delete_service_by_challenge_pk(mock_challenge)

    assert (
        response["ResponseMetadata"]["HTTPStatusCode"]
        == HTTPStatus.BAD_REQUEST
    )
    mock_client.deregister_task_definition.assert_called_once_with(
        taskDefinition=mock_challenge.task_def_arn
    )


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_delete_service_client_error(
    mock_cleanup, mock_challenge, mock_client
):
    mock_challenge.workers = 0

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        mock_client.delete_service.side_effect = ClientError(
            error_response={
                "Error": {"Code": "DeleteServiceError"},
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            },
            operation_name="DeleteService",
        )

        response = delete_service_by_challenge_pk(mock_challenge)

    assert (
        response["ResponseMetadata"]["HTTPStatusCode"]
        == HTTPStatus.BAD_REQUEST
    )
    mock_challenge.save.assert_not_called()
    mock_client.deregister_task_definition.assert_not_called()


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_delete_service_service_not_found_returns_success(
    mock_cleanup, mock_challenge, mock_client
):
    """Test that ServiceNotFoundException is treated as success since the
    deletion goal is achieved (service doesn't exist)."""
    mock_challenge.workers = 0
    mock_challenge.task_def_arn = "valid_task_def_arn"
    mock_challenge.pk = 123

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        mock_client.delete_service.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ServiceNotFoundException"},
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            },
            operation_name="DeleteService",
        )

        response = delete_service_by_challenge_pk(mock_challenge)

    # Should return success since the service doesn't exist
    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    # Challenge state should be cleaned up
    assert mock_challenge.workers is None
    assert mock_challenge.task_def_arn == ""
    mock_challenge.save.assert_called()
    # Should attempt to deregister task definition
    mock_client.deregister_task_definition.assert_called_once_with(
        taskDefinition="valid_task_def_arn"
    )


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_delete_service_service_not_found_with_deregister_failure(
    mock_cleanup, mock_challenge, mock_client
):
    """Test that ServiceNotFoundException still succeeds even if deregister
    task definition also fails."""
    mock_challenge.workers = 0
    mock_challenge.task_def_arn = "valid_task_def_arn"
    mock_challenge.pk = 123

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        mock_client.delete_service.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ServiceNotFoundException"},
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            },
            operation_name="DeleteService",
        )
        mock_client.deregister_task_definition.side_effect = ClientError(
            error_response={
                "Error": {"Code": "TaskDefinitionNotFound"},
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            },
            operation_name="DeregisterTaskDefinition",
        )

        response = delete_service_by_challenge_pk(mock_challenge)

    # Should still return success
    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    # Challenge state should be cleaned up
    assert mock_challenge.workers is None
    assert mock_challenge.task_def_arn == ""
    mock_challenge.save.assert_called()


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_update_service_service_not_found_proceeds_to_delete(
    mock_cleanup, mock_challenge, mock_client
):
    """Test that when update_service fails with ServiceNotFoundException,
    the code proceeds to delete_service anyway."""
    mock_challenge.workers = 3
    mock_challenge.task_def_arn = "valid_task_def_arn"
    mock_challenge.pk = 123

    response_metadata_ok = {
        "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
    }
    response_service_not_found = {
        "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        "Error": {"Code": "ServiceNotFoundException"},
    }

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        with patch(
            "challenges.aws_utils.update_service_by_challenge_pk",
            return_value=response_service_not_found,
        ):
            mock_client.delete_service.return_value = response_metadata_ok

            response = delete_service_by_challenge_pk(mock_challenge)

    # Should return success since delete succeeded
    assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
    # delete_service should have been called despite update failure
    mock_client.delete_service.assert_called_once()
    mock_challenge.save.assert_called()


@patch("challenges.aws_utils.cleanup_auto_scaling_for_service")
def test_update_service_other_error_does_not_proceed_to_delete(
    mock_cleanup, mock_challenge, mock_client
):
    """Test that when update_service fails with a non-ServiceNotFoundException
    error, the code does NOT proceed to delete_service."""
    mock_challenge.workers = 3
    mock_challenge.task_def_arn = "valid_task_def_arn"

    response_other_error = {
        "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        "Error": {"Code": "SomeOtherError"},
    }

    with patch(
        "challenges.aws_utils.get_boto3_client", return_value=mock_client
    ):
        with patch(
            "challenges.aws_utils.update_service_by_challenge_pk",
            return_value=response_other_error,
        ):
            response = delete_service_by_challenge_pk(mock_challenge)

    # Should return the error response
    assert (
        response["ResponseMetadata"]["HTTPStatusCode"]
        == HTTPStatus.BAD_REQUEST
    )
    # delete_service should NOT have been called
    mock_client.delete_service.assert_not_called()


class TestServiceManager:
    @pytest.fixture
    def mock_client(self):
        return MagicMock()

    @pytest.fixture
    def mock_challenge(self):
        return MagicMock()

    def test_service_manager_updates_service(
        self, mock_client, mock_challenge
    ):
        # Setup
        mock_challenge.workers = 1
        num_of_tasks = 5
        force_new_deployment = False
        response_metadata_ok = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        # Mock the update_service_by_challenge_pk to return a mock response
        with patch(
            "challenges.aws_utils.update_service_by_challenge_pk",
            return_value=response_metadata_ok,
        ) as mock_update:
            # Call the function
            response = service_manager(
                mock_client,
                mock_challenge,
                num_of_tasks=num_of_tasks,
                force_new_deployment=force_new_deployment,
            )

            # Verify
            assert response == response_metadata_ok
            mock_update.assert_called_once_with(
                mock_client, mock_challenge, num_of_tasks, force_new_deployment
            )

    def test_service_manager_creates_service(
        self, mock_client, mock_challenge
    ):
        # Setup
        mock_challenge.workers = None
        response_metadata_ok = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        # Mock client_token_generator and create_service_by_challenge_pk to
        # return a mock response
        with patch(
            "challenges.aws_utils.client_token_generator",
            return_value="mock_client_token",
        ):
            with patch(
                "challenges.aws_utils.create_service_by_challenge_pk",
                return_value=response_metadata_ok,
            ) as mock_create:
                # Call the function
                response = service_manager(mock_client, mock_challenge)

                # Verify
                assert response == response_metadata_ok
                mock_create.assert_called_once_with(
                    mock_client, mock_challenge, "mock_client_token"
                )

    def test_service_manager_service_not_found_stop_returns_success(
        self, mock_client, mock_challenge
    ):
        """When update fails with ServiceNotFoundException and num_of_tasks=0
        (stop), treat as success and sync challenge.workers to 0."""
        mock_challenge.workers = 1
        response_service_not_found = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": {"Code": "ServiceNotFoundException"},
        }

        with patch(
            "challenges.aws_utils.update_service_by_challenge_pk",
            return_value=response_service_not_found,
        ):
            response = service_manager(
                mock_client, mock_challenge, num_of_tasks=0
            )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
        assert mock_challenge.workers == 0
        mock_challenge.save.assert_called()

    def test_service_manager_service_not_found_start_creates_service(
        self, mock_client, mock_challenge
    ):
        """When update fails with ServiceNotFoundException and num_of_tasks>0
        (start), create the service instead."""
        mock_challenge.workers = 1
        response_service_not_found = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": {"Code": "ServiceNotFoundException"},
        }
        response_metadata_ok = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        with patch(
            "challenges.aws_utils.update_service_by_challenge_pk",
            return_value=response_service_not_found,
        ):
            with patch(
                "challenges.aws_utils.client_token_generator",
                return_value="mock_client_token",
            ):
                with patch(
                    "challenges.aws_utils.create_service_by_challenge_pk",
                    return_value=response_metadata_ok,
                ) as mock_create:
                    response = service_manager(
                        mock_client, mock_challenge, num_of_tasks=1
                    )

        assert response == response_metadata_ok
        assert mock_challenge.workers is None
        mock_challenge.save.assert_called()
        mock_create.assert_called_once_with(
            mock_client, mock_challenge, "mock_client_token"
        )


class TestStopEc2Instance(unittest.TestCase):
    @patch("challenges.aws_utils.get_boto3_client")
    def test_stop_instance_success(self, mock_get_boto3_client):
        # Mocking the EC2 client
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        # Mocking describe_instance_status response
        mock_ec2.describe_instance_status.return_value = {
            "InstanceStatuses": [
                {
                    "SystemStatus": {"Status": "ok"},
                    "InstanceStatus": {"Status": "ok"},
                    "InstanceState": {"Name": "running"},
                }
            ]
        }
        # Mocking stop_instances response
        mock_ec2.stop_instances.return_value = {
            "StoppingInstances": [
                {
                    "InstanceId": "i-1234567890abcdef0",
                    "CurrentState": {"Name": "stopping"},
                }
            ]
        }

        # Creating a mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1

        # Calling the function
        result = stop_ec2_instance(challenge)

        # Checking the response
        self.assertEqual(
            result["response"],
            {
                "StoppingInstances": [
                    {
                        "InstanceId": "i-1234567890abcdef0",
                        "CurrentState": {"Name": "stopping"},
                    }
                ]
            },
        )
        self.assertEqual(
            result["message"], "Instance for challenge 1 successfully stopped."
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_instance_not_running(self, mock_get_boto3_client):
        # Mocking the EC2 client
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        # Mocking describe_instance_status response
        mock_ec2.describe_instance_status.return_value = {
            "InstanceStatuses": [
                {
                    "SystemStatus": {"Status": "ok"},
                    "InstanceStatus": {"Status": "ok"},
                    "InstanceState": {"Name": "stopped"},
                }
            ]
        }

        # Creating a mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1

        # Calling the function
        result = stop_ec2_instance(challenge)

        # Checking the response
        self.assertEqual(
            result["error"],
            "Instance for challenge 1 is not running. Please ensure the instance is running.",
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_status_checks_not_ready(self, mock_get_boto3_client):
        # Mocking the EC2 client
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        # Mocking describe_instance_status response
        mock_ec2.describe_instance_status.return_value = {
            "InstanceStatuses": [
                {
                    "SystemStatus": {"Status": "impaired"},
                    "InstanceStatus": {"Status": "ok"},
                    "InstanceState": {"Name": "running"},
                }
            ]
        }

        # Creating a mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1

        # Calling the function
        result = stop_ec2_instance(challenge)

        # Checking the response
        self.assertEqual(
            result["error"],
            "Instance status checks are not ready for challenge 1. Please wait for the status checks to pass.",
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_instance_not_found(self, mock_get_boto3_client):
        # Mocking the EC2 client
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2

        # Mocking describe_instance_status response
        mock_ec2.describe_instance_status.return_value = {
            "InstanceStatuses": []
        }

        # Creating a mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1

        # Calling the function
        result = stop_ec2_instance(challenge)

        # Checking the response
        self.assertEqual(
            result["error"],
            "Instance for challenge 1 not found. Please ensure the instance exists.",
        )


class TestDescribeEC2Instance(unittest.TestCase):
    @patch(
        "challenges.aws_utils.get_boto3_client"
    )  # Mock the `get_boto3_client` function
    def test_describe_ec2_instance_success(self, mock_get_boto3_client):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "State": {"Name": "running"},
                        }
                    ]
                }
            ]
        }
        mock_ec2.describe_instances.return_value = mock_response
        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        # Call the function
        result = describe_ec2_instance(challenge)
        # Assert the result
        self.assertEqual(
            result,
            {
                "message": {
                    "InstanceId": "i-1234567890abcdef0",
                    "State": {"Name": "running"},
                }
            },
        )
        mock_ec2.describe_instances.assert_called_once_with(
            InstanceIds=["i-1234567890abcdef0"]
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="ec2_worker_script_content",
    )
    def test_set_ec2_storage(self, mock_open, mock_get_boto3_client):
        # Mock setup
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {"Instances": [{"InstanceId": "i-1234567890abcdef0"}]}
        mock_ec2.run_instances.return_value = mock_response

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = None
        challenge.pk = 1
        challenge.ec2_storage = None
        challenge.worker_instance_type = None
        challenge.worker_image_url = None
        challenge.worker_python_version = "3.9"
        challenge.queue = "test_queue"  # Add this to avoid None issues

        # Call the function with ec2_storage
        result = create_ec2_instance(challenge, ec2_storage=100)

        # Assert the expected output
        expected_message = "Instance for challenge 1 successfully created."
        self.assertEqual(result["response"], mock_response)
        self.assertEqual(result["message"], expected_message)

        # Ensure the challenge was updated and saved
        self.assertEqual(challenge.ec2_storage, 100)
        challenge.save.assert_called_once()

        # Ensure the worker script was read correctly
        mock_open.assert_called_once_with(
            "/code/scripts/deployment/deploy_ec2_worker.sh"
        )
        self.assertEqual(mock_open().read(), "ec2_worker_script_content")

    @patch("challenges.aws_utils.get_boto3_client")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="ec2_worker_script_content",
    )
    def test_set_worker_instance_type(self, mock_open, mock_get_boto3_client):
        # Mock setup
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {"Instances": [{"InstanceId": "i-1234567890abcdef0"}]}
        mock_ec2.run_instances.return_value = mock_response

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = None
        challenge.pk = 1
        challenge.ec2_storage = None
        challenge.worker_instance_type = None
        challenge.worker_image_url = None
        challenge.worker_python_version = "3.9"
        challenge.queue = "test_queue"  # Add this to avoid None issues

        # Call the function with worker_instance_type
        result = create_ec2_instance(
            challenge, worker_instance_type="t3.medium"
        )

        # Assert the expected output
        expected_message = "Instance for challenge 1 successfully created."
        self.assertEqual(result["response"], mock_response)
        self.assertEqual(result["message"], expected_message)

        # Ensure the challenge was updated and saved
        self.assertEqual(challenge.worker_instance_type, "t3.medium")
        challenge.save.assert_called_once()

        # Ensure the worker script was read correctly
        mock_open.assert_called_once_with(
            "/code/scripts/deployment/deploy_ec2_worker.sh"
        )
        self.assertEqual(mock_open().read(), "ec2_worker_script_content")

    @patch("challenges.aws_utils.get_boto3_client")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="ec2_worker_script_content",
    )
    def test_set_worker_image_url(self, mock_open, mock_get_boto3_client):
        # Mock setup
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {"Instances": [{"InstanceId": "i-1234567890abcdef0"}]}
        mock_ec2.run_instances.return_value = mock_response

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = None
        challenge.pk = 1
        challenge.ec2_storage = None
        challenge.worker_instance_type = None
        challenge.worker_image_url = None
        challenge.worker_python_version = "3.9"
        challenge.queue = "test_queue"  # Add this to avoid None issues

        # Call the function with worker_image_url
        result = create_ec2_instance(
            challenge, worker_image_url="ami-12345678"
        )

        # Assert the expected output
        expected_message = "Instance for challenge 1 successfully created."
        self.assertEqual(result["response"], mock_response)
        self.assertEqual(result["message"], expected_message)

        # Ensure the challenge was updated and saved
        self.assertEqual(challenge.worker_image_url, "ami-12345678")
        challenge.save.assert_called_once()

        # Ensure the worker script was read correctly
        mock_open.assert_called_once_with(
            "/code/scripts/deployment/deploy_ec2_worker.sh"
        )
        self.assertEqual(mock_open().read(), "ec2_worker_script_content")

    @patch("challenges.aws_utils.get_boto3_client")
    def test_multiple_instances(self, mock_get_boto3_client):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "State": {"Name": "running"},
                        },
                        {
                            "InstanceId": "i-0987654321fedcba0",
                            "State": {"Name": "stopped"},
                        },
                    ]
                }
            ]
        }
        mock_ec2.describe_instances.return_value = mock_response

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"

        # Call the function
        result = describe_ec2_instance(challenge)

        # Assert the result
        self.assertEqual(
            result,
            {
                "message": {
                    "InstanceId": "i-1234567890abcdef0",
                    "State": {"Name": "running"},
                }
            },
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_describe_ec2_instance_exception(
        self, mock_logger, mock_get_boto3_client
    ):
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2

        exception = Exception("Some error")
        exception.response = {"Error": "SomeError"}
        mock_ec2.describe_instances.side_effect = exception

        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"

        result = describe_ec2_instance(challenge)

        assert result == {"error": {"Error": "SomeError"}}
        mock_logger.exception.assert_called_once_with(exception)


class TestStartEC2Instance(unittest.TestCase):
    @patch(
        "challenges.aws_utils.get_boto3_client"
    )  # Mock the `get_boto3_client` function
    def test_start_ec2_instance_success(self, mock_get_boto3_client):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "State": {"Name": "stopped"},
                        }
                    ]
                }
            ]
        }
        mock_ec2.describe_instances.return_value = mock_response
        mock_start_response = {
            "StartingInstances": [
                {
                    "InstanceId": "i-1234567890abcdef0",
                    "CurrentState": {"Name": "pending"},
                }
            ]
        }
        mock_ec2.start_instances.return_value = mock_start_response
        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1
        # Call the function
        result = start_ec2_instance(challenge)
        # Assert the result
        self.assertEqual(
            result,
            {
                "response": mock_start_response,
                "message": "Instance for challenge 1 successfully started.",
            },
        )
        mock_ec2.describe_instances.assert_called_once_with(
            InstanceIds=["i-1234567890abcdef0"]
        )
        mock_ec2.start_instances.assert_called_once_with(
            InstanceIds=["i-1234567890abcdef0"]
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_start_ec2_instance_already_running(self, mock_get_boto3_client):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2

        mock_response = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "State": {"Name": "running"},
                        }
                    ]
                }
            ]
        }
        mock_ec2.describe_instances.return_value = mock_response

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1
        # Call the function
        result = start_ec2_instance(challenge)

        # Assert the result
        self.assertEqual(
            result,
            {
                "error": "Instance for challenge 1 is running. Please ensure the instance is stopped."
            },
        )
        mock_ec2.describe_instances.assert_called_once_with(
            InstanceIds=["i-1234567890abcdef0"]
        )
        mock_ec2.start_instances.assert_not_called()

    @patch("challenges.aws_utils.get_boto3_client")
    def test_start_ec2_instance_no_instances(self, mock_get_boto3_client):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2

        mock_response = {"Reservations": []}
        mock_ec2.describe_instances.return_value = mock_response

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1

        # Call the function
        result = start_ec2_instance(challenge)

        # Assert the result
        self.assertEqual(
            result,
            {
                "error": "Instance for challenge 1 not found. Please ensure the instance exists."
            },
        )
        mock_ec2.describe_instances.assert_called_once_with(
            InstanceIds=["i-1234567890abcdef0"]
        )
        mock_ec2.start_instances.assert_not_called()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_start_ec2_instance_exception(
        self, mock_logger, mock_get_boto3_client
    ):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_ec2.describe_instances.return_value = {
            "Reservations": [
                {
                    "Instances": [
                        {
                            "InstanceId": "i-1234567890abcdef0",
                            "State": {"Name": "stopped"},
                        }
                    ]
                }
            ]
        }
        mock_ec2.start_instances.side_effect = ClientError(
            {"Error": {"Message": "Test Exception"}}, "StartInstances"
        )

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1

        # Call the function
        result = start_ec2_instance(challenge)

        # Assert the result
        self.assertIn("error", result)
        mock_logger.exception.assert_called_once()


class TestRestartEC2Instance(unittest.TestCase):
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_restart_ec2_instance_success(
        self, mock_logger, mock_get_boto3_client
    ):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {
            "RebootingInstances": [{"InstanceId": "i-1234567890abcdef0"}]
        }
        mock_ec2.reboot_instances.return_value = mock_response

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1

        # Call the function
        result = restart_ec2_instance(challenge)

        # Assert the expected output
        expected_message = "Instance for challenge 1 successfully restarted."
        self.assertEqual(result["response"], mock_response)
        self.assertEqual(result["message"], expected_message)

        # Ensure no exceptions were logged
        mock_logger.exception.assert_not_called()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_restart_ec2_instance_client_error(
        self, mock_logger, mock_get_boto3_client
    ):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2

        # Simulate ClientError
        error_response = {
            "Error": {
                "Code": "InvalidInstanceID.NotFound",
                "Message": "The instance ID does not exist",
            }
        }
        mock_ec2.reboot_instances.side_effect = ClientError(
            error_response, "RebootInstances"
        )

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"

        # Call the function
        result = restart_ec2_instance(challenge)

        # Assert the expected output
        self.assertEqual(result["error"], error_response)

        # Ensure the exception was logged
        mock_logger.exception.assert_called_once_with(
            mock_ec2.reboot_instances.side_effect
        )


class TestTerminateEC2Instance(unittest.TestCase):
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_terminate_ec2_instance_success(
        self, mock_logger, mock_get_boto3_client
    ):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {
            "TerminatingInstances": [{"InstanceId": "i-1234567890abcdef0"}]
        }
        mock_ec2.terminate_instances.return_value = mock_response

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1

        # Call the function
        result = terminate_ec2_instance(challenge)

        # Assert the expected output
        expected_message = "Instance for challenge 1 successfully terminated."
        self.assertEqual(result["response"], mock_response)
        self.assertEqual(result["message"], expected_message)

        # Ensure the EC2 instance ID was cleared and the challenge was saved
        self.assertEqual(challenge.ec2_instance_id, "")
        challenge.save.assert_called_once()

        # Ensure no exceptions were logged
        mock_logger.exception.assert_not_called()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_terminate_ec2_instance_client_error(
        self, mock_logger, mock_get_boto3_client
    ):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2

        # Simulate ClientError
        error_response = {
            "Error": {
                "Code": "InvalidInstanceID.NotFound",
                "Message": "The instance ID does not exist",
            }
        }
        mock_ec2.terminate_instances.side_effect = ClientError(
            error_response, "TerminateInstances"
        )

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"

        # Call the function
        result = terminate_ec2_instance(challenge)

        # Assert the expected output
        self.assertEqual(result["error"], error_response)

        # Ensure the exception was logged
        mock_logger.exception.assert_called_once_with(
            mock_ec2.terminate_instances.side_effect
        )

        # Ensure the EC2 instance ID was not cleared and the challenge was not
        # saved
        self.assertNotEqual(challenge.ec2_instance_id, "")
        challenge.save.assert_not_called()


class TestCreateEC2Instance(unittest.TestCase):
    @patch("challenges.aws_utils.get_boto3_client")
    def test_existing_ec2_instance_id(self, mock_get_boto3_client):
        # Mock challenge object with existing EC2 instance ID
        challenge = MagicMock()
        challenge.ec2_instance_id = "i-1234567890abcdef0"
        challenge.pk = 1

        # Call the function
        result = create_ec2_instance(challenge)

        # Assert the expected output
        expected_error = (
            "Challenge 1 has existing EC2 instance ID. "
            "Please ensure there is no existing associated instance before trying to create one."
        )
        self.assertEqual(result["error"], expected_error)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="ec2_worker_script_content",
    )
    def test_create_ec2_instance_success(
        self, mock_open, mock_get_boto3_client
    ):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {"Instances": [{"InstanceId": "i-1234567890abcdef0"}]}
        mock_ec2.run_instances.return_value = mock_response

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = None
        challenge.pk = 1
        challenge.ec2_storage = 50
        challenge.worker_instance_type = "t2.micro"
        challenge.worker_image_url = "ami-0747bdcabd34c712a"
        challenge.worker_python_version = "3.9"
        challenge.queue = "some_queue"

        # Mock settings
        with patch("challenges.aws_utils.settings", ENVIRONMENT="test"):
            # Call the function
            result = create_ec2_instance(challenge)

        # Assert the expected output
        expected_message = "Instance for challenge 1 successfully created."
        self.assertEqual(result["response"], mock_response)
        self.assertEqual(result["message"], expected_message)

        # Ensure the challenge was updated and saved
        self.assertTrue(challenge.uses_ec2_worker)
        self.assertEqual(challenge.ec2_instance_id, "i-1234567890abcdef0")
        challenge.save.assert_called_once()

        # Ensure the worker script was read correctly
        mock_open.assert_called_once_with(
            "/code/scripts/deployment/deploy_ec2_worker.sh"
        )
        self.assertEqual(mock_open().read(), "ec2_worker_script_content")

    @patch("challenges.aws_utils.get_boto3_client")
    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data="ec2_worker_script_content",
    )
    @patch("challenges.aws_utils.logger")
    def test_create_ec2_instance_client_error(
        self, mock_logger, mock_open, mock_get_boto3_client
    ):
        # Setup mock
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2

        # Simulate ClientError
        error_response = {
            "Error": {
                "Code": "InvalidParameterValue",
                "Message": "The parameter value is invalid",
            }
        }
        client_error = ClientError(error_response, "RunInstances")
        mock_ec2.run_instances.side_effect = client_error

        # Mock challenge object
        challenge = MagicMock()
        challenge.ec2_instance_id = None
        challenge.pk = 1
        challenge.queue = "test_queue"
        challenge.worker_image_url = "worker_image_url"

        # Mock aws_keys and settings
        with patch(
            "challenges.aws_utils.aws_keys",
            {
                "AWS_ACCOUNT_ID": "123456789012",
                "AWS_ACCESS_KEY_ID": "access_key",
                "AWS_SECRET_ACCESS_KEY": "secret_key",
                "AWS_REGION": "us-west-1",
            },
        ):
            with patch("challenges.aws_utils.settings", ENVIRONMENT="test"):
                # Call the function
                result = create_ec2_instance(challenge)

        # Assert the expected output
        self.assertEqual(result["error"], error_response)

        mock_logger.exception.assert_called_once()
        logged_exception = mock_logger.exception.call_args[0][0]
        self.assertIsInstance(logged_exception, ClientError)
        self.assertEqual(str(logged_exception), str(client_error))


class TestUpdateSQSRetentionPeriod(unittest.TestCase):
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_update_sqs_retention_period_success(
        self, mock_logger, mock_get_boto3_client
    ):
        # Setup mock SQS client
        mock_sqs = MagicMock()
        mock_get_boto3_client.return_value = mock_sqs
        mock_sqs.get_queue_url.return_value = {
            "QueueUrl": "https://sqs.us-west-1.amazonaws.com/123456789012/test_queue"
        }
        mock_sqs.set_queue_attributes.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": 200}
        }

        # Mock challenge object
        challenge = MagicMock()
        challenge.queue = "test_queue"
        challenge.sqs_retention_period = 86400  # 1 day in seconds

        # Call the function
        result = update_sqs_retention_period(challenge)

        # Assert the expected output
        expected_response = {"ResponseMetadata": {"HTTPStatusCode": 200}}
        self.assertEqual(result, {"message": expected_response})

        # Ensure methods were called with expected arguments
        mock_sqs.get_queue_url.assert_called_once_with(
            QueueName=challenge.queue
        )
        mock_sqs.set_queue_attributes.assert_called_once_with(
            QueueUrl="https://sqs.us-west-1.amazonaws.com/123456789012/test_queue",
            Attributes={"MessageRetentionPeriod": "86400"},
        )
        mock_logger.exception.assert_not_called()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_update_sqs_retention_period_failure(
        self, mock_logger, mock_get_boto3_client
    ):
        # Setup mock SQS client
        mock_sqs = MagicMock()
        mock_get_boto3_client.return_value = mock_sqs
        mock_sqs.get_queue_url.side_effect = ClientError(
            {
                "Error": {
                    "Code": "QueueDoesNotExist",
                    "Message": "The queue does not exist",
                }
            },
            "GetQueueUrl",
        )

        # Mock challenge object
        challenge = MagicMock()
        challenge.queue = "test_queue"
        challenge.sqs_retention_period = 86400  # 1 day in seconds

        # Call the function
        result = update_sqs_retention_period(challenge)

        # Assert the expected output
        self.assertEqual(
            result,
            {
                "error": "An error occurred (QueueDoesNotExist) when calling the "
                "GetQueueUrl operation: The queue does not exist"
            },
        )

        # Ensure methods were called with expected arguments
        mock_sqs.get_queue_url.assert_called_once_with(
            QueueName=challenge.queue
        )
        mock_sqs.set_queue_attributes.assert_not_called()
        mock_logger.exception.assert_called_once()


class TestStartWorkers(unittest.TestCase):
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_start_workers_debug_mode(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Mock queryset
        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = None
        queryset = [challenge]

        # Call the function
        result = start_workers(queryset)

        # Assert the expected output
        expected_result = {
            "count": 0,
            "failures": [
                {
                    "message": "Workers cannot be started on AWS ECS service in development environment",
                    "challenge_pk": 1,
                }
            ],
        }
        self.assertEqual(result, expected_result)
        mock_get_boto3_client.assert_not_called()
        mock_service_manager.assert_not_called()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_start_workers_success(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Setup mock ECS client
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        # Mock queryset
        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 0
        queryset = [challenge]

        # Call the function
        result = start_workers(queryset)

        # Assert the expected output
        expected_result = {"count": 1, "failures": []}
        self.assertEqual(result, expected_result)

        # Ensure methods were called with expected arguments
        aws_keys = {
            "AWS_ACCOUNT_ID": "x",
            "AWS_ACCESS_KEY_ID": "x",
            "AWS_SECRET_ACCESS_KEY": "x",
            "AWS_REGION": "us-east-1",
            "AWS_STORAGE_BUCKET_NAME": "evalai-s3-bucket",
        }
        mock_get_boto3_client.assert_called_once_with("ecs", aws_keys)
        mock_service_manager.assert_called_once_with(
            mock_client, challenge=challenge, num_of_tasks=1
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_start_workers_clears_evaluation_module_error(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Setup mock ECS client
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        # Mock queryset with a challenge that has an OOM error
        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 0
        challenge.evaluation_module_error = (
            "Worker stopped: OutOfMemoryError. Current memory: 2048 MB."
        )
        queryset = [challenge]

        # Call the function
        result = start_workers(queryset)

        # Assert the error was cleared
        self.assertIsNone(challenge.evaluation_module_error)
        challenge.save.assert_called()
        self.assertEqual(result, {"count": 1, "failures": []})

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_start_workers_no_clear_when_no_error(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Setup mock ECS client
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        # Mock queryset with a challenge that has no error
        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 0
        challenge.evaluation_module_error = None
        queryset = [challenge]

        # Call the function
        result = start_workers(queryset)

        # save() should not be called for clearing error (it's None already)
        challenge.save.assert_not_called()
        self.assertEqual(result, {"count": 1, "failures": []})

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_start_workers_failure(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Setup mock ECS client
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "Some error occurred",
        }

        # Mock queryset
        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 0
        queryset = [challenge]

        # Call the function
        result = start_workers(queryset)

        # Assert the expected output
        expected_result = {
            "count": 0,
            "failures": [
                {"message": "Some error occurred", "challenge_pk": 1}
            ],
        }
        self.assertEqual(result, expected_result)

        # Ensure methods were called with expected arguments
        aws_keys = {
            "AWS_ACCOUNT_ID": "x",
            "AWS_ACCESS_KEY_ID": "x",
            "AWS_SECRET_ACCESS_KEY": "x",
            "AWS_REGION": "us-east-1",
            "AWS_STORAGE_BUCKET_NAME": "evalai-s3-bucket",
        }
        mock_get_boto3_client.assert_called_once_with("ecs", aws_keys)
        mock_service_manager.assert_called_once_with(
            mock_client, challenge=challenge, num_of_tasks=1
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_start_workers_with_active_workers(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Mock queryset with active workers
        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 5
        queryset = [challenge]

        # Call the function
        result = start_workers(queryset)

        # Assert the expected output
        expected_result = {
            "count": 0,
            "failures": [
                {
                    "message": "Please select challenge with inactive workers only.",
                    "challenge_pk": 1,
                }
            ],
        }
        self.assertEqual(result, expected_result)

    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_stop_workers_debug_mode(self, mock_settings):
        # Mock queryset with challenges
        challenge1 = MagicMock()
        challenge1.pk = 1
        challenge2 = MagicMock()
        challenge2.pk = 2
        queryset = [challenge1, challenge2]

        # Call the function
        result = stop_workers(queryset)

        # Assert the expected output
        expected_failures = [
            {
                "message": "Workers cannot be stopped on AWS ECS service in development environment",
                "challenge_pk": 1,
            },
            {
                "message": "Workers cannot be stopped on AWS ECS service in development environment",
                "challenge_pk": 2,
            },
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    def test_stop_workers_success(
        self, mock_service_manager, mock_get_boto3_client, mock_settings
    ):
        # Mock client and service manager response
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
        mock_service_manager.return_value = mock_response

        # Mock queryset with active workers
        challenge1 = MagicMock()
        challenge1.pk = 1
        challenge1.workers = 5
        challenge2 = MagicMock()
        challenge2.pk = 2
        challenge2.workers = 3
        queryset = [challenge1, challenge2]

        # Call the function
        result = stop_workers(queryset)

        # Assert the expected output
        self.assertEqual(result, {"count": 2, "failures": []})

        # Ensure the service manager was called correctly
        mock_service_manager.assert_called_with(
            mock_ec2, challenge=challenge2, num_of_tasks=0
        )
        self.assertEqual(mock_service_manager.call_count, 2)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    def test_stop_workers_failure(
        self, mock_service_manager, mock_get_boto3_client, mock_settings
    ):
        # Mock client and service manager response with error
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "Error stopping worker",
        }
        mock_service_manager.return_value = mock_response

        # Mock queryset with active workers
        challenge1 = MagicMock()
        challenge1.pk = 1
        challenge1.workers = 5
        challenge2 = MagicMock()
        challenge2.pk = 2
        challenge2.workers = 0  # No active workers
        queryset = [challenge1, challenge2]

        # Call the function
        result = stop_workers(queryset)

        # Assert the expected output
        expected_failures = [
            {"message": "Error stopping worker", "challenge_pk": 1},
            {
                "message": "Please select challenges with active workers only.",
                "challenge_pk": 2,
            },
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the service manager was called correctly
        mock_service_manager.assert_called_with(
            mock_ec2, challenge=challenge1, num_of_tasks=0
        )
        self.assertEqual(mock_service_manager.call_count, 1)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    def test_stop_workers_no_active_workers(
        self, mock_service_manager, mock_get_boto3_client, mock_settings
    ):
        # Mock client and service manager response with success
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
        mock_service_manager.return_value = mock_response

        # Mock queryset with no active workers
        challenge1 = MagicMock()
        challenge1.pk = 1
        challenge1.workers = 0
        challenge2 = MagicMock()
        challenge2.pk = 2
        challenge2.workers = 0
        queryset = [challenge1, challenge2]

        # Call the function
        result = stop_workers(queryset)

        # Assert the expected output
        expected_failures = [
            {
                "message": "Please select challenges with active workers only.",
                "challenge_pk": 1,
            },
            {
                "message": "Please select challenges with active workers only.",
                "challenge_pk": 2,
            },
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the service manager was not called
        mock_service_manager.assert_not_called()


class TestScaleWorkers(unittest.TestCase):
    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_scale_workers_debug_mode(self, mock_settings):
        # Mock queryset with challenges
        challenge1 = MagicMock()
        challenge1.pk = 1
        challenge2 = MagicMock()
        challenge2.pk = 2
        queryset = [challenge1, challenge2]

        # Call the function
        result = scale_workers(queryset, num_of_tasks=5)

        # Assert the expected output
        expected_failures = [
            {
                "message": "Workers cannot be scaled on AWS ECS service in development environment",
                "challenge_pk": 1,
            },
            {
                "message": "Workers cannot be scaled on AWS ECS service in development environment",
                "challenge_pk": 2,
            },
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_no_current_workers(
        self, mock_service_manager, mock_get_boto3_client, mock_settings
    ):
        # Mock client and service manager response
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2

        # Mock queryset with no current workers
        challenge1 = MagicMock()
        challenge1.pk = 1
        challenge1.workers = None
        challenge2 = MagicMock()
        challenge2.pk = 2
        challenge2.workers = None
        queryset = [challenge1, challenge2]

        # Call the function
        result = scale_workers(queryset, num_of_tasks=5)

        # Assert the expected output
        expected_failures = [
            {
                "message": "Please start worker(s) before scaling.",
                "challenge_pk": 1,
            },
            {
                "message": "Please start worker(s) before scaling.",
                "challenge_pk": 2,
            },
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the service manager was not called
        mock_service_manager.assert_not_called()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_same_num_of_tasks(
        self, mock_service_manager, mock_get_boto3_client, mock_settings
    ):
        # Mock client and service manager response
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2

        # Mock queryset where num_of_tasks is the same as current workers
        challenge1 = MagicMock()
        challenge1.pk = 1
        challenge1.workers = 5
        challenge2 = MagicMock()
        challenge2.pk = 2
        challenge2.workers = 5
        queryset = [challenge1, challenge2]

        # Call the function
        result = scale_workers(queryset, num_of_tasks=5)

        # Assert the expected output
        expected_failures = [
            {
                "message": "Please scale to a different number. Challenge has 5 worker(s).",
                "challenge_pk": 1,
            },
            {
                "message": "Please scale to a different number. Challenge has 5 worker(s).",
                "challenge_pk": 2,
            },
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the service manager was not called
        mock_service_manager.assert_not_called()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_success(
        self, mock_service_manager, mock_get_boto3_client, mock_settings
    ):
        # Mock client and service manager response
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}}
        mock_service_manager.return_value = mock_response

        # Mock queryset with current workers and valid scaling
        challenge1 = MagicMock()
        challenge1.pk = 1
        challenge1.workers = 5
        challenge1.max_ecs_workers = 7
        challenge1.min_ecs_workers = 0
        challenge2 = MagicMock()
        challenge2.pk = 2
        challenge2.workers = 10
        challenge2.max_ecs_workers = 7
        challenge2.min_ecs_workers = 0
        queryset = [challenge1, challenge2]

        # Call the function
        result = scale_workers(queryset, num_of_tasks=7)

        # Assert the expected output
        self.assertEqual(result, {"count": 2, "failures": []})

        # Ensure the service manager was called correctly
        mock_service_manager.assert_called_with(
            mock_ec2, challenge=challenge2, num_of_tasks=7
        )
        self.assertEqual(mock_service_manager.call_count, 2)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_failure(
        self, mock_service_manager, mock_get_boto3_client, mock_settings
    ):
        # Mock client and service manager response with error
        mock_ec2 = MagicMock()
        mock_get_boto3_client.return_value = mock_ec2
        mock_response = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "Error scaling workers",
        }
        mock_service_manager.return_value = mock_response

        # Mock queryset with current workers and valid scaling
        challenge1 = MagicMock()
        challenge1.pk = 1
        challenge1.workers = 5
        challenge1.max_ecs_workers = 7
        challenge1.min_ecs_workers = 0
        challenge2 = MagicMock()
        challenge2.pk = 2
        challenge2.workers = 10
        challenge2.max_ecs_workers = 7
        challenge2.min_ecs_workers = 0
        queryset = [challenge1, challenge2]

        # Call the function
        result = scale_workers(queryset, num_of_tasks=7)

        # Assert the expected output
        expected_failures = [
            {"message": "Error scaling workers", "challenge_pk": 1},
            {"message": "Error scaling workers", "challenge_pk": 2},
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the service manager was called correctly
        mock_service_manager.assert_called_with(
            mock_ec2, challenge=challenge2, num_of_tasks=7
        )
        self.assertEqual(mock_service_manager.call_count, 2)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.setup_auto_scaling_for_service")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_raises_auto_scaling_ceiling(
        self,
        mock_service_manager,
        mock_setup_auto_scaling,
        mock_get_boto3_client,
        mock_settings,
    ):
        """Scaling up must lift the Application Auto Scaling ceiling too.

        Otherwise the scale-up policy's ExactCapacity clamps the service back
        down and the extra tasks are killed.
        """
        mock_get_boto3_client.return_value = MagicMock()
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_setup_auto_scaling.return_value = True

        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 1
        challenge.max_ecs_workers = 1

        result = scale_workers([challenge], num_of_tasks=2)

        self.assertEqual(result, {"count": 1, "failures": []})
        self.assertEqual(challenge.max_ecs_workers, 2)
        mock_setup_auto_scaling.assert_called_once_with(challenge)
        challenge.save.assert_called()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.setup_auto_scaling_for_service")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_aborts_when_auto_scaling_update_fails(
        self,
        mock_service_manager,
        mock_setup_auto_scaling,
        mock_get_boto3_client,
        mock_settings,
    ):
        """Never raise desiredCount past a ceiling we failed to lift."""
        mock_get_boto3_client.return_value = MagicMock()
        mock_setup_auto_scaling.return_value = False

        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 1
        challenge.max_ecs_workers = 1

        result = scale_workers([challenge], num_of_tasks=2)

        self.assertEqual(result["count"], 0)
        self.assertEqual(result["failures"][0]["challenge_pk"], 1)
        self.assertIn("auto-scaling", result["failures"][0]["message"].lower())
        # The ceiling is rolled back so the DB does not drift from AWS.
        self.assertEqual(challenge.max_ecs_workers, 1)
        mock_service_manager.assert_not_called()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.setup_auto_scaling_for_service")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_rolls_back_ceiling_on_ecs_failure(
        self,
        mock_service_manager,
        mock_setup_auto_scaling,
        mock_get_boto3_client,
        mock_settings,
    ):
        """Autoscaling succeeds but ECS fails: roll back ceiling and re-sync AWS."""
        mock_get_boto3_client.return_value = MagicMock()
        mock_setup_auto_scaling.return_value = True
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "ECS update failed",
        }

        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 1
        challenge.max_ecs_workers = 1
        challenge.min_ecs_workers = 0

        result = scale_workers([challenge], num_of_tasks=2)

        self.assertEqual(result["count"], 0)
        self.assertEqual(challenge.max_ecs_workers, 1)
        # setup called twice: once to raise ceiling, once to roll back
        self.assertEqual(mock_setup_auto_scaling.call_count, 2)
        # DB not persisted since ECS failed
        challenge.save.assert_not_called()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.setup_auto_scaling_for_service")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_logs_warning_when_rollback_fails(
        self,
        mock_service_manager,
        mock_setup_auto_scaling,
        mock_get_boto3_client,
        mock_settings,
    ):
        """If the compensating setup call also fails, a warning is logged."""
        mock_get_boto3_client.return_value = MagicMock()
        # First call (raise ceiling) succeeds, second (rollback) fails
        mock_setup_auto_scaling.side_effect = [True, False]
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "ECS update failed",
        }

        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 1
        challenge.max_ecs_workers = 1
        challenge.min_ecs_workers = 0

        with self.assertLogs("challenges.aws_utils", level="ERROR") as log:
            result = scale_workers([challenge], num_of_tasks=2)

        self.assertEqual(result["count"], 0)
        self.assertEqual(challenge.max_ecs_workers, 1)
        self.assertEqual(mock_setup_auto_scaling.call_count, 2)
        challenge.save.assert_not_called()
        self.assertTrue(any("inconsistent" in m for m in log.output))

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.setup_auto_scaling_for_service")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_to_zero_preserves_ceiling(
        self,
        mock_service_manager,
        mock_setup_auto_scaling,
        mock_get_boto3_client,
        mock_settings,
    ):
        """Scaling to 0 is an idle pause, not a request to lower the ceiling."""
        mock_get_boto3_client.return_value = MagicMock()
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 4
        challenge.max_ecs_workers = 4

        result = scale_workers([challenge], num_of_tasks=0)

        self.assertEqual(result, {"count": 1, "failures": []})
        self.assertEqual(challenge.max_ecs_workers, 4)
        mock_setup_auto_scaling.assert_not_called()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.setup_auto_scaling_for_service")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_lowers_auto_scaling_ceiling(
        self,
        mock_service_manager,
        mock_setup_auto_scaling,
        mock_get_boto3_client,
        mock_settings,
    ):
        """Scaling down must lower the ceiling as well.

        The scale-up policy restores ExactCapacity == the ceiling, so a stale
        higher ceiling would push the service straight back up.
        """
        mock_get_boto3_client.return_value = MagicMock()
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_setup_auto_scaling.return_value = True

        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 4
        challenge.max_ecs_workers = 4

        result = scale_workers([challenge], num_of_tasks=2)

        self.assertEqual(result, {"count": 1, "failures": []})
        self.assertEqual(challenge.max_ecs_workers, 2)
        mock_setup_auto_scaling.assert_called_once_with(challenge)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.setup_auto_scaling_for_service")
    @patch("challenges.aws_utils.service_manager")
    def test_scale_workers_skips_auto_scaling_when_ceiling_unchanged(
        self,
        mock_service_manager,
        mock_setup_auto_scaling,
        mock_get_boto3_client,
        mock_settings,
    ):
        """Restarting an idle service at its existing ceiling needs no AWS churn."""
        mock_get_boto3_client.return_value = MagicMock()
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        challenge = MagicMock()
        challenge.pk = 1
        challenge.workers = 0
        challenge.max_ecs_workers = 2

        result = scale_workers([challenge], num_of_tasks=2)

        self.assertEqual(result, {"count": 1, "failures": []})
        self.assertEqual(challenge.max_ecs_workers, 2)
        mock_setup_auto_scaling.assert_not_called()


class TestScaleResources(unittest.TestCase):
    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    def test_scale_resources_no_changes(
        self, mock_get_boto3_client, mock_settings
    ):
        # Mock client
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        # Mock challenge
        challenge = MagicMock()
        challenge.worker_cpu_cores = 2
        challenge.worker_memory = 4096
        # Call the function with no changes
        result = scale_resources(
            challenge, worker_cpu_cores=2, worker_memory=4096
        )
        # Assert the expected output
        expected_result = {
            "Success": True,
            "Message": "Worker not modified",
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
        }
        self.assertEqual(result, expected_result)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    def test_scale_resources_no_task_def_arn(
        self, mock_get_boto3_client, mock_settings
    ):
        # Mock client
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        # Mock challenge with no task definition ARN
        challenge = MagicMock()
        challenge.task_def_arn = None
        challenge.worker_cpu_cores = 2
        challenge.worker_memory = 4096
        # Call the function
        result = scale_resources(
            challenge, worker_cpu_cores=4, worker_memory=8192
        )
        # Assert the expected output
        expected_result = {
            "Error": "Error. No active task definition registered for the challenge {}.".format(
                challenge.pk
            ),
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }
        self.assertEqual(result, expected_result)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    def test_scale_resources_deregister_success(
        self, mock_get_boto3_client, mock_settings
    ):
        # Mock client and response
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        # Mock challenge
        challenge = MagicMock()
        challenge.task_def_arn = "some_task_def_arn"
        challenge.worker_cpu_cores = 2
        challenge.worker_memory = 4096
        challenge.queue = "test_queue"
        challenge.workers = 1
        # Mock other dependencies
        with patch(
            "challenges.aws_utils.get_image_settings_for_challenge"
        ) as mock_get_image_settings, patch(
            "challenges.aws_utils.build_task_definition_dict"
        ) as mock_build_task_definition:
            mock_get_image_settings.return_value = {}
            mock_build_task_definition.return_value = (
                {"some_key": "some_value"},
                None,
            )

            # Mock register_task_definition response
            mock_client.register_task_definition.return_value = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
                "taskDefinition": {"taskDefinitionArn": "new_task_def_arn"},
            }

            # Mock update_service response
            mock_client.update_service.return_value = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
            }

            # Call the function
            result = scale_resources(
                challenge, worker_cpu_cores=4, worker_memory=8192
            )

            mock_get_image_settings.assert_called_once_with(challenge)
            mock_build_task_definition.assert_called_once()
            call_kwargs = mock_build_task_definition.call_args.kwargs
            self.assertEqual(call_kwargs["worker_cpu_cores"], 4)
            self.assertEqual(call_kwargs["worker_memory"], 8192)

            expected_result = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
            }
            self.assertEqual(result, expected_result)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_scale_resources_deregister_failure(
        self, mock_get_boto3_client, mock_logger, mock_settings
    ):
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {"taskDefinitionArn": "new_task_def_arn"},
        }
        mock_client.update_service.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_client.deregister_task_definition.side_effect = ClientError(
            {"Error": {"Message": "Scaling inactive workers not supported"}},
            "DeregisterTaskDefinition",
        )

        challenge = MagicMock()
        challenge.task_def_arn = "some_task_def_arn"
        challenge.worker_cpu_cores = 2
        challenge.worker_memory = 4096
        challenge.queue = "test_queue"
        challenge.workers = 1

        with patch(
            "challenges.aws_utils.get_image_settings_for_challenge"
        ) as mock_get_image_settings, patch(
            "challenges.aws_utils.build_task_definition_dict"
        ) as mock_build_task_definition:
            mock_get_image_settings.return_value = {}
            mock_build_task_definition.return_value = (
                {"some_key": "some_value"},
                None,
            )

            result = scale_resources(
                challenge, worker_cpu_cores=4, worker_memory=8192
            )

        mock_get_image_settings.assert_called_once_with(challenge)
        mock_build_task_definition.assert_called_once()
        expected_result = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        self.assertEqual(result, expected_result)
        mock_client.deregister_task_definition.assert_called_once_with(
            taskDefinition="some_task_def_arn"
        )
        mock_logger.warning.assert_called_once()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_scale_resources_register_client_error(
        self, mock_get_boto3_client, mock_logger, mock_settings
    ):
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.register_task_definition.side_effect = ClientError(
            {"Error": {"Message": "register failed"}},
            "RegisterTaskDefinition",
        )

        challenge = MagicMock()
        challenge.task_def_arn = "some_task_def_arn"
        challenge.worker_cpu_cores = 2
        challenge.worker_memory = 4096
        challenge.queue = "test_queue"
        challenge.workers = 1

        with patch(
            "challenges.aws_utils.get_image_settings_for_challenge"
        ) as mock_get_image_settings, patch(
            "challenges.aws_utils.build_task_definition_dict"
        ) as mock_build_task_definition:
            mock_get_image_settings.return_value = {}
            mock_build_task_definition.return_value = (
                {"some_key": "some_value"},
                None,
            )

            result = scale_resources(
                challenge, worker_cpu_cores=4, worker_memory=8192
            )

        self.assertEqual(result["Error"]["Message"], "register failed")
        mock_logger.exception.assert_called_once()
        mock_client.update_service.assert_not_called()
        mock_client.deregister_task_definition.assert_not_called()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    def test_scale_resources_register_task_def_success(
        self, mock_get_boto3_client, mock_settings
    ):
        # Mock client and response
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        # Mock challenge
        challenge = MagicMock()
        challenge.task_def_arn = "some_task_def_arn"
        challenge.worker_cpu_cores = 2
        challenge.worker_memory = 4096
        challenge.worker_image_url = "some_image_url"
        challenge.queue = "queue_name"
        challenge.ephemeral_storage = 50
        challenge.pk = 123
        challenge.workers = 10

        # Mock other dependencies
        with patch(
            "challenges.aws_utils.get_image_settings_for_challenge"
        ) as mock_get_image_settings, patch(
            "challenges.aws_utils.build_task_definition_dict"
        ) as mock_build_task_definition:
            mock_get_image_settings.return_value = {}
            mock_build_task_definition.return_value = (
                {"some_key": "some_value"},
                None,
            )

            # Mock register_task_definition response
            mock_client.register_task_definition.return_value = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
                "taskDefinition": {"taskDefinitionArn": "new_task_def_arn"},
            }

            # Mock update_service response
            mock_client.update_service.return_value = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
            }

            # Call the function
            result = scale_resources(
                challenge, worker_cpu_cores=4, worker_memory=8192
            )

            mock_get_image_settings.assert_called_once_with(challenge)
            mock_build_task_definition.assert_called_once()
            call_kwargs = mock_build_task_definition.call_args.kwargs
            self.assertEqual(call_kwargs["worker_cpu_cores"], 4)
            self.assertEqual(call_kwargs["worker_memory"], 8192)

            expected_result = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
            }
            self.assertEqual(result, expected_result)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    def test_scale_resources_register_task_def_failure(
        self, mock_get_boto3_client, mock_settings
    ):
        # Mock client and response
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        # Mock challenge
        challenge = MagicMock()
        challenge.task_def_arn = "some_task_def_arn"
        challenge.worker_cpu_cores = 2
        challenge.worker_memory = 4096
        challenge.worker_image_url = "some_image_url"
        challenge.queue = "queue_name"
        challenge.ephemeral_storage = 50
        challenge.pk = 123
        challenge.workers = 10

        # Mock other dependencies
        with patch(
            "challenges.aws_utils.get_image_settings_for_challenge"
        ) as mock_get_image_settings, patch(
            "challenges.aws_utils.build_task_definition_dict"
        ) as mock_build_task_definition:
            mock_get_image_settings.return_value = {}
            mock_build_task_definition.return_value = (
                {"some_key": "some_value"},
                None,
            )

            # Mock register_task_definition response with error
            mock_client.register_task_definition.return_value = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
                "Error": "Failed to register task definition",
            }

            # Call the function
            result = scale_resources(
                challenge, worker_cpu_cores=4, worker_memory=8192
            )

            mock_get_image_settings.assert_called_once_with(challenge)
            mock_build_task_definition.assert_called_once()
            call_kwargs = mock_build_task_definition.call_args.kwargs
            self.assertEqual(call_kwargs["worker_cpu_cores"], 4)
            self.assertEqual(call_kwargs["worker_memory"], 8192)

            # Expected result
            expected_result = {
                "Error": "Failed to register task definition",
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            }
            self.assertEqual(result, expected_result)


class TestDeleteWorkers(TestCase):
    @patch("challenges.aws_utils.delete_service_by_challenge_pk")
    @patch("challenges.aws_utils.get_log_group_name")
    @patch("challenges.aws_utils.delete_log_group")
    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_delete_workers_in_dev_environment(
        self,
        mock_settings,
        mock_delete_log_group,
        mock_get_log_group_name,
        mock_delete_service_by_challenge_pk,
    ):
        # Mock a queryset
        mock_queryset = [MagicMock(pk=1), MagicMock(pk=2)]

        # Call the function
        result = delete_workers(mock_queryset)

        # Assertions
        expected_failures = [
            {
                "message": "Workers cannot be deleted on AWS ECS service in development environment",
                "challenge_pk": 1,
            },
            {
                "message": "Workers cannot be deleted on AWS ECS service in development environment",
                "challenge_pk": 2,
            },
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the delete_service_by_challenge_pk method was never called
        mock_delete_service_by_challenge_pk.assert_not_called()

    @patch("challenges.aws_utils.delete_service_by_challenge_pk")
    @patch("challenges.aws_utils.get_log_group_name")
    @patch("challenges.aws_utils.delete_log_group")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_delete_workers_no_workers(
        self,
        mock_settings,
        mock_delete_log_group,
        mock_get_log_group_name,
        mock_delete_service_by_challenge_pk,
    ):
        # Mock a queryset with no workers
        challenge_with_no_workers = MagicMock(pk=1, workers=None)
        mock_queryset = [challenge_with_no_workers]

        # Call the function
        result = delete_workers(mock_queryset)

        # Assertions
        expected_failures = [
            {
                "message": "Please select challenges with active workers only.",
                "challenge_pk": 1,
            }
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the delete_service_by_challenge_pk method was never called
        mock_delete_service_by_challenge_pk.assert_not_called()

    @patch("challenges.aws_utils.delete_service_by_challenge_pk")
    @patch("challenges.aws_utils.get_log_group_name")
    @patch("challenges.aws_utils.delete_log_group")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_delete_workers_success(
        self,
        mock_settings,
        mock_delete_log_group,
        mock_get_log_group_name,
        mock_delete_service_by_challenge_pk,
    ):
        # Mock a challenge with workers and successful deletion
        challenge_with_workers = MagicMock(pk=1, workers=5)
        mock_queryset = [challenge_with_workers]

        # Mock the delete_service_by_challenge_pk response
        mock_delete_service_by_challenge_pk.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        # Mock the log group name
        mock_get_log_group_name.return_value = "log_group_name"

        # Call the function
        result = delete_workers(mock_queryset)

        # Assertions
        self.assertEqual(result, {"count": 1, "failures": []})

        # Ensure the delete_service_by_challenge_pk, get_log_group_name, and
        # delete_log_group methods were called
        mock_delete_service_by_challenge_pk.assert_called_once_with(
            challenge=challenge_with_workers
        )
        mock_get_log_group_name.assert_called_once_with(
            challenge_with_workers.pk
        )
        mock_delete_log_group.assert_called_once_with("log_group_name")

    @patch("challenges.aws_utils.delete_service_by_challenge_pk")
    @patch("challenges.aws_utils.get_log_group_name")
    @patch("challenges.aws_utils.delete_log_group")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_delete_workers_failure(
        self,
        mock_settings,
        mock_delete_log_group,
        mock_get_log_group_name,
        mock_delete_service_by_challenge_pk,
    ):
        # Mock a challenge with workers and failed deletion
        challenge_with_workers = MagicMock(pk=1, workers=5)
        mock_queryset = [challenge_with_workers]

        # Mock the delete_service_by_challenge_pk response to simulate a
        # failure
        mock_delete_service_by_challenge_pk.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "An error occurred",
        }

        # Call the function
        result = delete_workers(mock_queryset)

        # Assertions
        expected_failures = [
            {"message": "An error occurred", "challenge_pk": 1}
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the delete_service_by_challenge_pk was called
        mock_delete_service_by_challenge_pk.assert_called_once_with(
            challenge=challenge_with_workers
        )

        # Ensure get_log_group_name and delete_log_group were not called
        mock_get_log_group_name.assert_not_called()
        mock_delete_log_group.assert_not_called()


class TestRestartWorkers(TestCase):
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_restart_workers_in_dev_environment(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Mock a queryset
        mock_queryset = [MagicMock(pk=1), MagicMock(pk=2)]

        # Call the function
        result = restart_workers(mock_queryset)

        # Assertions
        expected_failures = [
            {
                "message": "Workers cannot be restarted on AWS ECS service in development environment",
                "challenge_pk": 1,
            },
            {
                "message": "Workers cannot be restarted on AWS ECS service in development environment",
                "challenge_pk": 2,
            },
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the service_manager method was never called
        mock_service_manager.assert_not_called()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_docker_based_challenge(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        challenge_docker_based = MagicMock(
            pk=1,
            workers=2,
            is_docker_based=True,
            is_static_dataset_code_upload=False,
        )
        mock_queryset = [challenge_docker_based]
        mock_refresh_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        result = restart_workers(mock_queryset)

        self.assertEqual(result, {"count": 1, "failures": []})
        mock_refresh_task_definition.assert_called_once_with(
            challenge_docker_based,
            client=mock_get_boto3_client.return_value,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_no_workers(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Mock a challenge with no workers
        challenge_no_workers = MagicMock(
            pk=1,
            workers=0,
            is_docker_based=False,
            is_static_dataset_code_upload=False,
        )
        mock_queryset = [challenge_no_workers]

        # Call the function
        result = restart_workers(mock_queryset)

        # Assertions
        # Expect a failure message indicating no active workers
        expected_result = {
            "count": 0,
            "failures": [
                {
                    "message": "Please select challenges with active workers only.",
                    "challenge_pk": 1,
                }
            ],
        }
        self.assertEqual(result, expected_result)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_success(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        # Mock a challenge with active workers
        challenge_with_workers = MagicMock(
            pk=1,
            workers=2,
            is_docker_based=False,
            is_static_dataset_code_upload=False,
        )
        mock_queryset = [challenge_with_workers]

        mock_refresh_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        result = restart_workers(mock_queryset)

        self.assertEqual(result, {"count": 1, "failures": []})
        mock_refresh_task_definition.assert_called_once_with(
            challenge_with_workers,
            client=mock_get_boto3_client.return_value,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_clears_evaluation_module_error(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        # Mock a challenge with active workers and an OOM error
        challenge_with_workers = MagicMock(
            pk=1,
            workers=2,
            is_docker_based=False,
            is_static_dataset_code_upload=False,
        )
        challenge_with_workers.evaluation_module_error = (
            "Worker stopped: OutOfMemoryError. Current memory: 2048 MB."
        )
        mock_queryset = [challenge_with_workers]

        mock_refresh_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        result = restart_workers(mock_queryset)

        # Assert the error was cleared
        self.assertIsNone(challenge_with_workers.evaluation_module_error)
        challenge_with_workers.save.assert_called()
        self.assertEqual(result, {"count": 1, "failures": []})

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_failure(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        challenge_with_workers = MagicMock(
            pk=1,
            workers=2,
            is_docker_based=False,
            is_static_dataset_code_upload=False,
        )
        mock_queryset = [challenge_with_workers]

        mock_refresh_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "An error occurred",
        }

        result = restart_workers(mock_queryset)

        expected_failures = [
            {"message": "An error occurred", "challenge_pk": 1}
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})
        mock_refresh_task_definition.assert_called_once_with(
            challenge_with_workers,
            client=mock_get_boto3_client.return_value,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_failure_without_error_message(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        challenge_with_workers = MagicMock(
            pk=8,
            workers=2,
            is_docker_based=False,
            is_static_dataset_code_upload=False,
        )
        mock_refresh_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }

        result = restart_workers([challenge_with_workers])

        self.assertEqual(result["count"], 0)
        self.assertEqual(
            result["failures"][0]["message"], "Failed to restart worker."
        )
        self.assertEqual(result["failures"][0]["challenge_pk"], 8)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_skipped_refresh_response(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        challenge_with_workers = MagicMock(
            pk=7,
            workers=2,
            is_docker_based=False,
            is_static_dataset_code_upload=False,
        )
        mock_refresh_task_definition.return_value = {
            "skipped": True,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
        }

        result = restart_workers([challenge_with_workers])

        self.assertEqual(result["count"], 0)
        self.assertEqual(
            result["failures"],
            [
                {
                    "message": (
                        "Worker task definition refresh is not supported "
                        "for this challenge type."
                    ),
                    "challenge_pk": 7,
                }
            ],
        )
        mock_refresh_task_definition.assert_called_once_with(
            challenge_with_workers,
            client=mock_get_boto3_client.return_value,
        )


class TestRestartWorkersSignalCallback(TestCase):
    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_restart_workers_signal_callback_debug_mode(
        self, mock_settings, *args
    ):
        # Mock the sender and instance
        mock_sender = MagicMock()
        mock_instance = MagicMock()

        # Call the signal callback
        result = restart_workers_signal_callback(
            sender=mock_sender,
            instance=mock_instance,
            field_name="evaluation_script",
        )

        # Assert that the function returns None when DEBUG is True
        self.assertIsNone(result)

    @patch("challenges.aws_utils.settings")
    @patch("challenges.aws_utils.restart_workers")
    def test_restart_workers_signal_callback_restarts_workers(
        self, mock_restart_workers, mock_settings
    ):
        mock_settings.DEBUG = False

        mock_challenge = MagicMock()
        mock_challenge.pk = 1
        mock_challenge.id = 1

        mock_restart_workers.return_value = {"count": 1, "failures": []}

        restart_workers_signal_callback(
            sender=None,
            instance=mock_challenge,
            field_name="evaluation_script",
        )

        mock_restart_workers.assert_called_once()

    @patch("challenges.aws_utils.settings")
    @patch("challenges.aws_utils.restart_workers")
    @patch("challenges.aws_utils._file_content_changed")
    def test_restart_workers_signal_callback_identical_content_skips(
        self,
        mock_content_changed,
        mock_restart_workers,
        mock_settings,
    ):
        mock_settings.DEBUG = False
        mock_content_changed.return_value = False

        mock_challenge = MagicMock()
        mock_challenge.pk = 1
        mock_challenge.id = 1

        restart_workers_signal_callback(
            sender=None,
            instance=mock_challenge,
            field_name="evaluation_script",
        )

        mock_restart_workers.assert_not_called()


class TestFileContentChanged(TestCase):
    def _make_file_field(self, content):
        from io import BytesIO

        f = BytesIO(content)
        return f

    def test_identical_content_returns_false(self):
        old = self._make_file_field(b"same content")
        new = self._make_file_field(b"same content")
        self.assertFalse(_file_content_changed(old, new))

    def test_different_content_returns_true(self):
        old = self._make_file_field(b"old content")
        new = self._make_file_field(b"new content")
        self.assertTrue(_file_content_changed(old, new))

    def test_one_empty_one_present_returns_true(self):
        new = self._make_file_field(b"content")
        self.assertTrue(_file_content_changed(None, new))
        self.assertTrue(_file_content_changed("", new))

    def test_present_to_empty_returns_true(self):
        old = self._make_file_field(b"content")
        self.assertTrue(_file_content_changed(old, None))
        self.assertTrue(_file_content_changed(old, ""))

    def test_both_empty_returns_false(self):
        self.assertFalse(_file_content_changed(None, None))
        self.assertFalse(_file_content_changed("", ""))

    def test_exception_falls_back_to_true(self):
        old = MagicMock()
        old.__bool__ = lambda self: True
        old.seek.side_effect = IOError("storage unavailable")
        new = MagicMock()
        new.__bool__ = lambda self: True
        self.assertTrue(_file_content_changed(old, new))


class TestGetLogsFromCloudwatch(TestCase):
    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_get_logs_from_cloudwatch_debug_mode(self, mock_settings, *args):
        # Test when DEBUG is True
        log_group_name = "dummy_group"
        log_stream_prefix = "dummy_prefix"
        start_time = 123456789
        end_time = 123456999
        pattern = ""
        limit = 10

        logs = get_logs_from_cloudwatch(
            log_group_name,
            log_stream_prefix,
            start_time,
            end_time,
            pattern,
            limit,
        )

        expected_logs = [
            "The worker logs in the development environment are available on the terminal. "
            "Please use docker-compose logs -f worker to view the logs."
        ]

        self.assertEqual(logs, expected_logs)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_get_logs_from_cloudwatch_success(
        self, mock_settings, mock_get_boto3_client
    ):
        # Test when DEBUG is False and logs are retrieved successfully
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        mock_client.filter_log_events.return_value = {
            "events": [
                {"message": "Log message 1"},
                {"message": "Log message 2"},
            ],
            "nextToken": None,
        }

        log_group_name = "dummy_group"
        log_stream_prefix = "dummy_prefix"
        start_time = 123456789
        end_time = 123456999
        pattern = ""
        limit = 10

        logs = get_logs_from_cloudwatch(
            log_group_name,
            log_stream_prefix,
            start_time,
            end_time,
            pattern,
            limit,
        )

        expected_logs = ["Log message 1", "Log message 2"]

        self.assertEqual(logs, expected_logs)
        mock_client.filter_log_events.assert_called_once_with(
            logGroupName=log_group_name,
            logStreamNamePrefix=log_stream_prefix,
            startTime=start_time,
            endTime=end_time,
            filterPattern=pattern,
            limit=limit,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_get_logs_from_cloudwatch_resource_not_found(
        self, mock_settings, mock_get_boto3_client
    ):
        # Test when DEBUG is False and ResourceNotFoundException is raised
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        exception = Exception()
        exception.response = {"Error": {"Code": "ResourceNotFoundException"}}
        mock_client.filter_log_events.side_effect = exception

        log_group_name = "dummy_group"
        log_stream_prefix = "dummy_prefix"
        start_time = 123456789
        end_time = 123456999
        pattern = ""
        limit = 10

        logs = get_logs_from_cloudwatch(
            log_group_name,
            log_stream_prefix,
            start_time,
            end_time,
            pattern,
            limit,
        )

        self.assertEqual(logs, [])

    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_get_logs_from_cloudwatch_other_exception(
        self, mock_settings, mock_get_boto3_client, mock_logger
    ):
        # Test when DEBUG is False and a different exception is raised
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        exception = Exception("Some error")
        exception.response = {"Error": {"Code": "OtherException"}}
        mock_client.filter_log_events.side_effect = exception

        log_group_name = "dummy_group"
        log_stream_prefix = "dummy_prefix"
        start_time = 123456789
        end_time = 123456999
        pattern = ""
        limit = 10

        logs = get_logs_from_cloudwatch(
            log_group_name,
            log_stream_prefix,
            start_time,
            end_time,
            pattern,
            limit,
        )

        expected_logs = [
            "There is an error in displaying logs. Please find the full error traceback here Some error"
        ]

        self.assertEqual(logs, expected_logs)
        mock_logger.exception.assert_called_once_with(exception)

    @patch(
        "challenges.aws_utils.settings"
    )  # Adjust the path to the actual module
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_delete_log_group_debug_mode(
        self, mock_logger, mock_get_boto3_client, mock_settings
    ):
        # When settings.DEBUG is True
        mock_settings.DEBUG = True

        # Call the function
        delete_log_group("test-log-group")

        # Assert that get_boto3_client and logger were not called
        mock_get_boto3_client.assert_not_called()
        mock_logger.assert_not_called()

    @patch(
        "challenges.aws_utils.settings"
    )  # Adjust the path to the actual module
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_delete_log_group_non_debug_mode(
        self, mock_logger, mock_get_boto3_client, mock_settings
    ):
        # When settings.DEBUG is False
        mock_settings.DEBUG = False

        # Mock boto3 client and its methods
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        # Call the function
        delete_log_group("test-log-group")

        aws_keys = {
            "AWS_ACCOUNT_ID": "x",
            "AWS_ACCESS_KEY_ID": "x",
            "AWS_SECRET_ACCESS_KEY": "x",
            "AWS_REGION": "us-east-1",
            "AWS_STORAGE_BUCKET_NAME": "evalai-s3-bucket",
        }
        # Assert that get_boto3_client was called with the correct arguments
        mock_get_boto3_client.assert_called_once_with("logs", aws_keys)

        # Assert that delete_log_group was called on the client with the
        # correct argument
        mock_client.delete_log_group.assert_called_once_with(
            logGroupName="test-log-group"
        )

        # Assert that logger.exception was not called
        mock_logger.exception.assert_not_called()

    @patch(
        "challenges.aws_utils.settings"
    )  # Adjust the path to the actual module
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.logger")
    def test_delete_log_group_with_exception(
        self, mock_logger, mock_get_boto3_client, mock_settings
    ):
        # When settings.DEBUG is False and an exception occurs
        mock_settings.DEBUG = False

        # Mock boto3 client and its methods to raise an exception
        mock_client = MagicMock()
        mock_client.delete_log_group.side_effect = Exception("Delete failed")
        mock_get_boto3_client.return_value = mock_client

        # Call the function
        delete_log_group("test-log-group")

        aws_keys = {
            "AWS_ACCOUNT_ID": "x",
            "AWS_ACCESS_KEY_ID": "x",
            "AWS_SECRET_ACCESS_KEY": "x",
            "AWS_REGION": "us-east-1",
            "AWS_STORAGE_BUCKET_NAME": "evalai-s3-bucket",
        }
        # Assert that get_boto3_client was called with the correct arguments
        mock_get_boto3_client.assert_called_once_with("logs", aws_keys)

        # Assert that delete_log_group was called on the client with the
        # correct argument
        mock_client.delete_log_group.assert_called_once_with(
            logGroupName="test-log-group"
        )

        # Retrieve the actual arguments passed to logger.exception
        args, kwargs = mock_logger.exception.call_args

        # Check if the first argument of logger.exception contains the correct
        # message
        self.assertTrue(
            "Delete failed" in str(args[0]),
            f"Expected 'Delete failed' in {args[0]}",
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_get_logs_from_cloudwatch_with_pagination(
        self, mock_settings, mock_get_boto3_client
    ):
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        mock_client.filter_log_events.side_effect = [
            {
                "events": [
                    {"message": "Log message 1"},
                    {"message": "Log message 2"},
                ],
                "nextToken": "token123",
            },
            {
                "events": [
                    {"message": "Log message 3"},
                    {"message": "Log message 4"},
                ],
                "nextToken": None,
            },
        ]

        log_group_name = "dummy_group"
        log_stream_prefix = "dummy_prefix"
        start_time = 123456789
        end_time = 123456999
        pattern = ""
        limit = 10

        logs = get_logs_from_cloudwatch(
            log_group_name,
            log_stream_prefix,
            start_time,
            end_time,
            pattern,
            limit,
        )

        expected_logs = [
            "Log message 1",
            "Log message 2",
            "Log message 3",
            "Log message 4",
        ]

        self.assertEqual(logs, expected_logs)
        assert mock_client.filter_log_events.call_count == 2

        _, kwargs = mock_client.filter_log_events.call_args
        assert kwargs["nextToken"] is None or kwargs["nextToken"] == "token123"


class TestCreateEKSNodegroup(unittest.TestCase):
    def setUp(self):
        # create_eks_nodegroup re-reads the challenge so a config edit made
        # while cluster setup is still running is not lost. These tests supply
        # the challenge through the serialized snapshot, so make that lookup
        # miss and fall back to it.
        patcher = patch("challenges.models.Challenge")
        mock_model = patcher.start()
        mock_model.DoesNotExist = Challenge.DoesNotExist
        mock_model.objects.get.side_effect = Challenge.DoesNotExist
        self.addCleanup(patcher.stop)

    @patch("challenges.models.ChallengeEvaluationCluster")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.get_code_upload_setup_meta_for_challenge")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.settings")
    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.construct_and_send_eks_cluster_creation_mail")
    @patch("challenges.aws_utils.create_service_by_challenge_pk")
    @patch("challenges.aws_utils.client_token_generator")
    def test_create_eks_nodegroup_success(
        self,
        mock_client_token_generator,
        mock_create_service_by_challenge_pk,
        mock_construct_and_send_eks_cluster_creation_mail,
        mock_logger,
        mock_settings,
        mock_deserialize,
        mock_get_aws_credentials_for_challenge,
        mock_get_code_upload_setup_meta_for_challenge,
        mock_get_boto3_client,
        mock_evaluation_cluster,
    ):
        # Setup mock objects and functions
        mock_settings.ENVIRONMENT = "test-env"
        mock_challenge = MagicMock()
        mock_deserialize.return_value = [MagicMock(object=mock_challenge)]

        mock_challenge.pk = 1
        mock_challenge.title = "Test Challenge"
        mock_challenge.min_worker_instance = 1
        mock_challenge.max_worker_instance = 2
        mock_challenge.desired_worker_instance = 1
        mock_challenge.worker_disk_size = 50
        mock_challenge.worker_instance_type = "t2.medium"
        mock_challenge.worker_ami_type = "AL2_x86_64"

        mock_cluster_meta = {
            "SUBNET_1": "subnet-123",
            "SUBNET_2": "subnet-456",
            "EKS_NODEGROUP_ROLE_ARN": "arn:aws:iam::123456789012:role/eks-nodegroup-role",
        }
        mock_get_code_upload_setup_meta_for_challenge.return_value = (
            mock_cluster_meta
        )
        mock_aws_credentials = {
            "AWS_ACCOUNT_ID": "x",
            "AWS_ACCESS_KEY_ID": "x",
            "AWS_SECRET_ACCESS_KEY": "x",
            "AWS_REGION": "us-east-1",
            "AWS_STORAGE_BUCKET_NAME": "evalai-s3-bucket",
        }
        mock_get_aws_credentials_for_challenge.return_value = (
            mock_aws_credentials
        )

        mock_client = MagicMock()
        mock_get_boto3_client.side_effect = [mock_client, mock_client]

        # Mocking the create_nodegroup method and the waiter
        mock_client.create_nodegroup.return_value = {"nodegroup": "created"}
        mock_waiter = MagicMock()
        mock_client.get_waiter.return_value = mock_waiter

        # Call the function
        create_eks_nodegroup(mock_challenge, "test-cluster")

        # Assertions
        mock_get_boto3_client.assert_called_with("ecs", mock_aws_credentials)

        mock_client.create_nodegroup.assert_called_once_with(
            clusterName="test-cluster",
            nodegroupName="Test-Challenge-1-test-env-nodegroup",
            scalingConfig={"minSize": 1, "maxSize": 2, "desiredSize": 1},
            diskSize=50,
            subnets=["subnet-123", "subnet-456"],
            instanceTypes=["t2.medium"],
            amiType="AL2_x86_64",
            nodeRole="arn:aws:iam::123456789012:role/eks-nodegroup-role",
        )

        # The nodegroup name is recorded so autoscaling can target it directly
        # instead of guessing the first entry from list_nodegroups.
        mock_evaluation_cluster.objects.filter.assert_called_once_with(
            challenge_id=mock_challenge.pk
        )
        mock_evaluation_cluster.objects.filter.return_value.update.assert_called_once_with(
            nodegroup_name="Test-Challenge-1-test-env-nodegroup"
        )

    @patch("challenges.models.ChallengeEvaluationCluster")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.get_code_upload_setup_meta_for_challenge")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.settings")
    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.construct_and_send_eks_cluster_creation_mail")
    @patch("challenges.aws_utils.create_service_by_challenge_pk")
    @patch("challenges.aws_utils.client_token_generator")
    def test_create_eks_nodegroup_continues_when_name_not_recorded(
        self,
        mock_client_token_generator,
        mock_create_service_by_challenge_pk,
        mock_construct_and_send_eks_cluster_creation_mail,
        mock_logger,
        mock_settings,
        mock_deserialize,
        mock_get_aws_credentials_for_challenge,
        mock_get_code_upload_setup_meta_for_challenge,
        mock_get_boto3_client,
        mock_evaluation_cluster,
    ):
        """
        Recording the nodegroup name is a convenience for autoscaling. Failing
        to record it must not abort cluster provisioning, which is the far
        more expensive operation.
        """
        mock_settings.ENVIRONMENT = "test-env"
        mock_challenge = MagicMock()
        mock_challenge.pk = 1
        mock_challenge.title = "Test Challenge"
        mock_deserialize.return_value = [MagicMock(object=mock_challenge)]
        mock_get_code_upload_setup_meta_for_challenge.return_value = {
            "SUBNET_1": "subnet-1",
            "SUBNET_2": "subnet-2",
            "EKS_NODEGROUP_ROLE_ARN": "arn:aws:iam::210987654321:role/ng",
        }
        mock_get_aws_credentials_for_challenge.return_value = {
            "AWS_REGION": "us-east-1"
        }

        mock_client = MagicMock()
        mock_get_boto3_client.side_effect = [mock_client, mock_client]
        mock_client.create_nodegroup.return_value = {"nodegroup": "created"}
        mock_evaluation_cluster.objects.filter.return_value.update.side_effect = DatabaseError(
            "connection lost"
        )

        create_eks_nodegroup(mock_challenge, "test-cluster")

        self.assertTrue(mock_logger.exception.called)
        # Provisioning still completes.
        self.assertTrue(mock_client.get_waiter.called)
        self.assertTrue(mock_create_service_by_challenge_pk.called)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.get_code_upload_setup_meta_for_challenge")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.settings")
    @patch("challenges.aws_utils.logger")
    def test_create_eks_nodegroup_client_error(
        self,
        mock_logger,
        mock_settings,
        mock_deserialize,
        mock_get_aws_credentials_for_challenge,
        mock_get_code_upload_setup_meta_for_challenge,
        mock_get_boto3_client,
    ):
        # Setup mock objects and functions
        mock_settings.ENVIRONMENT = "test-env"
        mock_challenge = MagicMock()
        mock_deserialize.return_value = [MagicMock(object=mock_challenge)]

        mock_challenge.pk = 1
        mock_challenge.title = "Test Challenge"
        mock_challenge.min_worker_instance = 1
        mock_challenge.max_worker_instance = 2
        mock_challenge.desired_worker_instance = 1
        mock_challenge.worker_disk_size = 50
        mock_challenge.worker_instance_type = "t2.medium"
        mock_challenge.worker_ami_type = "AL2_x86_64"

        mock_cluster_meta = {
            "SUBNET_1": "subnet-123",
            "SUBNET_2": "subnet-456",
            "EKS_NODEGROUP_ROLE_ARN": "arn:aws:iam::123456789012:role/eks-nodegroup-role",
        }
        mock_get_code_upload_setup_meta_for_challenge.return_value = (
            mock_cluster_meta
        )
        mock_aws_credentials = {
            "AWS_ACCESS_KEY_ID": "x",
            "AWS_SECRET_ACCESS_KEY": "x",
            "AWS_REGION": "us-east-1",
        }
        mock_get_aws_credentials_for_challenge.return_value = (
            mock_aws_credentials
        )

        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        # Mocking the create_nodegroup method to raise a ClientError
        mock_client.create_nodegroup.side_effect = ClientError(
            {"Error": {"Code": "SomeError", "Message": "Create failed"}},
            "CreateNodegroup",
        )

        # Call the function
        create_eks_nodegroup(mock_challenge, "test-cluster")

        # Assertions
        mock_get_boto3_client.assert_called_once_with(
            "eks", mock_aws_credentials
        )
        mock_client.create_nodegroup.assert_called_once_with(
            clusterName="test-cluster",
            nodegroupName="Test-Challenge-1-test-env-nodegroup",
            scalingConfig={"minSize": 1, "maxSize": 2, "desiredSize": 1},
            diskSize=50,
            subnets=["subnet-123", "subnet-456"],
            instanceTypes=["t2.medium"],
            amiType="AL2_x86_64",
            nodeRole="arn:aws:iam::123456789012:role/eks-nodegroup-role",
        )

        # Retrieve the actual arguments passed to logger.exception
        args, kwargs = mock_logger.exception.call_args

        # Extract the ClientError object from the actual call
        actual_error = args[0]

        # Check if the actual error message contains the expected message
        expected_message = "An error occurred (SomeError) when calling the CreateNodegroup operation: Create failed"
        self.assertIn(
            expected_message,
            str(actual_error),
            f"Expected message '{expected_message}' in {str(actual_error)}",
        )


class TestSetupEksCluster(TestCase):
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.serializers.ChallengeEvaluationClusterSerializer")
    @patch("challenges.aws_utils.logger")
    def test_setup_eks_cluster_success(
        self,
        mock_logger,
        mock_serializer,
        mock_get_cluster,
        mock_deserialize,
        mock_boto3,
        mock_get_aws,
    ):
        """Test case to ensure success path of the setup_eks_cluster function"""

        # Mocks
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_serializer.return_value.is_valid.return_value = True
        mock_serializer.return_value.save.return_value = None
        mock_get_cluster.return_value = MagicMock()

        # Simulate valid deserialization
        mock_obj = MagicMock()
        mock_obj.object = MagicMock()
        mock_deserialize.return_value = [mock_obj]

        # Call the function
        setup_eks_cluster('{"some": "data"}')

        # Assertions for role creation and policy attachment
        self.assertTrue(mock_client.create_role.called)
        self.assertTrue(mock_client.attach_role_policy.called)
        self.assertTrue(mock_client.create_policy.called)
        self.assertTrue(mock_serializer.return_value.save.called)

        # Ensure an exception was logged
        mock_logger.exception.assert_called_once()

    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.logger")
    def test_setup_eks_cluster_create_role_failure(
        self, mock_logger, mock_deserialize, mock_boto3, mock_get_aws
    ):
        """Test case to simulate failure during EKS role creation"""

        # Mocks
        mock_client = MagicMock()
        mock_client.create_role.side_effect = ClientError(
            {"Error": {"Code": "SomeError"}}, "CreateRole"
        )
        mock_boto3.return_value = mock_client

        # Simulate valid deserialization
        mock_obj = MagicMock()
        mock_obj.object = MagicMock()
        mock_deserialize.return_value = [mock_obj]

        # Call the function
        setup_eks_cluster('{"some": "data"}')

        # Assertions for exception handling
        mock_logger.exception.assert_called_once()
        self.assertTrue(mock_client.create_role.called)

    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.logger")
    def test_setup_eks_cluster_attach_role_policy_failure(
        self, mock_logger, mock_deserialize, mock_boto3, mock_get_aws
    ):
        """Test case to simulate failure during policy attachment"""

        # Mocks
        mock_client = MagicMock()
        mock_client.attach_role_policy.side_effect = ClientError(
            {"Error": {"Code": "SomeError"}}, "AttachRolePolicy"
        )
        mock_boto3.return_value = mock_client

        # Simulate valid deserialization
        mock_obj = MagicMock()
        mock_obj.object = MagicMock()
        mock_deserialize.return_value = [mock_obj]

        # Call the function
        setup_eks_cluster('{"some": "data"}')

        # Assertions for exception handling
        mock_logger.exception.assert_called_once()
        self.assertTrue(mock_client.attach_role_policy.called)

    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.logger")
    def test_setup_eks_cluster_create_policy_failure(
        self, mock_logger, mock_deserialize, mock_boto3, mock_get_aws
    ):
        """Test case to simulate failure during custom ECR policy creation"""

        # Mocks
        mock_client = MagicMock()
        mock_client.create_policy.side_effect = ClientError(
            {"Error": {"Code": "SomeError"}}, "CreatePolicy"
        )
        mock_boto3.return_value = mock_client

        # Simulate valid deserialization
        mock_obj = MagicMock()
        mock_obj.object = MagicMock()
        mock_deserialize.return_value = [mock_obj]

        # Call the function
        setup_eks_cluster('{"some": "data"}')

        # Assertions for exception handling
        mock_logger.exception.assert_called_once()
        self.assertTrue(mock_client.create_policy.called)

    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.logger")
    @patch("challenges.serializers.ChallengeEvaluationClusterSerializer")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    def test_setup_eks_cluster_serialization_failure(
        self,
        mock_get_cluster,
        mock_serializer,
        mock_logger,
        mock_deserialize,
        mock_boto3,
        mock_get_aws,
    ):
        """Test case to simulate failure during serialization"""

        # Mocks
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client

        # Simulate valid deserialization
        mock_obj = MagicMock()
        mock_obj.object = MagicMock()
        mock_deserialize.return_value = [mock_obj]

        # Simulate invalid serializer
        mock_serializer.return_value.is_valid.return_value = False
        mock_get_cluster.return_value = MagicMock()

        # Call the function
        setup_eks_cluster('{"some": "data"}')

        # Ensure serializer failure doesn't cause errors
        self.assertTrue(mock_serializer.return_value.is_valid.called)
        mock_logger.exception.assert_called_once()

    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.create_eks_cluster_subnets.delay")
    @patch("challenges.serializers.ChallengeEvaluationClusterSerializer")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    def test_setup_eks_cluster_subnets_creation(
        self,
        mock_get_cluster,
        mock_serializer,
        mock_create_subnets,
        mock_logger,
        mock_deserialize,
        mock_boto3,
        mock_get_aws,
    ):
        """Test case to ensure EKS cluster subnets creation is triggered"""

        # Mocks
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_serializer.return_value.is_valid.return_value = True
        mock_get_cluster.return_value = MagicMock()

        # Simulate valid deserialization
        mock_obj = MagicMock()
        mock_obj.object = MagicMock()
        mock_deserialize.return_value = [mock_obj]

        # Call the function
        setup_eks_cluster('{"some": "data"}')

        # Ensure subnets creation task is triggered
        self.assertTrue(mock_create_subnets.called)

    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.create_eks_cluster_subnets.delay")
    @patch("challenges.serializers.ChallengeEvaluationClusterSerializer")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.aws_utils.setup_eks_autoscale_cross_account_role")
    def test_setup_eks_cluster_survives_autoscale_role_failure(
        self,
        mock_autoscale_role,
        mock_get_cluster,
        mock_serializer,
        mock_create_subnets,
        mock_logger,
        mock_deserialize,
        mock_boto3,
        mock_get_aws,
    ):
        """
        The autoscale role is optional; the cluster is not. Any failure while
        provisioning it must not prevent the evaluation cluster config from
        being persisted or its subnets from being created.
        """
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_serializer.return_value.is_valid.return_value = True
        mock_get_cluster.return_value = MagicMock()
        mock_obj = MagicMock()
        mock_obj.object = MagicMock()
        mock_deserialize.return_value = [mock_obj]
        mock_autoscale_role.side_effect = RuntimeError("unexpected failure")

        setup_eks_cluster('{"some": "data"}')

        self.assertTrue(mock_autoscale_role.called)
        self.assertTrue(mock_serializer.return_value.save.called)
        self.assertTrue(mock_create_subnets.called)


class TestSetupEksAutoscaleCrossAccountRole(TestCase):
    """
    The autoscale Lambda cannot reach a host account's EKS cluster with its
    own execution role, so this role has to exist for every host-credential
    challenge.
    """

    def setUp(self):
        self.challenge = MagicMock()
        self.challenge.pk = 42
        self.challenge.use_host_credentials = True
        self.client = MagicMock()

    @override_settings(
        EKS_AUTOSCALE_LAMBDA_ROLE_ARN="arn:aws:iam::123456789012:role/lambda-role",
        EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME="evalai-autoscale-crossaccount",
        EKS_AUTOSCALE_CROSS_ACCOUNT_POLICY_NAME="evalai-autoscale-nodegroup-access",
    )
    def test_creates_role_and_attaches_policy(self):
        self.client.create_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::210987654321:role/evalai-autoscale-crossaccount"
            }
        }

        role_arn = setup_eks_autoscale_cross_account_role(
            self.client, self.challenge
        )

        self.assertEqual(
            role_arn,
            "arn:aws:iam::210987654321:role/evalai-autoscale-crossaccount",
        )
        create_kwargs = self.client.create_role.call_args.kwargs
        self.assertEqual(
            create_kwargs["RoleName"], "evalai-autoscale-crossaccount"
        )
        trust_policy = json.loads(create_kwargs["AssumeRolePolicyDocument"])
        self.assertEqual(
            trust_policy["Statement"][0]["Principal"]["AWS"],
            "arn:aws:iam::123456789012:role/lambda-role",
        )

        # Pin the permission contract: a role carrying the wrong policy is
        # indistinguishable from a missing one at autoscale time.
        put_kwargs = self.client.put_role_policy.call_args.kwargs
        self.assertEqual(
            put_kwargs["RoleName"], "evalai-autoscale-crossaccount"
        )
        self.assertEqual(
            put_kwargs["PolicyName"], "evalai-autoscale-nodegroup-access"
        )
        policy = json.loads(put_kwargs["PolicyDocument"])
        self.assertEqual(
            sorted(policy["Statement"][0]["Action"]),
            [
                "eks:DescribeCluster",
                "eks:DescribeNodegroup",
                "eks:ListNodegroups",
                "eks:UpdateNodegroupConfig",
            ],
        )
        self.assertEqual(policy["Statement"][0]["Effect"], "Allow")

    @override_settings(
        EKS_AUTOSCALE_LAMBDA_ROLE_ARN="arn:aws:iam::123456789012:role/lambda-role"
    )
    def test_skips_when_not_using_host_credentials(self):
        self.challenge.use_host_credentials = False

        role_arn = setup_eks_autoscale_cross_account_role(
            self.client, self.challenge
        )

        self.assertIsNone(role_arn)
        self.client.create_role.assert_not_called()

    @override_settings(EKS_AUTOSCALE_LAMBDA_ROLE_ARN="")
    def test_skips_when_lambda_role_arn_unset(self):
        role_arn = setup_eks_autoscale_cross_account_role(
            self.client, self.challenge
        )

        self.assertIsNone(role_arn)
        self.client.create_role.assert_not_called()

    @override_settings(
        EKS_AUTOSCALE_LAMBDA_ROLE_ARN="arn:aws:iam::123456789012:role/lambda-role",
        EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME="evalai-autoscale-crossaccount",
        EKS_AUTOSCALE_CROSS_ACCOUNT_POLICY_NAME="evalai-autoscale-nodegroup-access",
    )
    def test_refreshes_trust_policy_when_role_already_exists(self):
        """
        The role is shared across a host account's challenges, so it usually
        already exists. Its trust policy still needs refreshing in case the
        Lambda's role ARN changed.
        """
        self.client.create_role.side_effect = ClientError(
            {"Error": {"Code": "EntityAlreadyExists"}}, "CreateRole"
        )
        self.client.get_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::210987654321:role/evalai-autoscale-crossaccount"
            }
        }

        role_arn = setup_eks_autoscale_cross_account_role(
            self.client, self.challenge
        )

        self.assertEqual(
            role_arn,
            "arn:aws:iam::210987654321:role/evalai-autoscale-crossaccount",
        )
        refresh_kwargs = self.client.update_assume_role_policy.call_args.kwargs
        self.assertEqual(
            refresh_kwargs["RoleName"], "evalai-autoscale-crossaccount"
        )
        refreshed_trust = json.loads(refresh_kwargs["PolicyDocument"])
        self.assertEqual(
            refreshed_trust["Statement"][0]["Principal"]["AWS"],
            "arn:aws:iam::123456789012:role/lambda-role",
        )
        self.assertEqual(
            self.client.put_role_policy.call_args.kwargs["PolicyName"],
            "evalai-autoscale-nodegroup-access",
        )

    @override_settings(
        EKS_AUTOSCALE_LAMBDA_ROLE_ARN="arn:aws:iam::123456789012:role/lambda-role",
        EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME="evalai-autoscale-crossaccount",
    )
    def test_returns_none_on_unexpected_client_error(self):
        self.client.create_role.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "CreateRole"
        )

        role_arn = setup_eks_autoscale_cross_account_role(
            self.client, self.challenge
        )

        self.assertIsNone(role_arn)
        self.client.put_role_policy.assert_not_called()
        # A non-conflict CreateRole error is not the already-exists path, so
        # the trust policy must not be rewritten either.
        self.client.update_assume_role_policy.assert_not_called()

    @override_settings(
        EKS_AUTOSCALE_LAMBDA_ROLE_ARN="arn:aws:iam::123456789012:role/lambda-role",
        EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME="evalai-autoscale-crossaccount",
    )
    def test_returns_none_when_trust_policy_refresh_fails(self):
        self.client.create_role.side_effect = ClientError(
            {"Error": {"Code": "EntityAlreadyExists"}}, "CreateRole"
        )
        self.client.update_assume_role_policy.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "UpdateAssumeRolePolicy"
        )

        role_arn = setup_eks_autoscale_cross_account_role(
            self.client, self.challenge
        )

        self.assertIsNone(role_arn)
        self.client.put_role_policy.assert_not_called()

    @override_settings(
        EKS_AUTOSCALE_LAMBDA_ROLE_ARN="arn:aws:iam::123456789012:role/lambda-role",
        EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME="evalai-autoscale-crossaccount",
    )
    def test_returns_none_when_role_waiter_times_out(self):
        """
        WaiterError is a BotoCoreError, not a ClientError, so IAM eventual
        consistency outlasting the poll budget must not escape this
        best-effort function and abort cluster setup.
        """
        self.client.create_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::210987654321:role/evalai-autoscale-crossaccount"
            }
        }
        self.client.get_waiter.return_value.wait.side_effect = WaiterError(
            name="role_exists",
            reason="Max attempts exceeded",
            last_response={},
        )

        role_arn = setup_eks_autoscale_cross_account_role(
            self.client, self.challenge
        )

        self.assertIsNone(role_arn)
        self.client.put_role_policy.assert_not_called()

    @override_settings(
        EKS_AUTOSCALE_LAMBDA_ROLE_ARN="arn:aws:iam::123456789012:role/lambda-role",
        EKS_AUTOSCALE_CROSS_ACCOUNT_ROLE_NAME="evalai-autoscale-crossaccount",
        EKS_AUTOSCALE_CROSS_ACCOUNT_POLICY_NAME="evalai-autoscale-nodegroup-access",
    )
    def test_returns_none_when_policy_attachment_fails(self):
        self.client.create_role.return_value = {
            "Role": {
                "Arn": "arn:aws:iam::210987654321:role/evalai-autoscale-crossaccount"
            }
        }
        self.client.put_role_policy.side_effect = ClientError(
            {"Error": {"Code": "AccessDenied"}}, "PutRolePolicy"
        )

        role_arn = setup_eks_autoscale_cross_account_role(
            self.client, self.challenge
        )

        # The role exists but cannot scale anything without its policy, so
        # report failure rather than a usable ARN.
        self.assertIsNone(role_arn)


@pytest.mark.django_db
class TestSetupEC2(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            ec2_instance_id=None,
            creator=self.challenge_host_team,
        )
        self.serialized_challenge = serializers.serialize(
            "json", [self.challenge]
        )

    @patch("challenges.aws_utils.start_ec2_instance")
    @patch("challenges.aws_utils.create_ec2_instance")
    @patch("django.core.serializers.deserialize")
    def test_setup_ec2_with_existing_instance(
        self, mock_deserialize, mock_create_ec2, mock_start_ec2
    ):
        # Setup mock behavior
        mock_obj = MagicMock()
        mock_obj.object = self.challenge
        mock_deserialize.return_value = [mock_obj]
        # Update the challenge to have an ec2_instance_id
        self.challenge.ec2_instance_id = "i-1234567890abcdef0"
        self.challenge.save()
        # Call the function
        setup_ec2(self.serialized_challenge)
        # Check if start_ec2_instance was called since the EC2 instance already
        # exists
        mock_start_ec2.assert_called_once_with(self.challenge)
        mock_create_ec2.assert_not_called()

    @patch("challenges.aws_utils.start_ec2_instance")
    @patch("challenges.aws_utils.create_ec2_instance")
    @patch("django.core.serializers.deserialize")
    def test_setup_ec2_without_existing_instance(
        self, mock_deserialize, mock_create_ec2, mock_start_ec2
    ):
        # Setup mock behavior
        mock_obj = MagicMock()
        mock_obj.object = self.challenge
        mock_deserialize.return_value = [mock_obj]
        # Ensure ec2_instance_id is None
        self.challenge.ec2_instance_id = None
        self.challenge.save()
        # Call the function
        setup_ec2(self.serialized_challenge)
        # Check if create_ec2_instance was called since the EC2 instance
        # doesn't exist
        mock_create_ec2.assert_called_once_with(self.challenge)
        mock_start_ec2.assert_not_called()

    @patch("challenges.aws_utils.update_sqs_retention_period")
    @patch("django.core.serializers.deserialize")
    def test_update_sqs_retention_period_task(
        self, mock_deserialize, mock_update_sqs_retention_period
    ):
        challenge_json = '{"model": "app.challenge", "pk": 1, "fields": {}}'
        mock_challenge_obj = MagicMock()

        mock_deserialized_object = MagicMock()
        mock_deserialized_object.object = mock_challenge_obj
        mock_deserialize.return_value = [mock_deserialized_object]

        update_sqs_retention_period_task(challenge_json)

        mock_deserialize.assert_called_once_with("json", challenge_json)
        mock_update_sqs_retention_period.assert_called_once_with(
            mock_challenge_obj
        )


@pytest.fixture
def celery_queue_env(monkeypatch):
    monkeypatch.setenv("CELERY_QUEUE_NAME", "evalai-celery")


@pytest.mark.usefixtures("celery_queue_env")
class TestRegisterTaskDefByChallengePk:
    @patch("challenges.aws_utils.JwtToken.objects.get")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.aws_utils.container_definition_code_upload_worker")
    @patch("challenges.aws_utils.container_definition_submission_worker")
    @patch("challenges.aws_utils.task_definition_static_code_upload_worker")
    @patch("challenges.aws_utils.task_definition_code_upload_worker")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_static_dataset_code_upload_success(
        self,
        mock_get_aws_credentials,
        mock_task_def_code_upload_worker,
        mock_task_def_static_code_upload_worker,
        mock_container_def_submission_worker,
        mock_container_def_code_upload_worker,
        mock_cluster_get,
        mock_jwt_get,
    ):
        mock_client = MagicMock()
        mock_challenge = MagicMock()
        mock_challenge.is_docker_based = True
        mock_challenge.is_static_dataset_code_upload = True
        mock_challenge.worker_image_url = None
        mock_challenge.creator.created_by = "user"
        mock_challenge.pk = 1
        mock_challenge.queue = "queue"
        mock_challenge.worker_cpu_cores = 2
        mock_challenge.worker_memory = 4096
        mock_challenge.ephemeral_storage = 21

        mock_cluster = MagicMock()
        mock_cluster.name = "cluster"
        mock_cluster.cluster_endpoint = "endpoint"
        mock_cluster.cluster_ssl = "ssl"
        mock_cluster.efs_id = "efs"
        mock_cluster_get.return_value = mock_cluster

        mock_token = MagicMock()
        mock_token.refresh_token = "token"
        mock_jwt_get.return_value = mock_token

        mock_container_def_code_upload_worker.format.return_value = (
            "'code_upload_container'"
        )
        mock_container_def_submission_worker.format.return_value = (
            "'submission_container'"
        )
        mock_task_def_static_code_upload_worker.format.return_value = (
            "{'family': 'test'}"
        )

        mock_get_aws_credentials.return_value = {}

        with patch(
            "challenges.aws_utils.load_aws_api_kwargs",
            side_effect=lambda x: {"family": "test"},
        ):
            response = register_task_def_by_challenge_pk(
                mock_client, "queue", mock_challenge
            )

        assert "family" in response or "Error" in response

    @patch("challenges.aws_utils.JwtToken.objects.get")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.aws_utils.task_definition_code_upload_worker")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_non_static_dataset_code_upload_success(
        self,
        mock_get_aws_credentials,
        mock_task_def_code_upload_worker,
        mock_cluster_get,
        mock_jwt_get,
    ):
        mock_client = MagicMock()
        mock_challenge = MagicMock()
        mock_challenge.is_docker_based = True
        mock_challenge.is_static_dataset_code_upload = False
        mock_challenge.worker_image_url = None
        mock_challenge.creator.created_by = "user"
        mock_challenge.pk = 1
        mock_challenge.queue = "queue"
        mock_challenge.worker_cpu_cores = 2
        mock_challenge.worker_memory = 4096
        mock_challenge.ephemeral_storage = 21

        mock_cluster = MagicMock()
        mock_cluster.name = "cluster"
        mock_cluster.cluster_endpoint = "endpoint"
        mock_cluster.cluster_ssl = "ssl"
        mock_cluster.efs_id = "efs"
        mock_cluster_get.return_value = mock_cluster

        mock_token = MagicMock()
        mock_token.refresh_token = "token"
        mock_jwt_get.return_value = mock_token

        mock_task_def_code_upload_worker.format.return_value = (
            "{'family': 'test'}"
        )
        mock_get_aws_credentials.return_value = {}

        with patch(
            "challenges.aws_utils.load_aws_api_kwargs",
            side_effect=lambda x: {"family": "test"},
        ):
            response = register_task_def_by_challenge_pk(
                mock_client, "queue", mock_challenge
            )

        assert "family" in response or "Error" in response

    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_challenge_evaluation_cluster_client_error(
        self, mock_get_aws_credentials, mock_cluster_get
    ):
        mock_client = MagicMock()
        mock_challenge = MagicMock()
        mock_challenge.is_docker_based = True
        mock_challenge.worker_image_url = None
        mock_challenge.task_def_arn = None
        mock_challenge.worker_python_version = "3.9"
        mock_challenge.creator.created_by = "user"
        mock_challenge.pk = 1
        mock_challenge.queue = "queue"
        mock_challenge.worker_cpu_cores = 2
        mock_challenge.worker_memory = 4096
        mock_challenge.ephemeral_storage = 21

        mock_cluster_get.side_effect = ChallengeEvaluationCluster.DoesNotExist
        mock_get_aws_credentials.return_value = {}

        response = register_task_def_by_challenge_pk(
            mock_client, "queue", mock_challenge
        )
        assert response == {
            "Error": "Error. Evaluation cluster not configured for challenge 1.",
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }

    @patch("challenges.aws_utils.JwtToken.objects.get")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.aws_utils.container_definition_code_upload_worker")
    @patch("challenges.aws_utils.container_definition_submission_worker")
    @patch("challenges.aws_utils.task_definition_static_code_upload_worker")
    @patch("challenges.aws_utils.task_definition_code_upload_worker")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_static_dataset_code_upload_with_custom_worker_image(
        self,
        mock_get_aws_credentials,
        mock_task_def_code_upload_worker,
        mock_task_def_static_code_upload_worker,
        mock_container_def_submission_worker,
        mock_container_def_code_upload_worker,
        mock_cluster_get,
        mock_jwt_get,
    ):
        mock_client = MagicMock()
        mock_challenge = MagicMock()
        mock_challenge.is_docker_based = True
        mock_challenge.is_static_dataset_code_upload = True
        mock_challenge.worker_image_url = "custom_image"
        mock_challenge.creator.created_by = "user"
        mock_challenge.pk = 1
        mock_challenge.queue = "queue"
        mock_challenge.worker_cpu_cores = 2
        mock_challenge.worker_memory = 4096
        mock_challenge.ephemeral_storage = 21

        mock_cluster = MagicMock()
        mock_cluster.name = "cluster"
        mock_cluster.cluster_endpoint = "endpoint"
        mock_cluster.cluster_ssl = "ssl"
        mock_cluster.efs_id = "efs"
        mock_cluster_get.return_value = mock_cluster

        mock_token = MagicMock()
        mock_token.refresh_token = "token"
        mock_jwt_get.return_value = mock_token

        mock_container_def_code_upload_worker.format.return_value = (
            "'code_upload_container'"
        )
        mock_container_def_submission_worker.format.return_value = (
            "'submission_container'"
        )
        mock_task_def_static_code_upload_worker.format.return_value = (
            "{'family': 'test'}"
        )

        mock_get_aws_credentials.return_value = {}

        with patch(
            "challenges.aws_utils.load_aws_api_kwargs",
            side_effect=lambda x: {"family": "test"},
        ):
            response = register_task_def_by_challenge_pk(
                mock_client, "queue", mock_challenge
            )

        assert "family" in response or "Error" in response

    @patch("challenges.aws_utils.JwtToken.objects.get")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.aws_utils.container_definition_code_upload_worker")
    @patch("challenges.aws_utils.container_definition_submission_worker")
    @patch("challenges.aws_utils.task_definition_static_code_upload_worker")
    @patch("challenges.aws_utils.task_definition_code_upload_worker")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_register_task_def_success(
        self,
        mock_get_aws_credentials,
        mock_task_def_code_upload_worker,
        mock_task_def_static_code_upload_worker,
        mock_container_def_submission_worker,
        mock_container_def_code_upload_worker,
        mock_cluster_get,
        mock_jwt_get,
    ):
        mock_client = MagicMock()
        mock_challenge = MagicMock()
        mock_challenge.worker_image_url = None
        mock_challenge.worker_python_version = "3.9"
        mock_challenge.is_docker_based = True
        mock_challenge.is_static_dataset_code_upload = False
        mock_challenge.task_def_arn = None
        mock_challenge.creator.created_by = "user"
        mock_challenge.pk = 1
        mock_challenge.queue = "queue"
        mock_challenge.worker_cpu_cores = 2
        mock_challenge.worker_memory = 4096
        mock_challenge.ephemeral_storage = 21

        mock_cluster = MagicMock()
        mock_cluster.name = "cluster"
        mock_cluster.cluster_endpoint = "endpoint"
        mock_cluster.cluster_ssl = "ssl"
        mock_cluster.efs_id = "efs"
        mock_cluster_get.return_value = mock_cluster

        mock_token = MagicMock()
        mock_token.refresh_token = "token"
        mock_jwt_get.return_value = mock_token

        mock_task_def_code_upload_worker.format.return_value = (
            "{'family': 'test'}"
        )
        mock_get_aws_credentials.return_value = {}

        with patch(
            "challenges.aws_utils.load_aws_api_kwargs",
            side_effect=lambda x: {"family": "test"},
        ):
            mock_client.register_task_definition.return_value = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
                "taskDefinition": {
                    "taskDefinitionArn": "arn:aws:ecs:task-def"
                },
            }

            response = register_task_def_by_challenge_pk(
                mock_client, "queue", mock_challenge
            )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
        assert mock_challenge.task_def_arn == "arn:aws:ecs:task-def"
        mock_challenge.save.assert_called_once()

    @patch("challenges.aws_utils.JwtToken.objects.get")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.aws_utils.container_definition_code_upload_worker")
    @patch("challenges.aws_utils.container_definition_submission_worker")
    @patch("challenges.aws_utils.task_definition_static_code_upload_worker")
    @patch("challenges.aws_utils.task_definition_code_upload_worker")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_register_task_def_failure(
        self,
        mock_get_aws_credentials,
        mock_task_def_code_upload_worker,
        mock_task_def_static_code_upload_worker,
        mock_container_def_submission_worker,
        mock_container_def_code_upload_worker,
        mock_cluster_get,
        mock_jwt_get,
    ):
        mock_client = MagicMock()
        mock_challenge = MagicMock()
        mock_challenge.worker_image_url = None
        mock_challenge.is_docker_based = True
        mock_challenge.is_static_dataset_code_upload = False
        mock_challenge.task_def_arn = None
        mock_challenge.creator.created_by = "user"
        mock_challenge.pk = 1
        mock_challenge.queue = "queue"
        mock_challenge.worker_cpu_cores = 2
        mock_challenge.worker_memory = 4096
        mock_challenge.ephemeral_storage = 21

        mock_cluster = MagicMock()
        mock_cluster.name = "cluster"
        mock_cluster.cluster_endpoint = "endpoint"
        mock_cluster.cluster_ssl = "ssl"
        mock_cluster.efs_id = "efs"
        mock_cluster_get.return_value = mock_cluster

        mock_token = MagicMock()
        mock_token.refresh_token = "token"
        mock_jwt_get.return_value = mock_token

        mock_task_def_code_upload_worker.format.return_value = (
            "{'family': 'test'}"
        )
        mock_get_aws_credentials.return_value = {}

        with patch(
            "challenges.aws_utils.load_aws_api_kwargs",
            side_effect=lambda x: {"family": "test"},
        ):
            error_response = {"Error": {"Code": "SomeError"}}
            mock_client.register_task_definition.side_effect = ClientError(
                error_response, "RegisterTaskDefinition"
            )

            response = register_task_def_by_challenge_pk(
                mock_client, "queue", mock_challenge
            )

        assert response == error_response

    @patch("challenges.aws_utils.ensure_challenge_worker_python_version")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch(
        "challenges.aws_utils.COMMON_SETTINGS_DICT",
        {
            "EXECUTION_ROLE_ARN": "arn:aws:iam::123456789012:role/ecsTaskExecutionRole"
        },
    )
    def test_register_task_def_register_non_ok_response(
        self, mock_build_task_definition, mock_ensure
    ):
        mock_client = MagicMock()
        mock_challenge = MagicMock()
        mock_challenge.task_def_arn = None
        mock_challenge.pk = 1
        mock_build_task_definition.return_value = ({"family": "test"}, None)
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "register rejected",
        }

        response = register_task_def_by_challenge_pk(
            mock_client, "queue", mock_challenge
        )

        assert response["Error"] == "register rejected"
        mock_ensure.assert_called_once_with(mock_challenge)
        mock_challenge.save.assert_not_called()

    @patch(
        "challenges.aws_utils.COMMON_SETTINGS_DICT",
        {"EXECUTION_ROLE_ARN": None},
    )
    def test_register_task_def_no_execution_role(self):
        mock_client = MagicMock()
        mock_challenge = MagicMock()
        mock_challenge.worker_image_url = None
        mock_challenge.is_docker_based = False
        mock_challenge.task_def_arn = None
        mock_challenge.pk = 1
        mock_challenge.queue = "queue"
        mock_challenge.worker_cpu_cores = 2
        mock_challenge.worker_memory = 4096
        mock_challenge.ephemeral_storage = 21

        response = register_task_def_by_challenge_pk(
            mock_client, "queue", mock_challenge
        )

        assert (
            response["ResponseMetadata"]["HTTPStatusCode"]
            == HTTPStatus.BAD_REQUEST
        )
        assert "TASK_EXECUTION_ROLE_ARN" in response["Error"]


class TestCreateEksClusterSubnets:
    @patch("challenges.aws_utils.create_eks_cluster.delay")
    @patch("challenges.aws_utils.uuid.uuid4")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.serializers.ChallengeEvaluationClusterSerializer")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.settings")
    def test_create_eks_cluster_subnets_success(
        self,
        mock_settings,
        mock_deserialize,
        mock_get_aws_credentials,
        mock_get_boto3_client,
        mock_serializer,
        mock_get_cluster,
        mock_uuid4,
        mock_create_eks_cluster_delay,
    ):
        mock_settings.ENVIRONMENT = "test"
        mock_challenge_obj = MagicMock()
        mock_challenge_obj.pk = 1
        mock_challenge_obj.subnet_1_cidr = "10.0.1.0/24"
        mock_challenge_obj.subnet_2_cidr = "10.0.2.0/24"
        mock_challenge_obj.vpc_cidr = "10.0.0.0/16"
        mock_deserialize.return_value = [MagicMock(object=mock_challenge_obj)]
        mock_get_aws_credentials.return_value = {"AWS_REGION": "us-east-1"}
        mock_client = MagicMock()
        mock_get_boto3_client.side_effect = [
            mock_client,
            MagicMock(),
        ]  # ec2, efs

        mock_client.create_vpc.return_value = {"Vpc": {"VpcId": "vpc-123"}}
        mock_client.create_internet_gateway.return_value = {
            "InternetGateway": {"InternetGatewayId": "igw-123"}
        }
        mock_client.create_route_table.return_value = {
            "RouteTable": {"RouteTableId": "rtb-123"}
        }
        mock_client.create_subnet.side_effect = [
            {"Subnet": {"SubnetId": "subnet-1"}},
            {"Subnet": {"SubnetId": "subnet-2"}},
        ]
        mock_client.create_security_group.side_effect = [
            {"GroupId": "sg-1"},
            {"GroupId": "sg-2"},
        ]
        mock_uuid4.return_value = "uuid-1234"
        efs_client_mock = MagicMock()
        mock_get_boto3_client.side_effect = [
            mock_client,
            efs_client_mock,
        ]  # ec2, efs
        efs_client_mock.create_file_system.return_value = {
            "FileSystemId": "efs-123"
        }
        mock_get_cluster.return_value = MagicMock()
        mock_serializer.return_value.is_valid.return_value = True

        create_eks_cluster_subnets('{"some": "data"}')

        assert mock_client.create_vpc.called
        assert mock_client.create_internet_gateway.called
        assert mock_client.create_route_table.called
        assert mock_client.create_subnet.call_count == 2
        assert mock_client.create_security_group.call_count == 2
        assert efs_client_mock.create_file_system.called
        assert mock_serializer.return_value.save.called
        assert mock_create_eks_cluster_delay.called

    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.settings")
    def test_create_eks_cluster_subnets_vpc_client_error(
        self,
        mock_settings,
        mock_deserialize,
        mock_get_aws_credentials,
        mock_get_boto3_client,
        mock_logger,
    ):
        mock_settings.ENVIRONMENT = "test"
        mock_challenge_obj = MagicMock()
        mock_challenge_obj.pk = 1
        mock_deserialize.return_value = [MagicMock(object=mock_challenge_obj)]
        mock_get_aws_credentials.return_value = {"AWS_REGION": "us-east-1"}
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        mock_client.create_vpc.side_effect = ClientError(
            {"Error": {"Code": "SomeError"}}, "CreateVpc"
        )

        create_eks_cluster_subnets('{"some": "data"}')

        assert mock_logger.exception.called

    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.settings")
    def test_create_eks_cluster_subnets_other_client_error(
        self,
        mock_settings,
        mock_deserialize,
        mock_get_aws_credentials,
        mock_get_boto3_client,
        mock_logger,
    ):
        mock_settings.ENVIRONMENT = "test"
        mock_challenge_obj = MagicMock()
        mock_challenge_obj.pk = 1
        mock_challenge_obj.subnet_1_cidr = "10.0.1.0/24"
        mock_challenge_obj.subnet_2_cidr = "10.0.2.0/24"
        mock_challenge_obj.vpc_cidr = "10.0.0.0/16"
        mock_deserialize.return_value = [MagicMock(object=mock_challenge_obj)]
        mock_get_aws_credentials.return_value = {"AWS_REGION": "us-east-1"}
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client

        mock_client.create_vpc.return_value = {"Vpc": {"VpcId": "vpc-123"}}
        mock_client.modify_vpc_attribute.return_value = None
        mock_client.create_internet_gateway.return_value = {
            "InternetGateway": {"InternetGatewayId": "igw-123"}
        }
        mock_client.attach_internet_gateway.return_value = None
        mock_client.get_waiter.return_value = MagicMock(wait=MagicMock())
        mock_client.create_route_table.return_value = {
            "RouteTable": {"RouteTableId": "rtb-123"}
        }
        mock_client.create_subnet.side_effect = [
            {"Subnet": {"SubnetId": "subnet-1"}},
            {"Subnet": {"SubnetId": "subnet-2"}},
        ]
        mock_client.create_security_group.side_effect = [
            {"GroupId": "sg-1"},
            {"GroupId": "sg-2"},
        ]

        mock_client.authorize_security_group_ingress.side_effect = ClientError(
            {"Error": {"Code": "SomeError"}}, "AuthorizeSecurityGroupIngress"
        )

        create_eks_cluster_subnets('{"some": "data"}')

        assert mock_logger.exception.called


class TestCreateEksCluster:
    @patch("challenges.aws_utils.create_eks_nodegroup.delay")
    @patch("challenges.aws_utils.NamedTemporaryFile")
    @patch("challenges.aws_utils.yaml.dump")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.serializers.ChallengeEvaluationClusterSerializer")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.get_code_upload_setup_meta_for_challenge")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.settings")
    def test_create_eks_cluster_success(
        self,
        mock_settings,
        mock_deserialize,
        mock_get_aws_credentials,
        mock_get_code_upload_setup_meta,
        mock_get_boto3_client,
        mock_serializer,
        mock_get_cluster,
        mock_yaml_dump,
        mock_tempfile,
        mock_create_eks_nodegroup_delay,
    ):
        mock_settings.ENVIRONMENT = "test"
        mock_challenge_obj = MagicMock()
        mock_challenge_obj.pk = 1
        mock_challenge_obj.title = "Test Challenge"
        mock_challenge_obj.approved_by_admin = True
        mock_challenge_obj.is_docker_based = True
        mock_deserialize.return_value = [MagicMock(object=mock_challenge_obj)]
        mock_get_aws_credentials.return_value = {"AWS_REGION": "us-east-1"}
        mock_cluster_meta = {
            "EKS_CLUSTER_ROLE_ARN": "arn:role",
            "SUBNET_1": "subnet-1",
            "SUBNET_2": "subnet-2",
            "SUBNET_SECURITY_GROUP": "sg-1",
        }
        mock_get_code_upload_setup_meta.return_value = mock_cluster_meta
        mock_client = MagicMock()
        mock_get_boto3_client.side_effect = [mock_client, MagicMock()]
        mock_client.create_cluster.return_value = {"cluster": "created"}
        mock_client.get_waiter.return_value = MagicMock(wait=MagicMock())
        mock_client.describe_cluster.return_value = {
            "cluster": {
                "certificateAuthority": {"data": "cert"},
                "endpoint": "endpoint",
            }
        }
        mock_get_cluster.return_value = MagicMock(
            efs_id="efs-1",
            subnet_1_id="subnet-1",
            subnet_2_id="subnet-2",
            efs_security_group_id="sg-efs",
        )
        mock_serializer.return_value.is_valid.return_value = True
        mock_yaml_dump.return_value = "yaml_config"
        mock_tempfile.return_value.write = MagicMock()

        create_eks_cluster('{"some": "data"}')

        assert mock_client.create_cluster.called
        assert mock_client.get_waiter.called
        assert mock_client.describe_cluster.called
        assert mock_serializer.return_value.save.called
        assert mock_create_eks_nodegroup_delay.called

    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.get_code_upload_setup_meta_for_challenge")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.settings")
    def test_create_eks_cluster_client_error(
        self,
        mock_settings,
        mock_deserialize,
        mock_get_aws_credentials,
        mock_get_code_upload_setup_meta,
        mock_get_boto3_client,
        mock_logger,
    ):
        mock_settings.ENVIRONMENT = "test"
        mock_challenge_obj = MagicMock()
        mock_challenge_obj.pk = 1
        mock_challenge_obj.title = "Test Challenge"
        mock_challenge_obj.approved_by_admin = True
        mock_challenge_obj.is_docker_based = True
        mock_deserialize.return_value = [MagicMock(object=mock_challenge_obj)]
        mock_get_aws_credentials.return_value = {"AWS_REGION": "us-east-1"}
        mock_cluster_meta = {
            "EKS_CLUSTER_ROLE_ARN": "arn:role",
            "SUBNET_1": "subnet-1",
            "SUBNET_2": "subnet-2",
            "SUBNET_SECURITY_GROUP": "sg-1",
        }
        mock_get_code_upload_setup_meta.return_value = mock_cluster_meta
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.create_cluster.side_effect = ClientError(
            {"Error": {"Code": "SomeError"}}, "CreateCluster"
        )

        create_eks_cluster('{"some": "data"}')

        assert mock_logger.exception.called

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.get_code_upload_setup_meta_for_challenge")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.aws_utils.settings")
    def test_create_eks_cluster_not_approved_or_not_docker(
        self,
        mock_settings,
        mock_deserialize,
        mock_get_aws_credentials,
        mock_get_code_upload_setup_meta,
        mock_get_boto3_client,
    ):
        mock_settings.ENVIRONMENT = "test"
        mock_challenge_obj = MagicMock()
        mock_challenge_obj.pk = 1
        mock_challenge_obj.title = "Test Challenge"
        mock_challenge_obj.approved_by_admin = False
        mock_challenge_obj.is_docker_based = False
        mock_deserialize.return_value = [MagicMock(object=mock_challenge_obj)]

        create_eks_cluster('{"some": "data"}')

        assert not mock_get_boto3_client.called


class TestChallengeApprovalCallback(TestCase):
    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.delete_workers")
    def test_disapprove_challenge_with_workers_and_delete_failure(
        self, mock_delete_workers, mock_logger
    ):
        challenge = MagicMock()
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.workers = 2
        challenge.id = 42
        challenge._original_approved_by_admin = True
        challenge.approved_by_admin = False

        mock_delete_workers.return_value = {
            "count": 0,
            "failures": [{"message": "Delete failed"}],
        }

        challenge_approval_callback(
            sender=None, instance=challenge, field_name="approved_by_admin"
        )

        mock_logger.error.assert_called_once()
        args, kwargs = mock_logger.error.call_args
        assert "couldn't be deleted! Error: Delete failed" in args[0]

    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.delete_workers")
    def test_disapprove_challenge_with_workers_and_delete_success(
        self, mock_delete_workers, mock_logger
    ):
        challenge = MagicMock()
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.workers = 2
        challenge.id = 42
        challenge._original_approved_by_admin = True
        challenge.approved_by_admin = False

        mock_delete_workers.return_value = {
            "count": 1,
            "failures": [],
        }

        challenge_approval_callback(
            sender=None, instance=challenge, field_name="approved_by_admin"
        )

        mock_logger.error.assert_not_called()


class TestSetupAutoScalingForService(unittest.TestCase):
    @patch("challenges.aws_utils.get_boto3_client")
    def test_setup_auto_scaling_success(self, mock_get_boto3_client):
        mock_autoscaling = MagicMock()
        mock_cloudwatch = MagicMock()

        def side_effect(resource, keys):
            if resource == "application-autoscaling":
                return mock_autoscaling
            elif resource == "cloudwatch":
                return mock_cloudwatch
            return MagicMock()

        mock_get_boto3_client.side_effect = side_effect

        mock_autoscaling.put_scaling_policy.side_effect = [
            {"PolicyARN": "arn:aws:autoscaling:scale-up-policy"},
            {"PolicyARN": "arn:aws:autoscaling:scale-down-policy"},
        ]

        challenge = MagicMock()
        challenge.pk = 1
        challenge.queue = "test_queue"
        challenge.max_ecs_workers = 1
        challenge.min_ecs_workers = 0

        setup_auto_scaling_for_service(challenge)

        mock_autoscaling.register_scalable_target.assert_called_once()
        assert mock_autoscaling.put_scaling_policy.call_count == 2
        assert mock_cloudwatch.put_metric_alarm.call_count == 2

        # Verify scale-up alarm uses the correct queue name
        scale_up_call = mock_cloudwatch.put_metric_alarm.call_args_list[0]
        assert scale_up_call[1]["AlarmName"] == "test_queue_service_scale_up"
        assert scale_up_call[1]["Dimensions"] == [
            {"Name": "QueueName", "Value": "test_queue"}
        ]

        # Verify scale-down alarm evaluates visible + in-flight queue depth
        # via metric math, and scales down (rather than getting stuck) when
        # SQS stops publishing data for a genuinely idle queue.
        scale_down_call = mock_cloudwatch.put_metric_alarm.call_args_list[1]
        assert (
            scale_down_call[1]["AlarmName"] == "test_queue_service_scale_down"
        )
        assert scale_down_call[1]["ComparisonOperator"] == (
            "LessThanOrEqualToThreshold"
        )
        assert scale_down_call[1]["Threshold"] == 0
        assert scale_down_call[1]["TreatMissingData"] == "breaching"
        assert scale_down_call[1]["EvaluationPeriods"] == 1
        metric_ids = {metric["Id"] for metric in scale_down_call[1]["Metrics"]}
        assert metric_ids == {"visible", "in_flight", "total_depth"}
        metrics_by_id = {
            metric["Id"]: metric for metric in scale_down_call[1]["Metrics"]
        }
        expected_metric_names = {
            "visible": "ApproximateNumberOfMessagesVisible",
            "in_flight": "ApproximateNumberOfMessagesNotVisible",
        }
        for metric_id, metric_name in expected_metric_names.items():
            metric_stat = metrics_by_id[metric_id]["MetricStat"]
            assert metrics_by_id[metric_id]["ReturnData"] is False
            assert metric_stat["Period"] == 120
            assert metric_stat["Stat"] == "Sum"
            assert metric_stat["Metric"]["Namespace"] == "AWS/SQS"
            assert metric_stat["Metric"]["MetricName"] == metric_name
            assert metric_stat["Metric"]["Dimensions"] == [
                {"Name": "QueueName", "Value": "test_queue"}
            ]
        total_depth_metric = metrics_by_id["total_depth"]
        assert total_depth_metric["Expression"] == "visible + in_flight"
        assert total_depth_metric["ReturnData"] is True

    @patch("challenges.aws_utils.get_boto3_client")
    def test_setup_auto_scaling_client_error(self, mock_get_boto3_client):
        mock_autoscaling = MagicMock()
        mock_autoscaling.register_scalable_target.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ValidationException"},
                "ResponseMetadata": {"HTTPStatusCode": 400},
            },
            operation_name="RegisterScalableTarget",
        )
        mock_get_boto3_client.return_value = mock_autoscaling

        challenge = MagicMock()
        challenge.pk = 1
        challenge.queue = "test_queue"
        challenge.max_ecs_workers = 1
        challenge.min_ecs_workers = 0

        # Should not raise, just log
        self.assertFalse(setup_auto_scaling_for_service(challenge))

    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_setup_auto_scaling_skipped_in_debug(self, mock_settings):
        challenge = MagicMock()
        challenge.pk = 42

        self.assertTrue(setup_auto_scaling_for_service(challenge))

        # No boto3 calls should be made in DEBUG mode

    def _run_setup(
        self, mock_get_boto3_client, max_ecs_workers, min_ecs_workers=1
    ):
        """Run setup_auto_scaling_for_service and return the autoscaling mock."""
        mock_autoscaling = MagicMock()
        mock_cloudwatch = MagicMock()

        def side_effect(resource, keys):
            if resource == "application-autoscaling":
                return mock_autoscaling
            elif resource == "cloudwatch":
                return mock_cloudwatch
            return MagicMock()

        mock_get_boto3_client.side_effect = side_effect
        mock_autoscaling.put_scaling_policy.side_effect = [
            {"PolicyARN": "arn:aws:autoscaling:scale-up-policy"},
            {"PolicyARN": "arn:aws:autoscaling:scale-down-policy"},
        ]

        challenge = MagicMock()
        challenge.pk = 1
        challenge.queue = "test_queue"
        challenge.max_ecs_workers = max_ecs_workers
        challenge.min_ecs_workers = min_ecs_workers

        result = setup_auto_scaling_for_service(challenge)
        return mock_autoscaling, result

    @patch("challenges.aws_utils.get_boto3_client")
    def test_setup_auto_scaling_uses_challenge_max_ecs_workers(
        self, mock_get_boto3_client
    ):
        """MaxCapacity and the scale-up target both follow challenge.max_ecs_workers."""
        mock_autoscaling, result = self._run_setup(mock_get_boto3_client, 3)

        self.assertTrue(result)
        register_kwargs = (
            mock_autoscaling.register_scalable_target.call_args.kwargs
        )
        self.assertEqual(register_kwargs["MaxCapacity"], 3)
        self.assertEqual(register_kwargs["MinCapacity"], 1)

        scale_up_kwargs = mock_autoscaling.put_scaling_policy.call_args_list[
            0
        ].kwargs
        self.assertEqual(
            scale_up_kwargs["StepScalingPolicyConfiguration"][
                "StepAdjustments"
            ][0]["ScalingAdjustment"],
            3,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_setup_auto_scaling_defaults_to_one_when_unset(
        self, mock_get_boto3_client
    ):
        """Challenges predating max_ecs_workers keep the original ceiling of 1."""
        mock_autoscaling, result = self._run_setup(mock_get_boto3_client, None)

        self.assertTrue(result)
        self.assertEqual(
            mock_autoscaling.register_scalable_target.call_args.kwargs[
                "MaxCapacity"
            ],
            1,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_setup_auto_scaling_floors_max_ecs_workers_at_one(
        self, mock_get_boto3_client
    ):
        """A ceiling of 0 would wedge the service off permanently."""
        mock_autoscaling, _ = self._run_setup(mock_get_boto3_client, 0)

        self.assertEqual(
            mock_autoscaling.register_scalable_target.call_args.kwargs[
                "MaxCapacity"
            ],
            1,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_setup_auto_scaling_uses_challenge_min_ecs_workers(
        self, mock_get_boto3_client
    ):
        """MinCapacity and scale-down target follow challenge.min_ecs_workers."""
        mock_autoscaling, result = self._run_setup(
            mock_get_boto3_client, max_ecs_workers=3, min_ecs_workers=1
        )

        self.assertTrue(result)
        register_kwargs = (
            mock_autoscaling.register_scalable_target.call_args.kwargs
        )
        self.assertEqual(register_kwargs["MinCapacity"], 1)

        scale_down_kwargs = mock_autoscaling.put_scaling_policy.call_args_list[
            1
        ].kwargs
        self.assertEqual(
            scale_down_kwargs["StepScalingPolicyConfiguration"][
                "StepAdjustments"
            ][0]["ScalingAdjustment"],
            1,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_setup_auto_scaling_defaults_min_ecs_workers_to_zero(
        self, mock_get_boto3_client
    ):
        """Challenges predating min_ecs_workers default to scale-to-zero."""
        mock_autoscaling, result = self._run_setup(
            mock_get_boto3_client, max_ecs_workers=2, min_ecs_workers=None
        )

        self.assertTrue(result)
        self.assertEqual(
            mock_autoscaling.register_scalable_target.call_args.kwargs[
                "MinCapacity"
            ],
            0,
        )
        scale_down_kwargs = mock_autoscaling.put_scaling_policy.call_args_list[
            1
        ].kwargs
        self.assertEqual(
            scale_down_kwargs["StepScalingPolicyConfiguration"][
                "StepAdjustments"
            ][0]["ScalingAdjustment"],
            0,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_setup_auto_scaling_floors_min_ecs_workers_at_zero(
        self, mock_get_boto3_client
    ):
        """Negative min_ecs_workers is clamped to 0."""
        mock_autoscaling, _ = self._run_setup(
            mock_get_boto3_client, max_ecs_workers=2, min_ecs_workers=-1
        )

        self.assertEqual(
            mock_autoscaling.register_scalable_target.call_args.kwargs[
                "MinCapacity"
            ],
            0,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_setup_auto_scaling_clamps_min_to_max(self, mock_get_boto3_client):
        """min_ecs_workers > max_ecs_workers is clamped to max."""
        mock_autoscaling, result = self._run_setup(
            mock_get_boto3_client,
            max_ecs_workers=2,
            min_ecs_workers=5,
        )

        self.assertTrue(result)
        register_kwargs = (
            mock_autoscaling.register_scalable_target.call_args.kwargs
        )
        self.assertEqual(register_kwargs["MinCapacity"], 2)
        self.assertEqual(register_kwargs["MaxCapacity"], 2)
        scale_down_kwargs = mock_autoscaling.put_scaling_policy.call_args_list[
            1
        ].kwargs
        self.assertEqual(
            scale_down_kwargs["StepScalingPolicyConfiguration"][
                "StepAdjustments"
            ][0]["ScalingAdjustment"],
            2,
        )


class TestCleanupAutoScalingForService(unittest.TestCase):
    @patch("challenges.aws_utils.delete_challenge_cleanup_schedule")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_cleanup_auto_scaling_success(
        self, mock_get_boto3_client, mock_delete_schedule
    ):
        mock_autoscaling = MagicMock()
        mock_cloudwatch = MagicMock()

        def side_effect(resource, keys):
            if resource == "application-autoscaling":
                return mock_autoscaling
            elif resource == "cloudwatch":
                return mock_cloudwatch
            return MagicMock()

        mock_get_boto3_client.side_effect = side_effect

        challenge = MagicMock()
        challenge.pk = 1
        challenge.queue = "test_queue"

        cleanup_auto_scaling_for_service(challenge)

        mock_autoscaling.deregister_scalable_target.assert_called_once()
        mock_cloudwatch.delete_alarms.assert_called_once_with(
            AlarmNames=[
                "test_queue_service_scale_up",
                "test_queue_service_scale_down",
            ]
        )
        mock_delete_schedule.assert_called_once_with(challenge)

    @patch("challenges.aws_utils.delete_challenge_cleanup_schedule")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_cleanup_auto_scaling_handles_not_found(
        self, mock_get_boto3_client, mock_delete_schedule
    ):
        """Cleanup should not raise even if resources don't exist."""
        mock_autoscaling = MagicMock()
        mock_autoscaling.deregister_scalable_target.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ObjectNotFoundException"},
                "ResponseMetadata": {"HTTPStatusCode": 400},
            },
            operation_name="DeregisterScalableTarget",
        )
        mock_cloudwatch = MagicMock()
        mock_cloudwatch.delete_alarms.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ResourceNotFound"},
                "ResponseMetadata": {"HTTPStatusCode": 400},
            },
            operation_name="DeleteAlarms",
        )

        def side_effect(resource, keys):
            if resource == "application-autoscaling":
                return mock_autoscaling
            elif resource == "cloudwatch":
                return mock_cloudwatch
            return MagicMock()

        mock_get_boto3_client.side_effect = side_effect

        challenge = MagicMock()
        challenge.pk = 1
        challenge.queue = "test_queue"

        # Should not raise
        cleanup_auto_scaling_for_service(challenge)
        mock_delete_schedule.assert_called_once_with(challenge)

    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_cleanup_auto_scaling_skipped_in_debug(self, mock_settings):
        challenge = MagicMock()
        challenge.pk = 42

        cleanup_auto_scaling_for_service(challenge)


class TestScheduleChallengeCleanup(unittest.TestCase):
    @patch(
        "challenges.aws_utils.EVENTBRIDGE_SCHEDULER_ROLE_ARN",
        "arn:aws:iam::123:role/scheduler-role",
    )
    @patch(
        "challenges.aws_utils.CHALLENGE_CLEANUP_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:cleanup",
    )
    @patch("challenges.aws_utils.settings.ENVIRONMENT", "staging")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_schedule_cleanup_success(self, mock_get_boto3_client):
        mock_scheduler = MagicMock()
        mock_get_boto3_client.return_value = mock_scheduler

        from datetime import datetime

        challenge = MagicMock()
        challenge.pk = 42
        challenge.queue = "test_queue"
        challenge.end_date = datetime(2026, 12, 31, 23, 59, 59)

        schedule_challenge_cleanup(challenge)

        mock_scheduler.create_schedule.assert_called_once()
        call_kwargs = mock_scheduler.create_schedule.call_args[1]
        assert call_kwargs["Name"] == "evalai-cleanup-challenge-staging-42"
        assert call_kwargs["ScheduleExpression"] == "at(2026-12-31T23:59:59)"
        assert call_kwargs["ActionAfterCompletion"] == "DELETE"
        assert "challenge_pk" in call_kwargs["Target"]["Input"]

    @patch(
        "challenges.aws_utils.CHALLENGE_CLEANUP_LAMBDA_ARN",
        "",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_schedule_cleanup_skipped_without_lambda_arn(
        self, mock_get_boto3_client
    ):
        challenge = MagicMock()
        challenge.pk = 42

        schedule_challenge_cleanup(challenge)

        mock_get_boto3_client.assert_not_called()

    @patch(
        "challenges.aws_utils.EVENTBRIDGE_SCHEDULER_ROLE_ARN",
        "arn:aws:iam::123:role/scheduler-role",
    )
    @patch(
        "challenges.aws_utils.CHALLENGE_CLEANUP_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:cleanup",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_schedule_cleanup_client_error(self, mock_get_boto3_client):
        mock_scheduler = MagicMock()
        mock_scheduler.create_schedule.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ServiceException"},
                "ResponseMetadata": {"HTTPStatusCode": 500},
            },
            operation_name="CreateSchedule",
        )
        mock_get_boto3_client.return_value = mock_scheduler

        from datetime import datetime

        challenge = MagicMock()
        challenge.pk = 42
        challenge.queue = "test_queue"
        challenge.end_date = datetime(2026, 12, 31, 23, 59, 59)

        # Should not raise, just log
        schedule_challenge_cleanup(challenge)

    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_schedule_cleanup_skipped_in_debug(self, mock_settings):
        challenge = MagicMock()
        challenge.pk = 42

        schedule_challenge_cleanup(challenge)


class TestUpdateChallengeCleanupSchedule(unittest.TestCase):
    @patch(
        "challenges.aws_utils.EVENTBRIDGE_SCHEDULER_ROLE_ARN",
        "arn:aws:iam::123:role/scheduler-role",
    )
    @patch(
        "challenges.aws_utils.CHALLENGE_CLEANUP_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:cleanup",
    )
    @patch("challenges.aws_utils.settings.ENVIRONMENT", "staging")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_update_schedule_success(self, mock_get_boto3_client):
        mock_scheduler = MagicMock()
        mock_get_boto3_client.return_value = mock_scheduler

        from datetime import datetime

        challenge = MagicMock()
        challenge.pk = 42
        challenge.queue = "test_queue"
        challenge.end_date = datetime(2027, 6, 15, 12, 0, 0)

        update_challenge_cleanup_schedule(challenge)

        mock_scheduler.update_schedule.assert_called_once()
        call_kwargs = mock_scheduler.update_schedule.call_args[1]
        assert call_kwargs["Name"] == "evalai-cleanup-challenge-staging-42"
        assert call_kwargs["ScheduleExpression"] == "at(2027-06-15T12:00:00)"

    @patch(
        "challenges.aws_utils.EVENTBRIDGE_SCHEDULER_ROLE_ARN",
        "arn:aws:iam::123:role/scheduler-role",
    )
    @patch(
        "challenges.aws_utils.CHALLENGE_CLEANUP_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:cleanup",
    )
    @patch("challenges.aws_utils.schedule_challenge_cleanup")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_update_schedule_not_found_creates_new(
        self, mock_get_boto3_client, mock_schedule_cleanup
    ):
        """When the schedule doesn't exist (already fired and auto-deleted),
        create a new one."""
        mock_scheduler = MagicMock()
        mock_scheduler.update_schedule.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ResourceNotFoundException"},
                "ResponseMetadata": {"HTTPStatusCode": 404},
            },
            operation_name="UpdateSchedule",
        )
        mock_get_boto3_client.return_value = mock_scheduler

        from datetime import datetime

        challenge = MagicMock()
        challenge.pk = 42
        challenge.queue = "test_queue"
        challenge.end_date = datetime(2027, 6, 15, 12, 0, 0)

        update_challenge_cleanup_schedule(challenge)

        mock_schedule_cleanup.assert_called_once_with(challenge)

    @patch(
        "challenges.aws_utils.CHALLENGE_CLEANUP_LAMBDA_ARN",
        "",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_update_schedule_skipped_without_lambda_arn(
        self, mock_get_boto3_client
    ):
        challenge = MagicMock()
        challenge.pk = 42

        update_challenge_cleanup_schedule(challenge)

        mock_get_boto3_client.assert_not_called()

    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_update_schedule_skipped_in_debug(self, mock_settings):
        challenge = MagicMock()
        challenge.pk = 42

        update_challenge_cleanup_schedule(challenge)

    @patch(
        "challenges.aws_utils.EVENTBRIDGE_SCHEDULER_ROLE_ARN",
        "arn:aws:iam::123:role/scheduler-role",
    )
    @patch(
        "challenges.aws_utils.CHALLENGE_CLEANUP_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:cleanup",
    )
    @patch("challenges.aws_utils.settings.ENVIRONMENT", "staging")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_update_schedule_other_client_error_logs_exception(
        self, mock_get_boto3_client
    ):
        """Non-ResourceNotFoundException errors should be logged, not re-raised."""
        mock_scheduler = MagicMock()
        mock_scheduler.update_schedule.side_effect = ClientError(
            error_response={
                "Error": {"Code": "InternalServerError"},
                "ResponseMetadata": {"HTTPStatusCode": 500},
            },
            operation_name="UpdateSchedule",
        )
        mock_get_boto3_client.return_value = mock_scheduler

        from datetime import datetime

        challenge = MagicMock()
        challenge.pk = 42
        challenge.queue = "test_queue"
        challenge.end_date = datetime(2027, 6, 15, 12, 0, 0)

        # Should not raise, just log the exception
        update_challenge_cleanup_schedule(challenge)

        mock_scheduler.update_schedule.assert_called_once()


class TestDeleteChallengeCleanupSchedule(unittest.TestCase):
    @patch("challenges.aws_utils.settings.ENVIRONMENT", "staging")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_delete_schedule_success(self, mock_get_boto3_client):
        mock_scheduler = MagicMock()
        mock_get_boto3_client.return_value = mock_scheduler

        challenge = MagicMock()
        challenge.pk = 42

        delete_challenge_cleanup_schedule(challenge)

        mock_scheduler.delete_schedule.assert_called_once_with(
            Name="evalai-cleanup-challenge-staging-42"
        )

    @patch("challenges.aws_utils.get_boto3_client")
    def test_delete_schedule_not_found(self, mock_get_boto3_client):
        """Deleting a non-existent schedule should not raise."""
        mock_scheduler = MagicMock()
        mock_scheduler.delete_schedule.side_effect = ClientError(
            error_response={
                "Error": {"Code": "ResourceNotFoundException"},
                "ResponseMetadata": {"HTTPStatusCode": 404},
            },
            operation_name="DeleteSchedule",
        )
        mock_get_boto3_client.return_value = mock_scheduler

        challenge = MagicMock()
        challenge.pk = 42

        # Should not raise
        delete_challenge_cleanup_schedule(challenge)

    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_delete_schedule_skipped_in_debug(self, mock_settings):
        challenge = MagicMock()
        challenge.pk = 42

        delete_challenge_cleanup_schedule(challenge)


class TestHandleEndDateChange(TestCase):
    @patch("challenges.aws_utils.start_workers")
    def test_end_date_extended_after_cleanup_recreates_workers(
        self, mock_start_workers
    ):
        """When end_date is extended after resources were cleaned up,
        recreate everything."""
        from datetime import timedelta

        from challenges.models import handle_end_date_change_for_challenge
        from django.utils import timezone

        challenge = MagicMock()
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.approved_by_admin = True
        challenge.workers = None  # Resources were cleaned up
        challenge._original_end_date = timezone.now() - timedelta(days=1)
        challenge.end_date = timezone.now() + timedelta(days=30)

        mock_start_workers.return_value = {"count": 1, "failures": []}

        handle_end_date_change_for_challenge(
            sender=None, instance=challenge, created=False
        )

        mock_start_workers.assert_called_once_with([challenge])

    @patch("challenges.aws_utils.update_challenge_cleanup_schedule")
    def test_end_date_extended_with_active_workers_reschedules(
        self, mock_update_schedule
    ):
        """When end_date is extended and workers are still active,
        just reschedule the cleanup."""
        from datetime import timedelta

        from challenges.models import handle_end_date_change_for_challenge
        from django.utils import timezone

        challenge = MagicMock()
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.approved_by_admin = True
        challenge.workers = 1  # Workers still active
        challenge._original_end_date = timezone.now() - timedelta(days=1)
        challenge.end_date = timezone.now() + timedelta(days=60)

        handle_end_date_change_for_challenge(
            sender=None, instance=challenge, created=False
        )

        mock_update_schedule.assert_called_once_with(challenge)

    @patch("challenges.aws_utils.delete_workers")
    def test_end_date_set_to_past_triggers_cleanup(self, mock_delete_workers):
        """When end_date is changed to the past, trigger cleanup."""
        from datetime import timedelta

        from challenges.models import handle_end_date_change_for_challenge
        from django.utils import timezone

        challenge = MagicMock()
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.approved_by_admin = True
        challenge.workers = 1
        challenge._original_end_date = timezone.now() + timedelta(days=30)
        challenge.end_date = timezone.now() - timedelta(days=1)

        mock_delete_workers.return_value = {"count": 1, "failures": []}

        handle_end_date_change_for_challenge(
            sender=None, instance=challenge, created=False
        )

        mock_delete_workers.assert_called_once_with([challenge])

    def test_end_date_change_skipped_for_docker_based(self):
        """Docker-based challenges should be skipped."""
        from datetime import timedelta

        from challenges.models import handle_end_date_change_for_challenge
        from django.utils import timezone

        challenge = MagicMock()
        challenge.is_docker_based = True
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.approved_by_admin = True
        challenge.workers = 1
        challenge._original_end_date = timezone.now() - timedelta(days=1)
        challenge.end_date = timezone.now() + timedelta(days=60)

        # Should not call any AWS functions
        with patch(
            "challenges.aws_utils.update_challenge_cleanup_schedule"
        ) as mock_update:
            handle_end_date_change_for_challenge(
                sender=None, instance=challenge, created=False
            )
            mock_update.assert_not_called()

    def test_end_date_change_skipped_for_unapproved_challenge_without_workers(
        self,
    ):
        """Unapproved challenges with no workers should be skipped."""
        from datetime import timedelta

        from challenges.models import handle_end_date_change_for_challenge
        from django.utils import timezone

        challenge = MagicMock()
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.approved_by_admin = False
        challenge.workers = None
        challenge._original_end_date = timezone.now() - timedelta(days=1)
        challenge.end_date = timezone.now() + timedelta(days=60)

        with patch("challenges.aws_utils.start_workers") as mock_start:
            handle_end_date_change_for_challenge(
                sender=None, instance=challenge, created=False
            )
            mock_start.assert_not_called()

    @patch("challenges.aws_utils.update_challenge_cleanup_schedule")
    def test_end_date_change_proceeds_for_unapproved_challenge_with_workers(
        self, mock_update_schedule
    ):
        """Unapproved challenges with active workers (set up by host
        testing) should still update the EventBridge schedule."""
        from datetime import timedelta

        from challenges.models import handle_end_date_change_for_challenge
        from django.utils import timezone

        challenge = MagicMock()
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.approved_by_admin = False
        challenge.workers = 1  # Workers created via host submission
        challenge._original_end_date = timezone.now() - timedelta(days=1)
        challenge.end_date = timezone.now() + timedelta(days=60)

        handle_end_date_change_for_challenge(
            sender=None, instance=challenge, created=False
        )

        mock_update_schedule.assert_called_once_with(challenge)

    def test_end_date_change_skipped_on_create(self):
        """New challenge creation should not trigger end_date handler."""
        from datetime import timedelta

        from challenges.models import handle_end_date_change_for_challenge
        from django.utils import timezone

        challenge = MagicMock()
        challenge._original_end_date = timezone.now() - timedelta(days=1)
        challenge.end_date = timezone.now() + timedelta(days=60)

        with patch("challenges.aws_utils.start_workers") as mock_start:
            handle_end_date_change_for_challenge(
                sender=None, instance=challenge, created=True
            )
            mock_start.assert_not_called()


class TestEnsureWorkersForSubmission(TestCase):
    @patch("challenges.aws_utils.settings")
    def test_returns_early_in_debug_mode(self, mock_settings):
        """Should return early without calling start_workers in DEBUG mode."""
        mock_settings.DEBUG = True
        challenge = MagicMock()
        challenge.pk = 1

        with patch("challenges.aws_utils.start_workers") as mock_start:
            ensure_workers_for_submission(challenge)
            mock_start.assert_not_called()

    @patch("challenges.aws_utils.settings")
    def test_returns_early_in_test_mode(self, mock_settings):
        """Should return early without calling start_workers in TEST mode."""
        mock_settings.DEBUG = False
        mock_settings.TEST = True
        challenge = MagicMock()
        challenge.pk = 1

        with patch("challenges.aws_utils.start_workers") as mock_start:
            ensure_workers_for_submission(challenge)
            mock_start.assert_not_called()

    @patch("challenges.aws_utils.settings")
    def test_returns_early_for_docker_based_challenge(self, mock_settings):
        """Should skip docker-based challenges."""
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        challenge = MagicMock()
        challenge.pk = 1
        challenge.is_docker_based = True
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False

        with patch("challenges.aws_utils.start_workers") as mock_start:
            ensure_workers_for_submission(challenge)
            mock_start.assert_not_called()

    @patch("challenges.aws_utils.settings")
    def test_returns_early_for_ec2_challenge(self, mock_settings):
        """Should skip EC2-based challenges."""
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        challenge = MagicMock()
        challenge.pk = 1
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = True
        challenge.remote_evaluation = False

        with patch("challenges.aws_utils.start_workers") as mock_start:
            ensure_workers_for_submission(challenge)
            mock_start.assert_not_called()

    @patch("challenges.aws_utils.settings")
    def test_returns_early_for_remote_evaluation_challenge(
        self, mock_settings
    ):
        """Should skip remote evaluation challenges."""
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        challenge = MagicMock()
        challenge.pk = 1
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = True

        with patch("challenges.aws_utils.start_workers") as mock_start:
            ensure_workers_for_submission(challenge)
            mock_start.assert_not_called()

    @patch("challenges.aws_utils.settings")
    def test_returns_early_when_workers_already_exist(self, mock_settings):
        """Should be a no-op when workers are already set up."""
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        challenge = MagicMock()
        challenge.pk = 1
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.workers = 1  # Workers already exist

        with patch("challenges.aws_utils.start_workers") as mock_start:
            ensure_workers_for_submission(challenge)
            mock_start.assert_not_called()

    @patch("challenges.aws_utils.settings")
    def test_starts_workers_when_workers_stopped(self, mock_settings):
        """Should start workers when workers are stopped (0)."""
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        challenge = MagicMock()
        challenge.pk = 1
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.workers = 0  # Workers exist but stopped

        with patch("challenges.aws_utils.start_workers") as mock_start:
            mock_start.return_value = {"count": 1, "failures": []}
            ensure_workers_for_submission(challenge)
            mock_start.assert_called_once_with([challenge])

    @patch("challenges.aws_utils.start_workers")
    @patch("challenges.aws_utils.settings")
    def test_creates_workers_when_none_exist(
        self, mock_settings, mock_start_workers
    ):
        """Should call start_workers when workers is None (stack never created)."""
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        challenge = MagicMock()
        challenge.pk = 1
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.workers = None

        mock_start_workers.return_value = {"count": 1, "failures": []}

        ensure_workers_for_submission(challenge)

        mock_start_workers.assert_called_once_with([challenge])

    @patch("challenges.aws_utils.start_workers")
    @patch("challenges.aws_utils.settings")
    def test_logs_error_when_worker_creation_fails(
        self, mock_settings, mock_start_workers
    ):
        """Should log error when start_workers fails."""
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        challenge = MagicMock()
        challenge.pk = 1
        challenge.is_docker_based = False
        challenge.uses_ec2_worker = False
        challenge.remote_evaluation = False
        challenge.workers = None

        mock_start_workers.return_value = {
            "count": 0,
            "failures": [
                {"message": "Service creation failed", "challenge_pk": 1}
            ],
        }

        # Should not raise, just log the error
        ensure_workers_for_submission(challenge)

        mock_start_workers.assert_called_once_with([challenge])


class TestGetCapacityProviderStrategy:
    def test_spot_only_defaults(self):
        challenge = MagicMock()
        challenge.fargate_spot_weight = 1
        challenge.fargate_spot_base = 0
        challenge.fargate_weight = 0
        challenge.fargate_base = 0
        challenge.use_fargate_spot = True

        result = get_capacity_provider_strategy(challenge)
        assert len(result) == 1
        assert result[0]["capacityProvider"] == "FARGATE_SPOT"
        assert result[0]["weight"] == 1
        assert result[0]["base"] == 0

    def test_mixed_strategy(self):
        challenge = MagicMock()
        challenge.fargate_spot_weight = 3
        challenge.fargate_spot_base = 0
        challenge.fargate_weight = 1
        challenge.fargate_base = 1
        challenge.use_fargate_spot = True

        result = get_capacity_provider_strategy(challenge)
        assert len(result) == 2
        spot = next(
            p for p in result if p["capacityProvider"] == "FARGATE_SPOT"
        )
        fargate = next(p for p in result if p["capacityProvider"] == "FARGATE")
        assert spot["weight"] == 3
        assert spot["base"] == 0
        assert fargate["weight"] == 1
        assert fargate["base"] == 1

    def test_fargate_only_via_weights(self):
        challenge = MagicMock()
        challenge.fargate_spot_weight = 0
        challenge.fargate_spot_base = 0
        challenge.fargate_weight = 1
        challenge.fargate_base = 0
        challenge.use_fargate_spot = True

        result = get_capacity_provider_strategy(challenge)
        assert len(result) == 1
        assert result[0]["capacityProvider"] == "FARGATE"

    def test_fallback_when_both_weights_zero(self):
        challenge = MagicMock()
        challenge.fargate_spot_weight = 0
        challenge.fargate_spot_base = 0
        challenge.fargate_weight = 0
        challenge.fargate_base = 0
        challenge.use_fargate_spot = True

        result = get_capacity_provider_strategy(challenge)
        assert len(result) == 1
        assert result[0]["capacityProvider"] == "FARGATE_SPOT"
        assert result[0]["weight"] == 1

    def test_spot_with_base(self):
        challenge = MagicMock()
        challenge.fargate_spot_weight = 2
        challenge.fargate_spot_base = 3
        challenge.fargate_weight = 0
        challenge.fargate_base = 0
        challenge.use_fargate_spot = True

        result = get_capacity_provider_strategy(challenge)
        assert len(result) == 1
        assert result[0]["capacityProvider"] == "FARGATE_SPOT"
        assert result[0]["weight"] == 2
        assert result[0]["base"] == 3


class TestCreateServiceFargateSpot:
    def test_create_service_with_fargate_spot(
        self, mock_client, mock_challenge, client_token
    ):
        mock_challenge.workers = None
        mock_challenge.task_def_arn = "valid_task_def_arn"
        mock_challenge.use_fargate_spot = True
        mock_challenge.fargate_spot_weight = 1
        mock_challenge.fargate_spot_base = 0
        mock_challenge.fargate_weight = 0
        mock_challenge.fargate_base = 0
        mock_challenge.pk = 42

        response_metadata = {"HTTPStatusCode": HTTPStatus.OK}
        mock_client.create_service.return_value = {
            "ResponseMetadata": response_metadata
        }

        with patch(
            "challenges.aws_utils.register_task_def_by_challenge_pk",
            return_value={"ResponseMetadata": response_metadata},
        ), patch(
            "challenges.aws_utils.setup_auto_scaling_for_service",
        ), patch(
            "challenges.aws_utils.schedule_challenge_cleanup",
        ):
            response = create_service_by_challenge_pk(
                mock_client, mock_challenge, client_token
            )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
        assert mock_challenge.workers == 1

        call_kwargs = mock_client.create_service.call_args[1]
        assert "capacityProviderStrategy" in call_kwargs
        assert "launchType" not in call_kwargs
        strategy = call_kwargs["capacityProviderStrategy"]
        assert len(strategy) == 1
        assert strategy[0]["capacityProvider"] == "FARGATE_SPOT"

    def test_create_service_with_fargate_launch_type(
        self, mock_client, mock_challenge, client_token
    ):
        mock_challenge.workers = None
        mock_challenge.task_def_arn = "valid_task_def_arn"
        mock_challenge.use_fargate_spot = False
        mock_challenge.pk = 42

        response_metadata = {"HTTPStatusCode": HTTPStatus.OK}
        mock_client.create_service.return_value = {
            "ResponseMetadata": response_metadata
        }

        with patch(
            "challenges.aws_utils.register_task_def_by_challenge_pk",
            return_value={"ResponseMetadata": response_metadata},
        ), patch(
            "challenges.aws_utils.setup_auto_scaling_for_service",
        ), patch(
            "challenges.aws_utils.schedule_challenge_cleanup",
        ):
            response = create_service_by_challenge_pk(
                mock_client, mock_challenge, client_token
            )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
        assert mock_challenge.workers == 1

        call_kwargs = mock_client.create_service.call_args[1]
        assert "launchType" in call_kwargs
        assert call_kwargs["launchType"] == "FARGATE"
        assert "capacityProviderStrategy" not in call_kwargs

    def test_create_service_with_mixed_strategy(
        self, mock_client, mock_challenge, client_token
    ):
        mock_challenge.workers = None
        mock_challenge.task_def_arn = "valid_task_def_arn"
        mock_challenge.use_fargate_spot = True
        mock_challenge.fargate_spot_weight = 3
        mock_challenge.fargate_spot_base = 0
        mock_challenge.fargate_weight = 1
        mock_challenge.fargate_base = 1
        mock_challenge.pk = 42

        response_metadata = {"HTTPStatusCode": HTTPStatus.OK}
        mock_client.create_service.return_value = {
            "ResponseMetadata": response_metadata
        }

        with patch(
            "challenges.aws_utils.register_task_def_by_challenge_pk",
            return_value={"ResponseMetadata": response_metadata},
        ), patch(
            "challenges.aws_utils.setup_auto_scaling_for_service",
        ), patch(
            "challenges.aws_utils.schedule_challenge_cleanup",
        ):
            response = create_service_by_challenge_pk(
                mock_client, mock_challenge, client_token
            )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK

        call_kwargs = mock_client.create_service.call_args[1]
        assert "capacityProviderStrategy" in call_kwargs
        assert "launchType" not in call_kwargs
        strategy = call_kwargs["capacityProviderStrategy"]
        assert len(strategy) == 2
        spot = next(
            p for p in strategy if p["capacityProvider"] == "FARGATE_SPOT"
        )
        fargate = next(
            p for p in strategy if p["capacityProvider"] == "FARGATE"
        )
        assert spot["weight"] == 3
        assert fargate["weight"] == 1
        assert fargate["base"] == 1


class TestTriggerEksNodeAutoscale:
    @patch("challenges.aws_utils.settings")
    @patch("challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN", "")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_skip_when_lambda_not_configured(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False

        trigger_eks_node_autoscale(11, "submission_created")

        mock_get_boto3_client.assert_not_called()

    @patch("challenges.aws_utils.settings")
    @patch(
        "challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:autoscale",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_invokes_lambda_with_event_payload(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        mock_lambda_client = MagicMock()
        mock_get_boto3_client.return_value = mock_lambda_client

        trigger_eks_node_autoscale(
            21,
            "submission_status_changed",
            submission_pk=77,
            submission_status="running",
        )

        mock_get_boto3_client.assert_called_once()
        kwargs = mock_lambda_client.invoke.call_args.kwargs
        assert kwargs["FunctionName"] == (
            "arn:aws:lambda:us-east-1:123:function:autoscale"
        )
        assert kwargs["InvocationType"] == "Event"
        payload = json.loads(kwargs["Payload"].decode("utf-8"))
        assert payload["challenge_pk"] == 21
        assert payload["trigger_source"] == "submission_status_changed"
        assert payload["submission_pk"] == 77
        assert payload["submission_status"] == "running"

    @patch("challenges.aws_utils.settings")
    @patch(
        "challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:autoscale",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_skip_in_debug_or_test(self, mock_get_boto3_client, mock_settings):
        mock_settings.DEBUG = True
        mock_settings.TEST = False
        trigger_eks_node_autoscale(11, "submission_created")
        mock_get_boto3_client.assert_not_called()

        mock_get_boto3_client.reset_mock()
        mock_settings.DEBUG = False
        mock_settings.TEST = True
        trigger_eks_node_autoscale(11, "submission_created")
        mock_get_boto3_client.assert_not_called()

    @patch("challenges.aws_utils.settings")
    @patch(
        "challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:autoscale",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_logs_boto_core_error_without_raising(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        mock_get_boto3_client.side_effect = NoCredentialsError()

        trigger_eks_node_autoscale(11, "submission_created")

        mock_get_boto3_client.assert_called_once()

    @patch("challenges.aws_utils.settings")
    @patch(
        "challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:autoscale",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_skip_for_message_republished_event(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False

        trigger_eks_node_autoscale(
            42,
            "submission_message_republished",
            submission_pk=3,
            submission_status="submitted",
        )
        mock_get_boto3_client.assert_not_called()

    @patch("challenges.aws_utils.settings")
    @patch(
        "challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:autoscale",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_skip_when_pending_boundary_unchanged(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False

        trigger_eks_node_autoscale(
            42,
            "submission_status_changed",
            submission_pk=3,
            submission_status="running",
            previous_submission_status="queued",
        )
        mock_get_boto3_client.assert_not_called()

    @patch("challenges.aws_utils.settings")
    @patch(
        "challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:autoscale",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_invoke_when_crossing_pending_boundary(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        mock_lambda_client = MagicMock()
        mock_get_boto3_client.return_value = mock_lambda_client

        trigger_eks_node_autoscale(
            42,
            "submission_status_changed",
            submission_pk=3,
            submission_status="running",
            previous_submission_status="failed",
        )
        mock_lambda_client.invoke.assert_called_once()

    @patch("challenges.aws_utils.settings")
    @patch(
        "challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN",
        "arn:aws:lambda:us-east-1:123:function:autoscale",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_skip_for_irrelevant_status_value(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False

        trigger_eks_node_autoscale(
            42,
            "submission_status_changed",
            submission_pk=3,
            submission_status="submitting",
            previous_submission_status="submitting",
        )
        mock_get_boto3_client.assert_not_called()

    @patch("challenges.aws_utils.settings")
    @patch(
        "challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN",
        "arn:aws:iam::937891341272:role/evalai-lambda-execution-role",
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_skip_when_lambda_arn_is_iam_role(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False

        trigger_eks_node_autoscale(11, "submission_created")

        mock_get_boto3_client.assert_not_called()

    @patch("challenges.aws_utils.settings")
    @patch(
        "challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN",
        "arn:aws:iam::937891341272:role/evalai-lambda-execution-role",
    )
    @patch.dict(
        os.environ,
        {
            "EKS_NODE_AUTOSCALE_LAMBDA_FUNCTION_NAME": "auto_scale_eks_nodes_lambda"
        },
        clear=False,
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_uses_function_name_env_var_over_misconfigured_arn(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        mock_lambda_client = MagicMock()
        mock_get_boto3_client.return_value = mock_lambda_client

        trigger_eks_node_autoscale(11, "submission_created")

        mock_get_boto3_client.assert_called_once()
        kwargs = mock_lambda_client.invoke.call_args.kwargs
        assert kwargs["FunctionName"] == "auto_scale_eks_nodes_lambda"

    @patch("challenges.aws_utils.settings")
    @patch("challenges.aws_utils.EKS_NODE_AUTOSCALE_LAMBDA_ARN", "")
    @patch.dict(
        os.environ,
        {
            "EKS_NODE_AUTOSCALE_LAMBDA_FUNCTION_NAME": "auto_scale_eks_nodes_lambda"
        },
        clear=False,
    )
    @patch("challenges.aws_utils.get_boto3_client")
    def test_uses_function_name_env_var_when_arn_empty(
        self, mock_get_boto3_client, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_settings.TEST = False
        mock_lambda_client = MagicMock()
        mock_get_boto3_client.return_value = mock_lambda_client

        trigger_eks_node_autoscale(11, "submission_created")

        mock_get_boto3_client.assert_called_once()
        kwargs = mock_lambda_client.invoke.call_args.kwargs
        assert kwargs["FunctionName"] == "auto_scale_eks_nodes_lambda"


class TestWorkerImageHelpers(TestCase):
    def test_normalize_worker_python_version_defaults_to_py39(self):
        self.assertEqual(normalize_worker_python_version(None), "3.9")
        self.assertEqual(normalize_worker_python_version(""), "3.9")
        self.assertEqual(normalize_worker_python_version("3.8"), "3.8")
        self.assertEqual(normalize_worker_python_version("invalid"), "3.9")

    def test_ensure_challenge_worker_python_version_persists_default(self):
        challenge = MagicMock(worker_python_version=None)
        version = ensure_challenge_worker_python_version(challenge)
        self.assertEqual(version, "3.9")
        self.assertEqual(challenge.worker_python_version, "3.9")
        challenge.save.assert_called_once_with(
            update_fields=["worker_python_version"]
        )

    def test_ensure_challenge_worker_python_version_no_op_when_valid(self):
        challenge = MagicMock(worker_python_version="3.8")
        version = ensure_challenge_worker_python_version(challenge)
        self.assertEqual(version, "3.8")
        challenge.save.assert_not_called()

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_evalai_submission_worker_ecr_image_defaults_to_py39(self):
        image = get_evalai_submission_worker_ecr_image()
        self.assertEqual(
            image,
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/evalai-production-worker-py3.9:latest",
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "prod")
    def test_get_evalai_submission_worker_ecr_image_maps_settings_prod_env(
        self,
    ):
        image = get_evalai_submission_worker_ecr_image(commit_id="abc123")
        self.assertEqual(
            image,
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/evalai-production-worker-py3.9:abc123",
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "prod")
    def test_is_evalai_managed_submission_worker_image_accepts_production_repo(
        self,
    ):
        image_url = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-worker-py3.9:oldsha"
        )
        self.assertTrue(is_evalai_managed_submission_worker_image(image_url))

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_evalai_submission_worker_ecr_image_invalid_version(self):
        image = get_evalai_submission_worker_ecr_image(python_version="3.11")
        self.assertTrue(image.endswith("worker-py3.9:latest"))

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_worker_image_for_challenge_uses_python_version(self):
        challenge = MagicMock(
            worker_image_url=None,
            worker_python_version="3.8",
        )
        image = get_worker_image_for_challenge(challenge, commit_id="abc123")
        self.assertEqual(
            image,
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/evalai-production-worker-py3.8:abc123",
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_worker_image_for_challenge_invalid_version_falls_back(
        self,
    ):
        challenge = MagicMock(
            worker_image_url=None,
            worker_python_version="3.11",
        )
        image = get_worker_image_for_challenge(challenge, commit_id="abc123")
        self.assertTrue(image.endswith("worker-py3.9:abc123"))

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_worker_image_for_challenge_updates_evalai_managed_tag(self):
        challenge = MagicMock(
            worker_image_url=(
                "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
                "evalai-production-worker-py3.7:oldsha"
            ),
            worker_python_version="3.7",
        )
        self.assertTrue(
            is_evalai_managed_submission_worker_image(
                challenge.worker_image_url
            )
        )
        image = get_worker_image_for_challenge(challenge, commit_id="newsha")
        self.assertEqual(
            image,
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-worker-py3.7:newsha",
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_worker_image_for_challenge_uses_python_version_for_evalai_image(
        self,
    ):
        challenge = MagicMock(
            worker_image_url=(
                "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
                "evalai-production-worker-py3.7:oldsha"
            ),
            worker_python_version="3.9",
        )
        image = get_worker_image_for_challenge(challenge, commit_id="newsha")
        self.assertEqual(
            image,
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-worker-py3.9:newsha",
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_worker_image_for_challenge_preserves_evalai_tag_without_commit_id(
        self,
    ):
        challenge = MagicMock(
            worker_image_url=(
                "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
                "evalai-production-worker-py3.7:pinnedsha"
            ),
            worker_python_version="3.9",
        )
        image = get_worker_image_for_challenge(challenge)
        self.assertEqual(
            image,
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-worker-py3.9:pinnedsha",
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_worker_image_for_challenge_preserves_custom_image_url(self):
        custom_image = "myregistry.example.com/custom-worker:v1.2.3"
        challenge = MagicMock(worker_image_url=custom_image)
        self.assertFalse(
            is_evalai_managed_submission_worker_image(custom_image)
        )

        image = get_worker_image_for_challenge(challenge, commit_id="newsha")

        self.assertEqual(image, custom_image)

    def test_get_worker_image_for_challenge_returns_custom_url_without_commit_id(
        self,
    ):
        custom_image = "myregistry.example.com/custom-worker:stable"
        challenge = MagicMock(worker_image_url=custom_image)

        image = get_worker_image_for_challenge(challenge)

        self.assertEqual(image, custom_image)

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_worker_image_for_challenge_defaults_to_py39(self):
        challenge = MagicMock(
            worker_image_url=None,
            worker_python_version=None,
        )
        image = get_worker_image_for_challenge(challenge, commit_id="abc123")
        self.assertEqual(
            image,
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/evalai-production-worker-py3.9:abc123",
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_image_settings_for_challenge_preserves_custom_worker_image(
        self,
    ):
        custom_image = "myregistry.example.com/custom-worker:stable"
        challenge = MagicMock(
            worker_image_url=custom_image,
            worker_python_version="3.8",
        )
        settings_dict = get_image_settings_for_challenge(
            challenge, commit_id="newsha"
        )
        self.assertEqual(settings_dict["WORKER_IMAGE"], custom_image)
        self.assertTrue(
            settings_dict["CODE_UPLOAD_WORKER_IMAGE"].endswith(
                "code-upload-worker:newsha"
            )
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.update_service_by_challenge_pk")
    def test_refresh_task_definition_for_challenge_preserves_custom_worker_image(
        self,
        mock_update_service,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        custom_image = "myregistry.example.com/custom-worker:stable"
        challenge = MagicMock(
            pk=1,
            queue="test_queue",
            workers=1,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
            worker_image_url=custom_image,
            worker_python_version="3.8",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_build_task_definition.return_value = (
            {"family": "test_queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:task-def/new:2"
            },
        }
        mock_update_service.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        refresh_task_definition_for_challenge(
            challenge, commit_id="newsha", client=mock_client
        )

        image_settings = mock_build_task_definition.call_args.kwargs[
            "image_settings"
        ]
        self.assertEqual(image_settings["WORKER_IMAGE"], custom_image)

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.update_service_by_challenge_pk")
    def test_refresh_task_definition_for_challenge_syncs_evalai_worker_image_url(
        self,
        mock_update_service,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        challenge = MagicMock(
            pk=1,
            queue="test_queue",
            workers=1,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
            worker_image_url=(
                "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
                "evalai-production-worker-py3.7:oldsha"
            ),
            worker_python_version="3.9",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_build_task_definition.return_value = (
            {"family": "test_queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:task-def/new:2"
            },
        }
        mock_update_service.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        refresh_task_definition_for_challenge(
            challenge, commit_id="newsha", client=mock_client
        )

        self.assertEqual(
            challenge.worker_image_url,
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-worker-py3.9:newsha",
        )
        challenge.save.assert_called_once_with(
            update_fields=["task_def_arn", "worker_image_url"]
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.update_service_by_challenge_pk")
    def test_refresh_task_definition_for_challenge_skips_worker_image_url_when_already_synced(
        self,
        mock_update_service,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        resolved_image = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-worker-py3.9:newsha"
        )
        challenge = MagicMock(
            pk=1,
            queue="test_queue",
            workers=1,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
            worker_image_url=resolved_image,
            worker_python_version="3.9",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_build_task_definition.return_value = (
            {"family": "test_queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:task-def/new:2"
            },
        }
        mock_update_service.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        refresh_task_definition_for_challenge(
            challenge, commit_id="newsha", client=mock_client
        )

        self.assertEqual(challenge.worker_image_url, resolved_image)
        challenge.save.assert_called_once_with(update_fields=["task_def_arn"])

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_image_settings_for_challenge(self):
        challenge = MagicMock(
            worker_image_url=None,
            worker_python_version="3.9",
        )
        settings_dict = get_image_settings_for_challenge(
            challenge, commit_id="abc123"
        )
        self.assertIn("WORKER_IMAGE", settings_dict)
        self.assertIn("CODE_UPLOAD_WORKER_IMAGE", settings_dict)
        self.assertTrue(
            settings_dict["WORKER_IMAGE"].endswith("worker-py3.9:abc123")
        )
        self.assertTrue(
            settings_dict["CODE_UPLOAD_WORKER_IMAGE"].endswith(
                "code-upload-worker:abc123"
            )
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.get_image_settings_for_challenge")
    def test_refresh_task_definition_for_challenge_creates_ecs_client(
        self,
        mock_get_image_settings,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        challenge = MagicMock(
            pk=15,
            queue="test_queue",
            workers=0,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_get_image_settings.return_value = {"WORKER_IMAGE": "image:tag"}
        mock_build_task_definition.return_value = (
            {"family": "test_queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:task-def/new:2"
            },
        }
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        response = refresh_task_definition_for_challenge(challenge)

        mock_get_boto3_client.assert_called_once()
        self.assertEqual(
            response["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK
        )
        mock_client.register_task_definition.assert_called_once()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.get_image_settings_for_challenge")
    @patch("challenges.aws_utils.service_manager")
    def test_refresh_task_definition_for_challenge(
        self,
        mock_service_manager,
        mock_get_image_settings,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        challenge = MagicMock(
            pk=1,
            queue="test_queue",
            workers=1,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_get_image_settings.return_value = {"WORKER_IMAGE": "image:tag"}
        mock_build_task_definition.return_value = (
            {"family": "test_queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:task-def/new:2"
            },
        }
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        response = refresh_task_definition_for_challenge(
            challenge, commit_id="abc123", client=mock_client
        )

        self.assertEqual(
            response["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK
        )
        self.assertEqual(challenge.task_def_arn, "arn:aws:ecs:task-def/new:2")
        mock_service_manager.assert_called_once_with(
            mock_client,
            challenge,
            num_of_tasks=1,
            force_new_deployment=True,
        )
        mock_client.deregister_task_definition.assert_called_once_with(
            taskDefinition="arn:aws:ecs:task-def/old:1"
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.get_image_settings_for_challenge")
    @patch("challenges.aws_utils.create_service_by_challenge_pk")
    @patch("challenges.aws_utils.client_token_generator")
    @patch("challenges.aws_utils.update_service_by_challenge_pk")
    def test_refresh_task_definition_for_challenge_service_not_found(
        self,
        mock_update_service,
        mock_client_token_generator,
        mock_create_service,
        mock_get_image_settings,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        challenge = MagicMock(
            pk=2698,
            queue="test_queue",
            workers=1,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_get_image_settings.return_value = {"WORKER_IMAGE": "image:tag"}
        mock_build_task_definition.return_value = (
            {"family": "test_queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:task-def/new:2"
            },
        }
        mock_update_service.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": {
                "Code": "ServiceNotFoundException",
                "Message": "Service not found.",
            },
        }
        mock_client_token_generator.return_value = "mock_client_token"
        mock_create_service.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        response = refresh_task_definition_for_challenge(
            challenge, commit_id="abc123", client=mock_client
        )

        self.assertEqual(
            response["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK
        )
        self.assertEqual(challenge.task_def_arn, "arn:aws:ecs:task-def/new:2")
        mock_client_token_generator.assert_called_once_with(challenge.pk)
        mock_create_service.assert_called_once_with(
            mock_client, challenge, "mock_client_token"
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_deployed_worker_image_urls(self):
        urls = get_deployed_worker_image_urls(
            commit_id="abc123", python_version="3.8"
        )
        self.assertTrue(urls["WORKER_IMAGE"].endswith("worker-py3.8:abc123"))
        self.assertTrue(
            urls["CODE_UPLOAD_WORKER_IMAGE"].endswith(
                "code-upload-worker:abc123"
            )
        )

    @patch.dict(
        "os.environ", {"CELERY_QUEUE_NAME": "evalai-celery"}, clear=False
    )
    @patch("challenges.aws_utils.JwtToken.objects.get")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.task_definition")
    def test_build_task_definition_dict_normal_challenge(
        self,
        mock_task_definition,
        mock_get_aws_credentials,
        mock_cluster_get,
        mock_jwt_get,
    ):
        challenge = MagicMock(
            pk=1,
            is_docker_based=False,
            worker_cpu_cores=1024,
            worker_memory=2048,
            ephemeral_storage=21,
        )
        mock_get_aws_credentials.return_value = {}
        mock_task_definition.format.return_value = "{'family': 'queue'}"
        with patch(
            "challenges.aws_utils.load_aws_api_kwargs",
            side_effect=lambda value: {"family": "queue"},
        ):
            task_def, error = build_task_definition_dict(challenge, "queue")
        self.assertIsNone(error)
        self.assertEqual(task_def, {"family": "queue"})
        mock_task_definition.format.assert_called_once()

    @patch.dict(
        "os.environ", {"CELERY_QUEUE_NAME": "evalai-celery"}, clear=False
    )
    @patch("challenges.aws_utils.JwtToken.objects.get")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.task_definition_code_upload_worker")
    def test_build_task_definition_dict_code_upload_challenge(
        self,
        mock_task_definition,
        mock_get_aws_credentials,
        mock_cluster_get,
        mock_jwt_get,
    ):
        challenge = MagicMock(
            pk=1,
            is_docker_based=True,
            is_static_dataset_code_upload=False,
            worker_cpu_cores=1024,
            worker_memory=2048,
            ephemeral_storage=21,
            creator=MagicMock(created_by=MagicMock()),
        )
        mock_cluster_get.return_value = MagicMock(
            name="cluster",
            cluster_endpoint="endpoint",
            cluster_ssl="ssl",
            efs_id="efs",
        )
        mock_jwt_get.return_value = MagicMock(refresh_token="token")
        mock_get_aws_credentials.return_value = {}
        mock_task_definition.format.return_value = "{'family': 'queue'}"
        with patch(
            "challenges.aws_utils.load_aws_api_kwargs",
            side_effect=lambda value: {"family": "queue"},
        ):
            task_def, error = build_task_definition_dict(challenge, "queue")
        self.assertIsNone(error)
        self.assertEqual(task_def, {"family": "queue"})

    @patch.dict(
        "os.environ", {"CELERY_QUEUE_NAME": "evalai-celery"}, clear=False
    )
    @patch("challenges.aws_utils.JwtToken.objects.get")
    @patch("challenges.models.ChallengeEvaluationCluster.objects.get")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.task_definition_static_code_upload_worker")
    @patch("challenges.aws_utils.container_definition_submission_worker")
    @patch("challenges.aws_utils.container_definition_code_upload_worker")
    def test_build_task_definition_dict_static_code_upload_challenge(
        self,
        mock_code_upload_container,
        mock_submission_container,
        mock_task_definition,
        mock_get_aws_credentials,
        mock_cluster_get,
        mock_jwt_get,
    ):
        challenge = MagicMock(
            pk=1,
            is_docker_based=True,
            is_static_dataset_code_upload=True,
            worker_cpu_cores=1024,
            worker_memory=2048,
            ephemeral_storage=21,
            creator=MagicMock(created_by=MagicMock()),
        )
        mock_cluster_get.return_value = MagicMock(
            name="cluster",
            cluster_endpoint="endpoint",
            cluster_ssl="ssl",
            efs_id="efs",
        )
        mock_jwt_get.return_value = MagicMock(refresh_token="token")
        mock_get_aws_credentials.return_value = {}
        mock_code_upload_container.format.return_value = "{}"
        mock_submission_container.format.return_value = "{}"
        mock_task_definition.format.return_value = "{'family': 'queue'}"
        with patch(
            "challenges.aws_utils.load_aws_api_kwargs",
            side_effect=lambda value: {"family": "queue"},
        ):
            task_def, error = build_task_definition_dict(challenge, "queue")
        self.assertIsNone(error)
        self.assertEqual(task_def, {"family": "queue"})

    @patch.dict("os.environ", {}, clear=True)
    def test_build_task_definition_dict_requires_celery_queue_name(self):
        challenge = MagicMock(
            pk=1,
            is_docker_based=False,
            worker_cpu_cores=1024,
            worker_memory=2048,
            ephemeral_storage=21,
        )

        task_def, error = build_task_definition_dict(challenge, "queue")

        self.assertIsNone(task_def)
        self.assertIn("CELERY_QUEUE_NAME", error["Error"])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_refresh_worker_task_definitions_partial_failure(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        challenge_ok = MagicMock(pk=1)
        challenge_fail = MagicMock(pk=2)
        mock_refresh_task_definition.side_effect = [
            {"ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}},
            {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
                "Error": "refresh failed",
            },
        ]

        response = refresh_worker_task_definitions(
            queryset=[challenge_ok, challenge_fail], commit_id="abc123"
        )

        self.assertEqual(response["count"], 1)
        self.assertEqual(len(response["failures"]), 1)
        self.assertEqual(response["failures"][0]["challenge_pk"], 2)
        mock_refresh_task_definition.assert_any_call(
            challenge_ok,
            commit_id="abc123",
            client=mock_get_boto3_client.return_value,
        )
        mock_refresh_task_definition.assert_any_call(
            challenge_fail,
            commit_id="abc123",
            client=mock_get_boto3_client.return_value,
        )

    @patch("challenges.aws_utils.settings", DEBUG=True)
    def test_refresh_worker_task_definitions_debug_environment(
        self, mock_settings
    ):
        challenge = MagicMock(pk=5)
        response = refresh_worker_task_definitions(queryset=[challenge])
        self.assertEqual(response["count"], 0)
        self.assertEqual(len(response["failures"]), 1)
        self.assertEqual(response["failures"][0]["challenge_pk"], 5)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_refresh_worker_task_definitions_dry_run(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        challenges = [MagicMock(pk=1), MagicMock(pk=2)]
        response = refresh_worker_task_definitions(
            queryset=challenges, commit_id="abc123", dry_run=True
        )
        self.assertEqual(response["count"], 2)
        self.assertEqual(response["failures"], [])
        mock_refresh_task_definition.assert_not_called()
        mock_get_boto3_client.assert_not_called()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.models.Challenge.objects.filter")
    def test_refresh_worker_task_definitions_default_queryset(
        self,
        mock_filter,
        mock_refresh_task_definition,
        mock_get_boto3_client,
        mock_settings,
    ):
        challenge = MagicMock(pk=20)
        mock_filter.return_value.exclude.return_value = [challenge]
        mock_refresh_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
        }

        response = refresh_worker_task_definitions()

        mock_filter.assert_called_once()
        mock_filter.return_value.exclude.assert_called_once_with(
            task_def_arn=""
        )
        mock_refresh_task_definition.assert_called_once_with(
            challenge,
            commit_id=None,
            client=mock_get_boto3_client.return_value,
        )
        self.assertEqual(response, {"count": 1, "failures": []})

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_refresh_worker_task_definitions_skipped_challenge(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        mock_refresh_task_definition.return_value = {
            "skipped": True,
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
        }
        challenge = MagicMock(pk=6)
        response = refresh_worker_task_definitions(queryset=[challenge])
        self.assertEqual(response["count"], 0)
        self.assertEqual(response["failures"], [])

    def test_refresh_task_definition_for_challenge_skipped_ec2_worker(self):
        challenge = MagicMock(
            uses_ec2_worker=True,
            remote_evaluation=False,
        )
        response = refresh_task_definition_for_challenge(challenge)
        self.assertTrue(response.get("skipped"))

    def test_refresh_task_definition_for_challenge_skipped_remote_evaluation(
        self,
    ):
        challenge = MagicMock(
            uses_ec2_worker=False,
            remote_evaluation=True,
        )
        response = refresh_task_definition_for_challenge(challenge)
        self.assertTrue(response.get("skipped"))

    def test_refresh_task_definition_for_challenge_missing_task_def_arn(self):
        challenge = MagicMock(
            pk=7,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn=None,
        )
        response = refresh_task_definition_for_challenge(challenge)
        self.assertIn("Error", response)
        self.assertEqual(
            response["ResponseMetadata"]["HTTPStatusCode"],
            HTTPStatus.BAD_REQUEST,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.get_image_settings_for_challenge")
    @patch("challenges.aws_utils.update_service_by_challenge_pk")
    def test_refresh_task_definition_for_challenge_without_active_workers(
        self,
        mock_update_service,
        mock_get_image_settings,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        challenge = MagicMock(
            pk=8,
            queue="test_queue",
            workers=0,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_get_image_settings.return_value = {"WORKER_IMAGE": "image:tag"}
        mock_build_task_definition.return_value = (
            {"family": "test_queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:task-def/new:3"
            },
        }

        response = refresh_task_definition_for_challenge(
            challenge, commit_id="abc123", client=mock_client
        )

        self.assertEqual(
            response["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK
        )
        mock_update_service.assert_not_called()
        mock_client.deregister_task_definition.assert_called_once_with(
            taskDefinition="arn:aws:ecs:task-def/old:1"
        )

    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.get_image_settings_for_challenge")
    def test_refresh_task_definition_for_challenge_deregister_failure(
        self,
        mock_get_image_settings,
        mock_build_task_definition,
        mock_get_boto3_client,
        mock_logger,
    ):
        challenge = MagicMock(
            pk=9,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
            workers=0,
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_get_image_settings.return_value = {"WORKER_IMAGE": "image:tag"}
        mock_build_task_definition.return_value = (
            {"family": "queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:task-def/new:2"
            },
        }
        mock_client.deregister_task_definition.side_effect = ClientError(
            {"Error": {"Message": "deregister failed"}},
            "DeregisterTaskDefinition",
        )

        response = refresh_task_definition_for_challenge(
            challenge, client=mock_client
        )

        self.assertEqual(
            response["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK
        )
        self.assertEqual(challenge.task_def_arn, "arn:aws:ecs:task-def/new:2")
        mock_logger.warning.assert_called_once()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.get_image_settings_for_challenge")
    def test_refresh_task_definition_for_challenge_build_failure(
        self,
        mock_get_image_settings,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        challenge = MagicMock(
            pk=10,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_get_image_settings.return_value = {"WORKER_IMAGE": "image:tag"}
        mock_build_task_definition.return_value = (
            None,
            {
                "Error": "build failed",
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            },
        )

        response = refresh_task_definition_for_challenge(
            challenge, client=mock_client
        )

        self.assertEqual(response["Error"], "build failed")
        self.assertEqual(challenge.task_def_arn, "arn:aws:ecs:task-def/old:1")
        challenge.save.assert_not_called()
        mock_client.deregister_task_definition.assert_not_called()
        mock_client.register_task_definition.assert_not_called()

    def test_load_aws_api_kwargs_parses_dict_literal(self):
        kwargs = load_aws_api_kwargs(
            "{'cluster': 'evalai-prod-cluster', 'forceNewDeployment': True}"
        )
        self.assertEqual(kwargs["cluster"], "evalai-prod-cluster")
        self.assertTrue(kwargs["forceNewDeployment"])

    def test_strip_fifo_suffix_standard_queue(self):
        self.assertEqual(strip_fifo_suffix("my-queue"), "my-queue")

    def test_strip_fifo_suffix_fifo_queue(self):
        self.assertEqual(strip_fifo_suffix("my-queue.fifo"), "my-queue")

    def test_strip_fifo_suffix_no_double_strip(self):
        self.assertEqual(
            strip_fifo_suffix("my-queue.fifo.fifo"), "my-queue.fifo"
        )

    def test_get_ecs_service_name_standard_queue(self):
        self.assertEqual(get_ecs_service_name("my-queue"), "my-queue_service")

    def test_get_ecs_service_name_fifo_queue(self):
        self.assertEqual(
            get_ecs_service_name("my-queue.fifo"), "my-queue_service"
        )

    def test_get_ecs_service_name_no_double_strip(self):
        self.assertEqual(
            get_ecs_service_name("my-queue.fifo.fifo"),
            "my-queue-fifo_service",
        )

    def test_sanitize_ecs_resource_name_fifo_queue(self):
        self.assertEqual(
            sanitize_ecs_resource_name("my-queue.fifo"),
            "my-queue",
        )

    def test_sanitize_ecs_resource_name_removes_other_invalid_chars(self):
        self.assertEqual(
            sanitize_ecs_resource_name("my.queue_name.fifo"),
            "my-queue_name",
        )

    @patch.dict(
        "os.environ", {"CELERY_QUEUE_NAME": "evalai-celery"}, clear=False
    )
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.task_definition")
    def test_build_task_definition_dict_fifo_queue_uses_ecs_safe_family(
        self, mock_task_definition, mock_get_aws_credentials
    ):
        challenge = MagicMock(
            pk=2698,
            is_docker_based=False,
            worker_cpu_cores=1024,
            worker_memory=2048,
            ephemeral_storage=21,
        )
        mock_get_aws_credentials.return_value = {}
        mock_task_definition.format.return_value = "{'family': 'ecs-safe'}"

        with patch(
            "challenges.aws_utils.load_aws_api_kwargs",
            side_effect=lambda value: {"family": "ecs-safe"},
        ):
            task_def, error = build_task_definition_dict(
                challenge, "mars2-challenge-2698-production-abc.fifo"
            )

        self.assertIsNone(error)
        self.assertEqual(task_def["family"], "ecs-safe")
        format_kwargs = mock_task_definition.format.call_args.kwargs
        self.assertEqual(
            format_kwargs["queue_name"],
            "mars2-challenge-2698-production-abc",
        )
        self.assertEqual(
            format_kwargs["sqs_queue_name"],
            "mars2-challenge-2698-production-abc.fifo",
        )
        self.assertEqual(
            format_kwargs["container_name"],
            "worker_mars2-challenge-2698-production-abc",
        )

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "prod")
    def test_get_evalai_submission_worker_ecr_prefixes_includes_legacy_env(
        self,
    ):
        prefixes = get_evalai_submission_worker_ecr_prefixes()
        production_prefix = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-worker-py"
        )
        legacy_prefix = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-prod-worker-py"
        )
        self.assertIn(production_prefix, prefixes)
        self.assertIn(legacy_prefix, prefixes)

    @patch("challenges.aws_utils.ENV", "prod")
    @patch.dict("os.environ", {"ECR_ENV": "custom-env"}, clear=False)
    def test_get_current_ecr_env_honors_override(self):
        self.assertEqual(get_current_ecr_env(), "custom-env")

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "prod")
    def test_get_evalai_code_upload_worker_ecr_image_maps_settings_prod_env(
        self,
    ):
        image = get_evalai_code_upload_worker_ecr_image(commit_id="abc123")
        expected_image = (
            "123456789012.dkr.ecr.us-east-1.amazonaws.com/"
            "evalai-production-code-upload-worker:abc123"
        )
        self.assertEqual(image, expected_image)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.get_image_settings_for_challenge")
    def test_refresh_task_definition_register_failure_preserves_arn(
        self,
        mock_get_image_settings,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        challenge = MagicMock(
            pk=11,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_get_image_settings.return_value = {"WORKER_IMAGE": "image:tag"}
        mock_build_task_definition.return_value = (
            {"family": "queue"},
            None,
        )
        mock_client.register_task_definition.side_effect = ClientError(
            {"Error": {"Message": "register failed"}},
            "RegisterTaskDefinition",
        )

        response = refresh_task_definition_for_challenge(
            challenge, client=mock_client
        )

        self.assertEqual(response["Error"]["Message"], "register failed")
        self.assertEqual(challenge.task_def_arn, "arn:aws:ecs:task-def/old:1")
        challenge.save.assert_not_called()
        mock_client.deregister_task_definition.assert_not_called()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.get_image_settings_for_challenge")
    def test_refresh_task_definition_register_non_ok_response(
        self,
        mock_get_image_settings,
        mock_build_task_definition,
        mock_get_boto3_client,
    ):
        challenge = MagicMock(
            pk=12,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_get_image_settings.return_value = {"WORKER_IMAGE": "image:tag"}
        mock_build_task_definition.return_value = (
            {"family": "queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "register rejected",
        }

        response = refresh_task_definition_for_challenge(
            challenge, client=mock_client
        )

        self.assertEqual(response["Error"], "register rejected")
        challenge.save.assert_not_called()
        mock_client.deregister_task_definition.assert_not_called()

    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.build_task_definition_dict")
    @patch("challenges.aws_utils.get_image_settings_for_challenge")
    def test_refresh_task_definition_deregister_non_ok_http(
        self,
        mock_get_image_settings,
        mock_build_task_definition,
        mock_get_boto3_client,
        mock_logger,
    ):
        challenge = MagicMock(
            pk=13,
            uses_ec2_worker=False,
            remote_evaluation=False,
            task_def_arn="arn:aws:ecs:task-def/old:1",
            workers=0,
        )
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_get_image_settings.return_value = {"WORKER_IMAGE": "image:tag"}
        mock_build_task_definition.return_value = (
            {"family": "queue"},
            None,
        )
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {
                "taskDefinitionArn": "arn:aws:ecs:task-def/new:2"
            },
        }
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "deregister rejected",
        }

        response = refresh_task_definition_for_challenge(
            challenge, client=mock_client
        )

        self.assertEqual(
            response["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK
        )
        mock_logger.warning.assert_called_once()

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.logger")
    @patch("challenges.aws_utils.get_boto3_client")
    def test_scale_resources_deregister_non_ok_http(
        self, mock_get_boto3_client, mock_logger, mock_settings
    ):
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.register_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK},
            "taskDefinition": {"taskDefinitionArn": "new_task_def_arn"},
        }
        mock_client.update_service.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }
        mock_client.deregister_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "deregister rejected",
        }

        challenge = MagicMock()
        challenge.task_def_arn = "some_task_def_arn"
        challenge.worker_cpu_cores = 2
        challenge.worker_memory = 4096
        challenge.queue = "test_queue"
        challenge.workers = 1

        with patch(
            "challenges.aws_utils.get_image_settings_for_challenge"
        ) as mock_get_image_settings, patch(
            "challenges.aws_utils.build_task_definition_dict"
        ) as mock_build_task_definition:
            mock_get_image_settings.return_value = {}
            mock_build_task_definition.return_value = (
                {"some_key": "some_value"},
                None,
            )

            result = scale_resources(
                challenge, worker_cpu_cores=4, worker_memory=8192
            )

        self.assertEqual(
            result["ResponseMetadata"]["HTTPStatusCode"], HTTPStatus.OK
        )
        mock_logger.warning.assert_called_once()

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.refresh_task_definition_for_challenge")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_refresh_worker_task_definitions_failure_without_error_message(
        self,
        mock_settings,
        mock_refresh_task_definition,
        mock_get_boto3_client,
    ):
        mock_refresh_task_definition.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
        }
        challenge = MagicMock(pk=14)
        response = refresh_worker_task_definitions(queryset=[challenge])
        self.assertEqual(response["count"], 0)
        self.assertEqual(
            response["failures"][0]["message"],
            "Failed to refresh worker task definition.",
        )

    def test_update_evalai_worker_image_tag_no_op_without_commit_id(self):
        image_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/repo:old"
        self.assertEqual(
            update_evalai_worker_image_tag(image_url, None), image_url
        )
        self.assertEqual(update_evalai_worker_image_tag("", "abc123"), "")

    def test_update_evalai_worker_image_tag_no_op_without_tag_separator(self):
        image_url = "123456789012.dkr.ecr.us-east-1.amazonaws.com/repo"
        self.assertEqual(
            update_evalai_worker_image_tag(image_url, "abc123"), image_url
        )

    def test_is_evalai_managed_submission_worker_image_rejects_empty_url(self):
        self.assertFalse(is_evalai_managed_submission_worker_image(None))
        self.assertFalse(is_evalai_managed_submission_worker_image(""))

    @patch.dict(
        "challenges.aws_utils.aws_keys",
        {
            "AWS_ACCOUNT_ID": "123456789012",
            "AWS_REGION": "us-east-1",
        },
        clear=False,
    )
    @patch("challenges.aws_utils.ENV", "production")
    def test_get_evalai_submission_worker_ecr_prefixes_without_legacy_env(
        self,
    ):
        prefixes = get_evalai_submission_worker_ecr_prefixes()
        self.assertEqual(len(prefixes), 1)
        self.assertIn(
            "evalai-production-worker-py",
            next(iter(prefixes)),
        )


class TestValidateEKSNodegroupConfig(unittest.TestCase):
    """
    The validation gate runs before the old nodegroup is deleted, so a false
    negative here destroys a challenge's capacity.
    """

    def setUp(self):
        self.challenge = MagicMock()
        self.challenge.pk = 1
        self.challenge.worker_instance_type = "g5.xlarge"
        self.challenge.worker_ami_type = "AL2023_x86_64_NVIDIA"
        self.challenge.worker_disk_size = 100
        self.challenge.cpu_only_jobs = False
        self.challenge.min_worker_instance = 0
        self.challenge.max_worker_instance = 4
        self.challenge.desired_worker_instance = 1

        self.eks_client = MagicMock()
        self.eks_client.describe_cluster.return_value = {
            "cluster": {"version": "1.36"}
        }

        self.ec2_client = MagicMock()
        self.ec2_client.describe_instance_type_offerings.return_value = {
            "InstanceTypeOfferings": [{"InstanceType": "g5.xlarge"}]
        }

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_valid_config_returns_no_errors(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.ec2_client

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(errors, [])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_instance_type_not_offered_in_region(
        self, mock_credentials, mock_get_boto3_client
    ):
        self.ec2_client.describe_instance_type_offerings.return_value = {
            "InstanceTypeOfferings": []
        }
        mock_get_boto3_client.return_value = self.ec2_client

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("not offered in this region", errors[0])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_unknown_ami_type_rejected(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.ec2_client
        self.challenge.worker_ami_type = "NOT_A_REAL_AMI"

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Unknown worker_ami_type", errors[0])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_al2_ami_rejected_on_modern_kubernetes(
        self, mock_credentials, mock_get_boto3_client
    ):
        """
        AL2 AMIs no longer exist on Kubernetes 1.33+, so create_nodegroup would
        fail after the old nodegroup had already been deleted.
        """
        mock_get_boto3_client.return_value = self.ec2_client
        self.challenge.worker_ami_type = "AL2_x86_64_GPU"

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("not available on Kubernetes 1.36", errors[0])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_al2_ami_allowed_on_old_kubernetes(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.ec2_client
        self.challenge.worker_ami_type = "AL2_x86_64_GPU"
        self.eks_client.describe_cluster.return_value = {
            "cluster": {"version": "1.29"}
        }

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(errors, [])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_gpu_challenge_on_non_gpu_ami_rejected(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.ec2_client
        self.challenge.worker_ami_type = "AL2023_x86_64_STANDARD"

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("has no GPU driver", errors[0])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_cpu_only_challenge_on_non_gpu_ami_allowed(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.ec2_client
        self.challenge.worker_ami_type = "AL2023_x86_64_STANDARD"
        self.challenge.cpu_only_jobs = True

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(errors, [])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_invalid_disk_size_rejected(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.ec2_client
        self.challenge.worker_disk_size = 0

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("worker_disk_size", errors[0])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_empty_instance_type_rejected(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.ec2_client
        self.challenge.worker_instance_type = None

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("worker_instance_type is empty", errors[0])


class TestValidateEKSNodegroupConfigErrors(unittest.TestCase):
    """AWS lookups inside validation must degrade to an error, not an abort."""

    def setUp(self):
        self.challenge = MagicMock()
        self.challenge.pk = 1
        self.challenge.worker_instance_type = "g5.xlarge"
        self.challenge.worker_ami_type = "AL2023_x86_64_NVIDIA"
        self.challenge.worker_disk_size = 100
        self.challenge.cpu_only_jobs = False
        self.challenge.min_worker_instance = 0
        self.challenge.max_worker_instance = 4
        self.challenge.desired_worker_instance = 1
        self.eks_client = MagicMock()
        self.eks_client.describe_cluster.return_value = {
            "cluster": {"version": "1.36"}
        }
        self.ec2_client = MagicMock()
        self.ec2_client.describe_instance_type_offerings.return_value = {
            "InstanceTypeOfferings": [{"InstanceType": "g5.xlarge"}]
        }

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_instance_type_lookup_failure_is_an_error(
        self, mock_credentials, mock_get_boto3_client
    ):
        self.ec2_client.describe_instance_type_offerings.side_effect = (
            ClientError(
                {"Error": {"Code": "AccessDenied", "Message": "no"}},
                "DescribeInstanceTypeOfferings",
            )
        )
        mock_get_boto3_client.return_value = self.ec2_client

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Could not verify instance type", errors[0])

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_cluster_version_lookup_failure_is_an_error(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.ec2_client
        self.eks_client.describe_cluster.return_value = {}

        errors = validate_eks_nodegroup_config(
            self.challenge, self.eks_client, "test-cluster"
        )

        self.assertEqual(len(errors), 1)
        self.assertIn("Could not read cluster version", errors[0])


class TestValidateNodegroupScaling(unittest.TestCase):
    """
    Scaling bounds are sent to CreateNodegroup after the live nodegroup has
    already been deleted, so an invalid combination must be caught up front.
    """

    def setUp(self):
        self.challenge = MagicMock()
        self.challenge.pk = 1
        self.challenge.worker_instance_type = "g5.xlarge"
        self.challenge.worker_ami_type = "AL2023_x86_64_NVIDIA"
        self.challenge.worker_disk_size = 100
        self.challenge.cpu_only_jobs = False
        self.challenge.min_worker_instance = 0
        self.challenge.max_worker_instance = 4
        self.challenge.desired_worker_instance = 1

        self.eks_client = MagicMock()
        self.eks_client.describe_cluster.return_value = {
            "cluster": {"version": "1.36"}
        }
        self.ec2_client = MagicMock()
        self.ec2_client.describe_instance_type_offerings.return_value = {
            "InstanceTypeOfferings": [{"InstanceType": "g5.xlarge"}]
        }

    def _validate(self):
        with patch(
            "challenges.aws_utils.get_boto3_client",
            return_value=self.ec2_client,
        ), patch("challenges.utils.get_aws_credentials_for_challenge"):
            return validate_eks_nodegroup_config(
                self.challenge, self.eks_client, "test-cluster"
            )

    def test_valid_bounds_pass(self):
        self.assertEqual(self._validate(), [])

    def test_min_above_max_is_rejected(self):
        self.challenge.min_worker_instance = 5

        errors = self._validate()

        self.assertTrue(
            any("cannot exceed max_worker_instance" in e for e in errors)
        )

    def test_desired_outside_bounds_is_rejected(self):
        self.challenge.desired_worker_instance = 9

        errors = self._validate()

        self.assertTrue(any("must be between" in e for e in errors))

    def test_zero_max_is_rejected(self):
        self.challenge.max_worker_instance = 0
        self.challenge.desired_worker_instance = 0

        errors = self._validate()

        self.assertTrue(
            any("max_worker_instance must be at least 1" in e for e in errors)
        )

    def test_null_scaling_field_is_rejected(self):
        """All three fields are nullable on the model."""
        self.challenge.desired_worker_instance = None

        errors = self._validate()

        self.assertTrue(
            any(
                "desired_worker_instance must be a non-negative integer" in e
                for e in errors
            )
        )

    def test_negative_scaling_field_is_rejected(self):
        self.challenge.min_worker_instance = -1

        errors = self._validate()

        self.assertTrue(
            any(
                "min_worker_instance must be a non-negative integer" in e
                for e in errors
            )
        )

    def test_boolean_is_not_accepted_as_an_integer(self):
        self.challenge.max_worker_instance = True

        errors = self._validate()

        self.assertTrue(
            any(
                "max_worker_instance must be a non-negative integer" in e
                for e in errors
            )
        )


class TestRecreateEKSNodegroup(unittest.TestCase):
    def setUp(self):
        self.challenge = MagicMock()
        self.challenge.pk = 1
        self.challenge.title = "Test Challenge"

        self.cluster = MagicMock()
        self.cluster.name = "test-cluster"
        self.cluster.nodegroup_name = "test-nodegroup"

        self.client = MagicMock()

    def _patch_lookup(self):
        self.client.describe_nodegroup.return_value = {
            "nodegroup": {"status": "ACTIVE"}
        }
        return patch(
            "challenges.aws_utils._get_challenge_cluster",
            return_value=(self.challenge, self.cluster),
        )

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.validate_eks_nodegroup_config")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_deletes_then_creates_on_valid_config(
        self,
        mock_credentials,
        mock_get_boto3_client,
        mock_validate,
        mock_create,
    ):
        mock_get_boto3_client.return_value = self.client
        mock_validate.return_value = []
        mock_create.return_value = {"nodegroup": "created"}

        with self._patch_lookup():
            result = recreate_eks_nodegroup(1)

        self.client.delete_nodegroup.assert_called_once_with(
            clusterName="test-cluster", nodegroupName="test-nodegroup"
        )
        self.client.get_waiter.assert_called_once_with("nodegroup_deleted")
        mock_create.assert_called_once_with(
            self.client, self.challenge, "test-cluster", "test-nodegroup"
        )
        self.assertIn("message", result)

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.validate_eks_nodegroup_config")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_invalid_config_leaves_nodegroup_untouched(
        self,
        mock_credentials,
        mock_get_boto3_client,
        mock_validate,
        mock_create,
    ):
        """
        A failed precheck must abort before delete_nodegroup, otherwise the
        challenge is left with no capacity at all.
        """
        mock_get_boto3_client.return_value = self.client
        mock_validate.return_value = ["Instance type bogus.type is not valid."]

        with self._patch_lookup():
            result = recreate_eks_nodegroup(1)

        self.client.delete_nodegroup.assert_not_called()
        mock_create.assert_not_called()
        self.assertIn("error", result)
        self.assertIn("left untouched", result["error"])

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.validate_eks_nodegroup_config")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_missing_nodegroup_still_creates(
        self,
        mock_credentials,
        mock_get_boto3_client,
        mock_validate,
        mock_create,
    ):
        mock_get_boto3_client.return_value = self.client
        mock_validate.return_value = []
        mock_create.return_value = {"nodegroup": "created"}
        self.client.delete_nodegroup.side_effect = ClientError(
            {
                "Error": {
                    "Code": "ResourceNotFoundException",
                    "Message": "gone",
                }
            },
            "DeleteNodegroup",
        )

        with self._patch_lookup():
            result = recreate_eks_nodegroup(1)

        mock_create.assert_called_once()
        self.assertIn("message", result)

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.validate_eks_nodegroup_config")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_delete_error_aborts_before_create(
        self,
        mock_credentials,
        mock_get_boto3_client,
        mock_validate,
        mock_create,
    ):
        mock_get_boto3_client.return_value = self.client
        mock_validate.return_value = []
        self.client.delete_nodegroup.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "nope"}},
            "DeleteNodegroup",
        )

        with self._patch_lookup():
            result = recreate_eks_nodegroup(1)

        mock_create.assert_not_called()
        self.assertIn("error", result)

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.validate_eks_nodegroup_config")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_failed_create_reports_lost_capacity(
        self,
        mock_credentials,
        mock_get_boto3_client,
        mock_validate,
        mock_create,
    ):
        mock_get_boto3_client.return_value = self.client
        mock_validate.return_value = []
        mock_create.return_value = None

        with self._patch_lookup():
            result = recreate_eks_nodegroup(1)

        self.assertIn("error", result)
        self.assertIn("no worker capacity", result["error"])

    @patch("challenges.aws_utils.get_boto3_client")
    def test_no_cluster_is_a_noop(self, mock_get_boto3_client):
        with patch(
            "challenges.aws_utils._get_challenge_cluster",
            return_value=(None, None),
        ):
            result = recreate_eks_nodegroup(1)

        mock_get_boto3_client.assert_not_called()
        self.assertIn("error", result)

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.validate_eks_nodegroup_config")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_non_active_nodegroup_is_retried_not_dropped(
        self,
        mock_credentials,
        mock_get_boto3_client,
        mock_validate,
        mock_create,
    ):
        """
        A CREATING nodegroup means setup_eks_cluster is still in flight.
        Deleting it would make create_eks_nodegroup fail on a duplicate name
        and never start the code-upload worker. Abandoning the task instead
        would lose the edit for good, because the callback has already
        refreshed its snapshots, so the task must retry.
        """
        mock_get_boto3_client.return_value = self.client
        mock_validate.return_value = []

        with self._patch_lookup(), patch.object(
            recreate_eks_nodegroup, "retry"
        ) as mock_retry:
            self.client.describe_nodegroup.return_value = {
                "nodegroup": {"status": "CREATING"}
            }
            result = recreate_eks_nodegroup(1)

        mock_retry.assert_called_once_with(
            countdown=settings.EKS_NODEGROUP_SYNC_RETRY_SECONDS
        )
        self.assertEqual(
            recreate_eks_nodegroup.max_retries,
            settings.EKS_NODEGROUP_SYNC_MAX_RETRIES,
        )
        self.client.delete_nodegroup.assert_not_called()
        mock_create.assert_not_called()
        self.assertIn("error", result)
        self.assertIn("not ACTIVE", result["error"])

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.validate_eks_nodegroup_config")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_exhausted_retries_do_not_touch_the_nodegroup(
        self,
        mock_credentials,
        mock_get_boto3_client,
        mock_validate,
        mock_create,
    ):
        mock_get_boto3_client.return_value = self.client
        mock_validate.return_value = []

        with self._patch_lookup(), patch.object(
            recreate_eks_nodegroup,
            "retry",
            side_effect=MaxRetriesExceededError,
        ), patch("challenges.aws_utils.logger") as mock_logger:
            self.client.describe_nodegroup.return_value = {
                "nodegroup": {"status": "CREATING"}
            }
            result = recreate_eks_nodegroup(1)

        self.client.delete_nodegroup.assert_not_called()
        mock_create.assert_not_called()
        self.assertIn("error", result)
        # The edit is lost at this point, so the log must say how to recover.
        self.assertIn(
            "Recreate EKS nodegroup", mock_logger.error.call_args.args[0]
        )

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_describe_error_aborts_before_delete(
        self, mock_credentials, mock_get_boto3_client, mock_create
    ):
        mock_get_boto3_client.return_value = self.client

        with self._patch_lookup():
            self.client.describe_nodegroup.side_effect = ClientError(
                {"Error": {"Code": "AccessDeniedException", "Message": "no"}},
                "DescribeNodegroup",
            )
            result = recreate_eks_nodegroup(1)

        self.client.delete_nodegroup.assert_not_called()
        mock_create.assert_not_called()
        self.assertIn("error", result)

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_malformed_describe_response_aborts_before_delete(
        self, mock_credentials, mock_get_boto3_client, mock_create
    ):
        mock_get_boto3_client.return_value = self.client

        with self._patch_lookup():
            # Resolution succeeds, then the status lookup comes back without
            # the key the task needs.
            self.client.describe_nodegroup.side_effect = [
                {"nodegroup": {"status": "ACTIVE"}},
                {"nodegroup": {}},
            ]
            result = recreate_eks_nodegroup(1)

        self.client.delete_nodegroup.assert_not_called()
        mock_create.assert_not_called()
        self.assertIn("error", result)

    @patch("challenges.aws_utils._resolve_nodegroup_name", return_value=None)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_unresolvable_nodegroup_is_a_noop(
        self, mock_credentials, mock_get_boto3_client, mock_resolve
    ):
        mock_get_boto3_client.return_value = self.client

        with self._patch_lookup():
            result = recreate_eks_nodegroup(1)

        self.client.delete_nodegroup.assert_not_called()
        self.assertIn("error", result)

    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.validate_eks_nodegroup_config")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_delete_waiter_timeout_aborts_before_create(
        self,
        mock_credentials,
        mock_get_boto3_client,
        mock_validate,
        mock_create,
    ):
        """Creating over a half-deleted nodegroup would fail."""
        mock_get_boto3_client.return_value = self.client
        mock_validate.return_value = []

        with self._patch_lookup():
            self.client.get_waiter.return_value.wait.side_effect = WaiterError(
                name="nodegroup_deleted",
                reason="max attempts exceeded",
                last_response={},
            )
            result = recreate_eks_nodegroup(1)

        mock_create.assert_not_called()
        self.assertIn("error", result)


class TestCreateNodegroupForChallenge(unittest.TestCase):
    @patch("challenges.models.ChallengeEvaluationCluster")
    @patch("challenges.aws_utils.get_code_upload_setup_meta_for_challenge")
    def test_active_waiter_failure_still_reports_the_nodegroup(
        self, mock_meta, mock_evaluation_cluster
    ):
        """
        The nodegroup exists once create_nodegroup succeeds. Returning None on
        a waiter timeout would make callers report it as missing, and the next
        recreate would delete a nodegroup that was merely still CREATING.

        WaiterError must also not escape, or the caller's error handling and
        the code-upload worker start in create_eks_nodegroup are both skipped.
        """
        mock_meta.return_value = {
            "SUBNET_1": "subnet-123",
            "SUBNET_2": "subnet-456",
            "EKS_NODEGROUP_ROLE_ARN": "arn:aws:iam::123456789012:role/ng",
        }
        challenge = MagicMock()
        challenge.pk = 1
        client = MagicMock()
        client.create_nodegroup.return_value = {"nodegroup": "created"}
        client.get_waiter.return_value.wait.side_effect = WaiterError(
            name="nodegroup_active",
            reason="max attempts exceeded",
            last_response={},
        )

        result = create_nodegroup_for_challenge(
            client, challenge, "test-cluster", "test-nodegroup"
        )

        self.assertEqual(result, {"nodegroup": "created"})

    @patch("challenges.models.ChallengeEvaluationCluster")
    @patch("challenges.aws_utils.get_code_upload_setup_meta_for_challenge")
    def test_create_failure_returns_none(
        self, mock_meta, mock_evaluation_cluster
    ):
        mock_meta.return_value = {
            "SUBNET_1": "subnet-123",
            "SUBNET_2": "subnet-456",
            "EKS_NODEGROUP_ROLE_ARN": "arn:aws:iam::123456789012:role/ng",
        }
        challenge = MagicMock()
        challenge.pk = 1
        client = MagicMock()
        client.create_nodegroup.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterException", "Message": "bad"}},
            "CreateNodegroup",
        )

        result = create_nodegroup_for_challenge(
            client, challenge, "test-cluster", "test-nodegroup"
        )

        self.assertIsNone(result)


class TestCreateEKSNodegroupReadsCurrentConfig(unittest.TestCase):
    """
    Cluster setup takes many minutes, and the chain carries a challenge
    serialized at approval time. An edit landing in that window cannot be
    applied by the post_save hook, because there is no nodegroup to recreate
    yet, so the create must read the current row instead of the snapshot.
    """

    @patch("challenges.aws_utils.create_service_by_challenge_pk")
    @patch("challenges.aws_utils.client_token_generator")
    @patch("challenges.aws_utils.construct_and_send_eks_cluster_creation_mail")
    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.models.Challenge")
    def test_uses_database_row_not_serialized_snapshot(
        self,
        mock_challenge_model,
        mock_deserialize,
        mock_credentials,
        mock_get_boto3_client,
        mock_create,
        mock_mail,
        mock_token,
        mock_service,
    ):
        stale = MagicMock()
        stale.pk = 1
        stale.title = "Test Challenge"
        stale.worker_instance_type = "g5.4xlarge"
        mock_deserialize.return_value = [MagicMock(object=stale)]

        current = MagicMock()
        current.pk = 1
        current.title = "Test Challenge"
        current.worker_instance_type = "g5.xlarge"
        mock_challenge_model.DoesNotExist = Challenge.DoesNotExist
        mock_challenge_model.objects.get.return_value = current
        mock_create.return_value = {"nodegroup": "created"}

        create_eks_nodegroup("[]", "test-cluster")

        mock_challenge_model.objects.get.assert_called_once_with(pk=1)
        self.assertIs(mock_create.call_args.args[1], current)

    @patch("challenges.aws_utils.create_service_by_challenge_pk")
    @patch("challenges.aws_utils.client_token_generator")
    @patch("challenges.aws_utils.construct_and_send_eks_cluster_creation_mail")
    @patch("challenges.aws_utils.create_nodegroup_for_challenge")
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    @patch("challenges.aws_utils.serializers.deserialize")
    @patch("challenges.models.Challenge")
    def test_falls_back_to_snapshot_when_row_is_gone(
        self,
        mock_challenge_model,
        mock_deserialize,
        mock_credentials,
        mock_get_boto3_client,
        mock_create,
        mock_mail,
        mock_token,
        mock_service,
    ):
        stale = MagicMock()
        stale.pk = 1
        stale.title = "Test Challenge"
        mock_deserialize.return_value = [MagicMock(object=stale)]
        mock_challenge_model.DoesNotExist = Challenge.DoesNotExist
        mock_challenge_model.objects.get.side_effect = Challenge.DoesNotExist
        mock_create.return_value = {"nodegroup": "created"}

        create_eks_nodegroup("[]", "test-cluster")

        self.assertIs(mock_create.call_args.args[1], stale)


class TestUpdateEKSNodegroupScaling(unittest.TestCase):
    def setUp(self):
        self.challenge = MagicMock()
        self.challenge.pk = 1
        self.challenge.min_worker_instance = 0
        self.challenge.max_worker_instance = 4
        self.challenge.desired_worker_instance = 0

        self.cluster = MagicMock()
        self.cluster.name = "test-cluster"
        self.cluster.nodegroup_name = "test-nodegroup"

        self.client = MagicMock()
        self.client.describe_nodegroup.return_value = {
            "nodegroup": {
                "status": "ACTIVE",
                "scalingConfig": {
                    "minSize": 1,
                    "maxSize": 2,
                    "desiredSize": 2,
                },
            }
        }

    def _patch_lookup(self):
        return patch(
            "challenges.aws_utils._get_challenge_cluster",
            return_value=(self.challenge, self.cluster),
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_pushes_bounds_and_preserves_live_desired_size(
        self, mock_credentials, mock_get_boto3_client
    ):
        """
        The autoscale Lambda owns desiredSize. Pushing the challenge's stored
        value would shrink a busy nodegroup and kill running submissions.
        """
        mock_get_boto3_client.return_value = self.client

        with self._patch_lookup():
            result = update_eks_nodegroup_scaling(1)

        self.client.update_nodegroup_config.assert_called_once_with(
            clusterName="test-cluster",
            nodegroupName="test-nodegroup",
            scalingConfig={"minSize": 0, "maxSize": 4, "desiredSize": 2},
        )
        self.assertIn("message", result)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_live_desired_size_clamped_into_new_bounds(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.client
        self.client.describe_nodegroup.return_value = {
            "nodegroup": {
                "status": "ACTIVE",
                "scalingConfig": {"desiredSize": 9},
            }
        }

        with self._patch_lookup():
            update_eks_nodegroup_scaling(1)

        sent = self.client.update_nodegroup_config.call_args.kwargs
        self.assertEqual(sent["scalingConfig"]["desiredSize"], 4)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_live_desired_size_raised_to_new_minimum(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.client
        self.challenge.min_worker_instance = 3

        with self._patch_lookup():
            update_eks_nodegroup_scaling(1)

        sent = self.client.update_nodegroup_config.call_args.kwargs
        self.assertEqual(sent["scalingConfig"]["desiredSize"], 3)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_non_active_nodegroup_is_retried(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.client
        self.client.describe_nodegroup.return_value = {
            "nodegroup": {
                "status": "CREATING",
                "scalingConfig": {"desiredSize": 1},
            }
        }

        with self._patch_lookup(), patch.object(
            update_eks_nodegroup_scaling, "retry"
        ) as mock_retry:
            result = update_eks_nodegroup_scaling(1)

        mock_retry.assert_called_once_with(
            countdown=settings.EKS_NODEGROUP_SYNC_RETRY_SECONDS
        )
        self.assertEqual(
            update_eks_nodegroup_scaling.max_retries,
            settings.EKS_NODEGROUP_SYNC_MAX_RETRIES,
        )
        self.client.update_nodegroup_config.assert_not_called()
        self.assertIn("error", result)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_exhausted_retries_skip_the_update(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.client
        self.client.describe_nodegroup.return_value = {
            "nodegroup": {
                "status": "CREATING",
                "scalingConfig": {"desiredSize": 1},
            }
        }

        with self._patch_lookup(), patch.object(
            update_eks_nodegroup_scaling,
            "retry",
            side_effect=MaxRetriesExceededError,
        ), patch("challenges.aws_utils.logger") as mock_logger:
            result = update_eks_nodegroup_scaling(1)

        self.client.update_nodegroup_config.assert_not_called()
        self.assertIn("error", result)
        self.assertIn(
            "Recreate EKS nodegroup", mock_logger.error.call_args.args[0]
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_describe_error_is_reported(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.client
        # The first call resolves the nodegroup name; the task's own lookup is
        # the second one.
        self.client.describe_nodegroup.side_effect = [
            {"nodegroup": {"status": "ACTIVE"}},
            ClientError(
                {"Error": {"Code": "AccessDeniedException", "Message": "no"}},
                "DescribeNodegroup",
            ),
        ]

        with self._patch_lookup():
            result = update_eks_nodegroup_scaling(1)

        self.client.update_nodegroup_config.assert_not_called()
        self.assertIn("error", result)

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_client_error_is_reported(
        self, mock_credentials, mock_get_boto3_client
    ):
        mock_get_boto3_client.return_value = self.client
        self.client.update_nodegroup_config.side_effect = ClientError(
            {"Error": {"Code": "InvalidParameterException", "Message": "bad"}},
            "UpdateNodegroupConfig",
        )

        with self._patch_lookup():
            result = update_eks_nodegroup_scaling(1)

        self.assertIn("error", result)

    @patch("challenges.aws_utils.get_boto3_client")
    def test_no_cluster_is_a_noop(self, mock_get_boto3_client):
        with patch(
            "challenges.aws_utils._get_challenge_cluster",
            return_value=(None, None),
        ):
            result = update_eks_nodegroup_scaling(1)

        mock_get_boto3_client.assert_not_called()
        self.assertIn("error", result)

    @patch("challenges.aws_utils._resolve_nodegroup_name", return_value=None)
    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_unresolvable_nodegroup_is_a_noop(
        self, mock_credentials, mock_get_boto3_client, mock_resolve
    ):
        mock_get_boto3_client.return_value = self.client

        with self._patch_lookup():
            result = update_eks_nodegroup_scaling(1)

        self.client.update_nodegroup_config.assert_not_called()
        self.assertIn("error", result)


class TestGetChallengeCluster(unittest.TestCase):
    @patch("challenges.models.ChallengeEvaluationCluster")
    def test_missing_cluster_returns_nothing(self, mock_cluster):
        mock_cluster.DoesNotExist = ChallengeEvaluationCluster.DoesNotExist
        mock_cluster.objects.select_related.return_value.get.side_effect = (
            ChallengeEvaluationCluster.DoesNotExist
        )

        self.assertEqual(_get_challenge_cluster(1), (None, None))

    @patch("challenges.models.ChallengeEvaluationCluster")
    def test_database_error_returns_nothing(self, mock_cluster):
        mock_cluster.DoesNotExist = ChallengeEvaluationCluster.DoesNotExist
        mock_cluster.objects.select_related.return_value.get.side_effect = (
            DatabaseError("connection lost")
        )

        self.assertEqual(_get_challenge_cluster(1), (None, None))

    @patch("challenges.models.ChallengeEvaluationCluster")
    def test_returns_challenge_and_cluster(self, mock_cluster):
        cluster = MagicMock()
        mock_cluster.DoesNotExist = ChallengeEvaluationCluster.DoesNotExist
        mock_cluster.objects.select_related.return_value.get.return_value = (
            cluster
        )

        self.assertEqual(
            _get_challenge_cluster(1), (cluster.challenge, cluster)
        )


class TestVersionAtLeast(unittest.TestCase):
    def test_compares_dotted_versions(self):
        self.assertTrue(_version_at_least("1.36", "1.33"))
        self.assertTrue(_version_at_least("1.33", "1.33"))
        self.assertFalse(_version_at_least("1.29", "1.33"))

    def test_unparseable_version_is_not_at_least(self):
        """
        An unreadable cluster version must not be treated as modern, or a valid
        AL2 nodegroup would be rejected on an old cluster.
        """
        self.assertFalse(_version_at_least("unknown", "1.33"))
        self.assertFalse(_version_at_least(None, "1.33"))


class TestResolveNodegroupName(unittest.TestCase):
    """
    The name must never be re-derived from the challenge title: a renamed
    challenge would derive a name matching nothing, delete nothing, and then
    create a second nodegroup beside the live one.
    """

    def setUp(self):
        self.cluster = MagicMock()
        self.cluster.name = "test-cluster"
        self.cluster.nodegroup_name = None
        self.client = MagicMock()

    @patch("challenges.models.ChallengeEvaluationCluster")
    def test_single_nodegroup_is_resolved_and_recorded(self, mock_cluster):
        self.client.list_nodegroups.return_value = {
            "nodegroups": ["live-nodegroup"]
        }

        name = _resolve_nodegroup_name(self.client, 1, self.cluster)

        self.assertEqual(name, "live-nodegroup")
        mock_cluster.objects.filter.return_value.update.assert_called_once_with(
            nodegroup_name="live-nodegroup"
        )

    @patch("challenges.models.ChallengeEvaluationCluster")
    def test_stale_recorded_name_is_re_resolved(self, mock_cluster):
        """
        A nodegroup replaced by hand leaves the recorded name pointing at
        nothing. Trusting it would break every sync until the row was edited.
        """
        self.cluster.nodegroup_name = "stale-nodegroup"
        self.client.describe_nodegroup.side_effect = ClientError(
            {"Error": {"Code": "ResourceNotFoundException", "Message": "no"}},
            "DescribeNodegroup",
        )
        self.client.list_nodegroups.return_value = {
            "nodegroups": ["live-nodegroup"]
        }

        name = _resolve_nodegroup_name(self.client, 1, self.cluster)

        self.assertEqual(name, "live-nodegroup")
        mock_cluster.objects.filter.return_value.update.assert_called_once_with(
            nodegroup_name="live-nodegroup"
        )

    def test_recorded_name_is_verified_before_use(self):
        self.cluster.nodegroup_name = "recorded-nodegroup"

        name = _resolve_nodegroup_name(self.client, 1, self.cluster)

        self.assertEqual(name, "recorded-nodegroup")
        self.client.describe_nodegroup.assert_called_once_with(
            clusterName="test-cluster", nodegroupName="recorded-nodegroup"
        )
        self.client.list_nodegroups.assert_not_called()

    def test_describe_boto_error_returns_none(self):
        self.cluster.nodegroup_name = "recorded-nodegroup"
        self.client.describe_nodegroup.side_effect = WaiterError(
            name="describe", reason="connection reset", last_response={}
        )

        self.assertIsNone(
            _resolve_nodegroup_name(self.client, 1, self.cluster)
        )
        self.client.list_nodegroups.assert_not_called()

    def test_describe_error_other_than_missing_returns_none(self):
        self.cluster.nodegroup_name = "recorded-nodegroup"
        self.client.describe_nodegroup.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "no"}},
            "DescribeNodegroup",
        )

        self.assertIsNone(
            _resolve_nodegroup_name(self.client, 1, self.cluster)
        )
        self.client.list_nodegroups.assert_not_called()

    def test_no_nodegroup_returns_none(self):
        """Also the state during initial setup, before the nodegroup exists."""
        self.client.list_nodegroups.return_value = {"nodegroups": []}

        self.assertIsNone(
            _resolve_nodegroup_name(self.client, 1, self.cluster)
        )

    def test_multiple_nodegroups_refuses_to_guess(self):
        self.client.list_nodegroups.return_value = {
            "nodegroups": ["one", "two"]
        }

        self.assertIsNone(
            _resolve_nodegroup_name(self.client, 1, self.cluster)
        )

    @patch("challenges.models.ChallengeEvaluationCluster")
    def test_recording_failure_still_returns_name(self, mock_cluster):
        """Persisting the name is a convenience; the recreate must go ahead."""
        self.client.list_nodegroups.return_value = {
            "nodegroups": ["live-nodegroup"]
        }
        mock_cluster.objects.filter.return_value.update.side_effect = (
            DatabaseError("connection lost")
        )

        name = _resolve_nodegroup_name(self.client, 1, self.cluster)

        self.assertEqual(name, "live-nodegroup")

    def test_list_error_returns_none(self):
        self.client.list_nodegroups.side_effect = ClientError(
            {"Error": {"Code": "AccessDeniedException", "Message": "no"}},
            "ListNodegroups",
        )

        self.assertIsNone(
            _resolve_nodegroup_name(self.client, 1, self.cluster)
        )


class TestEKSNodegroupConfigChangeCallback(unittest.TestCase):
    def setUp(self):
        self.challenge = MagicMock()
        self.challenge.pk = 1
        self.challenge.is_docker_based = True
        self.challenge.remote_evaluation = False
        # Start with every tracked field unchanged.
        for field in (
            "worker_instance_type",
            "worker_ami_type",
            "worker_disk_size",
            "min_worker_instance",
            "max_worker_instance",
            "desired_worker_instance",
        ):
            value = "unchanged-{}".format(field)
            setattr(self.challenge, field, value)
            setattr(self.challenge, "_original_{}".format(field), value)

    @patch("challenges.aws_utils.update_eks_nodegroup_scaling")
    @patch("challenges.aws_utils.recreate_eks_nodegroup")
    @patch("challenges.aws_utils.settings", DEBUG=False, TEST=False)
    def test_no_change_dispatches_nothing(
        self, mock_settings, mock_recreate, mock_scale
    ):
        mock_settings.EKS_NODEGROUP_IMMUTABLE_FIELDS = (
            "worker_instance_type",
            "worker_ami_type",
            "worker_disk_size",
        )
        mock_settings.EKS_NODEGROUP_SCALING_FIELDS = (
            "min_worker_instance",
            "max_worker_instance",
            "desired_worker_instance",
        )

        action = eks_nodegroup_config_change_callback(self.challenge)

        self.assertIsNone(action)
        mock_recreate.delay.assert_not_called()
        mock_scale.delay.assert_not_called()

    @patch("challenges.aws_utils.update_eks_nodegroup_scaling")
    @patch("challenges.aws_utils.recreate_eks_nodegroup")
    @patch("challenges.aws_utils.settings", DEBUG=False, TEST=False)
    def test_instance_type_change_triggers_recreate(
        self, mock_settings, mock_recreate, mock_scale
    ):
        mock_settings.EKS_NODEGROUP_IMMUTABLE_FIELDS = (
            "worker_instance_type",
            "worker_ami_type",
            "worker_disk_size",
        )
        mock_settings.EKS_NODEGROUP_SCALING_FIELDS = (
            "min_worker_instance",
            "max_worker_instance",
            "desired_worker_instance",
        )
        self.challenge.worker_instance_type = "g5.xlarge"

        action = eks_nodegroup_config_change_callback(self.challenge)

        self.assertEqual(action, "recreate")
        mock_recreate.delay.assert_called_once_with(1)
        mock_scale.delay.assert_not_called()
        # The snapshot is refreshed so a second save is not a second recreate.
        self.assertEqual(
            self.challenge._original_worker_instance_type, "g5.xlarge"
        )

    @patch("challenges.aws_utils.update_eks_nodegroup_scaling")
    @patch("challenges.aws_utils.recreate_eks_nodegroup")
    @patch("challenges.aws_utils.settings", DEBUG=False, TEST=False)
    def test_scaling_change_triggers_update_only(
        self, mock_settings, mock_recreate, mock_scale
    ):
        mock_settings.EKS_NODEGROUP_IMMUTABLE_FIELDS = (
            "worker_instance_type",
            "worker_ami_type",
            "worker_disk_size",
        )
        mock_settings.EKS_NODEGROUP_SCALING_FIELDS = (
            "min_worker_instance",
            "max_worker_instance",
            "desired_worker_instance",
        )
        self.challenge.max_worker_instance = 8

        action = eks_nodegroup_config_change_callback(self.challenge)

        self.assertEqual(action, "scale")
        mock_scale.delay.assert_called_once_with(1)
        mock_recreate.delay.assert_not_called()

    @patch("challenges.aws_utils.update_eks_nodegroup_scaling")
    @patch("challenges.aws_utils.recreate_eks_nodegroup")
    @patch("challenges.aws_utils.settings", DEBUG=False, TEST=False)
    def test_recreate_wins_when_both_change(
        self, mock_settings, mock_recreate, mock_scale
    ):
        """
        create_nodegroup already sends the new scalingConfig, so dispatching an
        update as well would be a redundant AWS call.
        """
        mock_settings.EKS_NODEGROUP_IMMUTABLE_FIELDS = (
            "worker_instance_type",
            "worker_ami_type",
            "worker_disk_size",
        )
        mock_settings.EKS_NODEGROUP_SCALING_FIELDS = (
            "min_worker_instance",
            "max_worker_instance",
            "desired_worker_instance",
        )
        self.challenge.worker_instance_type = "g5.xlarge"
        self.challenge.max_worker_instance = 8

        action = eks_nodegroup_config_change_callback(self.challenge)

        self.assertEqual(action, "recreate")
        mock_recreate.delay.assert_called_once_with(1)
        mock_scale.delay.assert_not_called()

    @patch("challenges.aws_utils.update_eks_nodegroup_scaling")
    @patch("challenges.aws_utils.recreate_eks_nodegroup")
    @patch("challenges.aws_utils.settings", DEBUG=False, TEST=False)
    def test_non_code_upload_challenge_ignored(
        self, mock_settings, mock_recreate, mock_scale
    ):
        mock_settings.EKS_NODEGROUP_IMMUTABLE_FIELDS = (
            "worker_instance_type",
            "worker_ami_type",
            "worker_disk_size",
        )
        mock_settings.EKS_NODEGROUP_SCALING_FIELDS = (
            "min_worker_instance",
            "max_worker_instance",
            "desired_worker_instance",
        )
        self.challenge.is_docker_based = False
        self.challenge.worker_instance_type = "g5.xlarge"

        action = eks_nodegroup_config_change_callback(self.challenge)

        self.assertIsNone(action)
        mock_recreate.delay.assert_not_called()

    @patch("challenges.aws_utils.update_eks_nodegroup_scaling")
    @patch("challenges.aws_utils.recreate_eks_nodegroup")
    @patch("challenges.aws_utils.settings", DEBUG=True, TEST=False)
    def test_debug_mode_dispatches_nothing(
        self, mock_settings, mock_recreate, mock_scale
    ):
        self.challenge.worker_instance_type = "g5.xlarge"

        action = eks_nodegroup_config_change_callback(self.challenge)

        self.assertIsNone(action)
        mock_recreate.delay.assert_not_called()
        mock_scale.delay.assert_not_called()

    @patch("challenges.aws_utils.update_eks_nodegroup_scaling")
    @patch("challenges.aws_utils.recreate_eks_nodegroup")
    @patch("challenges.aws_utils.settings", DEBUG=False, TEST=True)
    def test_test_mode_dispatches_nothing(
        self, mock_settings, mock_recreate, mock_scale
    ):
        """
        The hook fires on every Challenge save, so without this guard the whole
        test suite would dispatch Celery tasks at a broker that is not running.
        """
        self.challenge.worker_instance_type = "g5.xlarge"

        action = eks_nodegroup_config_change_callback(self.challenge)

        self.assertIsNone(action)
        mock_recreate.delay.assert_not_called()
        mock_scale.delay.assert_not_called()
