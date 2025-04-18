import unittest
from http import HTTPStatus
from unittest import TestCase, mock
from unittest.mock import MagicMock, mock_open, patch

import pytest
from botocore.exceptions import ClientError
from challenges.aws_utils import (
    create_ec2_instance,
    create_eks_nodegroup,
    create_service_by_challenge_pk,
    delete_log_group,
    delete_service_by_challenge_pk,
    delete_workers,
    describe_ec2_instance,
    get_code_upload_setup_meta_for_challenge,
    get_logs_from_cloudwatch,
    restart_ec2_instance,
    restart_workers,
    restart_workers_signal_callback,
    scale_resources,
    scale_workers,
    service_manager,
    setup_ec2,
    setup_eks_cluster,
    start_ec2_instance,
    start_workers,
    stop_ec2_instance,
    stop_workers,
    terminate_ec2_instance,
    update_service_by_challenge_pk,
    update_sqs_retention_period,
    update_sqs_retention_period_task,
)
from challenges.models import Challenge
from django.contrib.auth.models import User
from django.core import serializers
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
    return MagicMock()


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

        response_metadata = {"HTTPStatusCode": HTTPStatus.OK}
        mock_client.create_service.return_value = {
            "ResponseMetadata": response_metadata
        }

        with patch(
            "challenges.aws_utils.register_task_def_by_challenge_pk",
            return_value={"ResponseMetadata": response_metadata},
        ):
            response = create_service_by_challenge_pk(
                mock_client, mock_challenge, client_token
            )

        assert response["ResponseMetadata"]["HTTPStatusCode"] == HTTPStatus.OK
        mock_challenge.save.assert_called_once()
        assert mock_challenge.workers == 1

    def test_create_service_client_error(
        self, mock_client, mock_challenge, client_token
    ):
        mock_challenge.workers = None
        mock_challenge.task_def_arn = "valid_task_def_arn"

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


def test_delete_service_success_when_workers_zero(mock_challenge, mock_client):
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


def test_delete_service_success_when_workers_not_zero(
    mock_challenge, mock_client
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


def test_update_service_failure(mock_challenge, mock_client):
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


def test_delete_service_failure(mock_challenge, mock_client):
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


def test_deregister_task_definition_failure(mock_challenge, mock_client):
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


def test_delete_service_client_error(mock_challenge, mock_client):
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

        # Mock client_token_generator and create_service_by_challenge_pk to return a mock response
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

        # Ensure the EC2 instance ID was not cleared and the challenge was not saved
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
                "error": "An error occurred (QueueDoesNotExist) when calling the GetQueueUrl operation: The queue does not exist"
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
        challenge2 = MagicMock()
        challenge2.pk = 2
        challenge2.workers = 10
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
        challenge2 = MagicMock()
        challenge2.pk = 2
        challenge2.workers = 10
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
        # Mock other dependencies
        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_aws_credentials_for_challenge, patch(
            "challenges.aws_utils.task_definition", new_callable=MagicMock
        ) as mock_task_definition, patch(
            "challenges.aws_utils.eval"
        ) as mock_eval:

            mock_get_aws_credentials_for_challenge.return_value = {}
            mock_task_definition.return_value = {
                "some_key": "some_value"
            }  # Use a dictionary here
            mock_eval.return_value = {
                "some_key": "some_value"
            }  # Use a dictionary here

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

            expected_result = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
            }
            self.assertEqual(result, expected_result)

    @patch("challenges.aws_utils.settings", DEBUG=False)
    @patch("challenges.aws_utils.get_boto3_client")
    def test_scale_resources_deregister_failure(
        self, mock_get_boto3_client, mock_settings
    ):
        # Mock client and response
        mock_client = MagicMock()
        mock_get_boto3_client.return_value = mock_client
        mock_client.deregister_task_definition.side_effect = ClientError(
            {"Error": {"Message": "Scaling inactive workers not supported"}},
            "DeregisterTaskDefinition",
        )

        # Mock challenge
        challenge = MagicMock()
        challenge.task_def_arn = "some_task_def_arn"
        challenge.worker_cpu_cores = 2
        challenge.worker_memory = 4096

        # Call the function
        result = scale_resources(
            challenge, worker_cpu_cores=4, worker_memory=8192
        )

        # Assert the expected output
        expected_result = {
            "Error": True,
            "Message": "Scaling inactive workers not supported",
        }
        self.assertEqual(result, expected_result)

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
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_aws_credentials_for_challenge, patch(
            "challenges.aws_utils.task_definition", new_callable=MagicMock
        ) as mock_task_definition, patch(
            "challenges.aws_utils.eval"
        ) as mock_eval:

            mock_get_aws_credentials_for_challenge.return_value = {}
            mock_task_definition.return_value = {
                "some_key": "some_value"
            }  # Use a dictionary here
            mock_eval.return_value = {
                "some_key": "some_value"
            }  # Use a dictionary here

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
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_aws_credentials_for_challenge, patch(
            "challenges.aws_utils.task_definition", new_callable=MagicMock
        ) as mock_task_definition, patch(
            "challenges.aws_utils.eval"
        ) as mock_eval:

            mock_get_aws_credentials_for_challenge.return_value = {}
            mock_task_definition.return_value = {
                "some_key": "some_value"
            }  # Use a dictionary here
            mock_eval.return_value = {
                "some_key": "some_value"
            }  # Use a dictionary here

            # Mock register_task_definition response with error
            mock_client.register_task_definition.return_value = {
                "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
                "Error": "Failed to register task definition",
            }

            # Call the function
            result = scale_resources(
                challenge, worker_cpu_cores=4, worker_memory=8192
            )

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

        # Ensure the delete_service_by_challenge_pk, get_log_group_name, and delete_log_group methods were called
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

        # Mock the delete_service_by_challenge_pk response to simulate a failure
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
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_docker_based_challenge(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Mock a Docker-based challenge queryset
        challenge_docker_based = MagicMock(
            pk=1, is_docker_based=True, is_static_dataset_code_upload=False
        )
        mock_queryset = [challenge_docker_based]

        # Call the function
        result = restart_workers(mock_queryset)

        # Assertions
        expected_failures = [
            {
                "message": "Sorry. This feature is not available for code upload/docker based challenges.",
                "challenge_pk": 1,
            }
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the service_manager method was never called
        mock_service_manager.assert_not_called()

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
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_success(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Mock a challenge with active workers
        challenge_with_workers = MagicMock(
            pk=1,
            workers=2,
            is_docker_based=False,
            is_static_dataset_code_upload=False,
        )
        mock_queryset = [challenge_with_workers]

        # Mock the service_manager response
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.OK}
        }

        # Call the function
        result = restart_workers(mock_queryset)

        # Assertions
        self.assertEqual(result, {"count": 1, "failures": []})

        # Ensure the service_manager method was called
        mock_service_manager.assert_called_once_with(
            mock_get_boto3_client.return_value,
            challenge=challenge_with_workers,
            num_of_tasks=challenge_with_workers.workers,
            force_new_deployment=True,
        )

    @patch("challenges.aws_utils.get_boto3_client")
    @patch("challenges.aws_utils.service_manager")
    @patch("challenges.aws_utils.settings", DEBUG=False)
    def test_restart_workers_failure(
        self, mock_settings, mock_service_manager, mock_get_boto3_client
    ):
        # Mock a challenge with active workers
        challenge_with_workers = MagicMock(
            pk=1,
            workers=2,
            is_docker_based=False,
            is_static_dataset_code_upload=False,
        )
        mock_queryset = [challenge_with_workers]

        # Mock the service_manager response to simulate a failure
        mock_service_manager.return_value = {
            "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.BAD_REQUEST},
            "Error": "An error occurred",
        }

        # Call the function
        result = restart_workers(mock_queryset)

        # Assertions
        expected_failures = [
            {"message": "An error occurred", "challenge_pk": 1}
        ]
        self.assertEqual(result, {"count": 0, "failures": expected_failures})

        # Ensure the service_manager method was called
        mock_service_manager.assert_called_once_with(
            mock_get_boto3_client.return_value,
            challenge=challenge_with_workers,
            num_of_tasks=challenge_with_workers.workers,
            force_new_deployment=True,
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
            "The worker logs in the development environment are available on the terminal. Please use docker-compose logs -f worker to view the logs."
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

        # Assert that delete_log_group was called on the client with the correct argument
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

        # Assert that delete_log_group was called on the client with the correct argument
        mock_client.delete_log_group.assert_called_once_with(
            logGroupName="test-log-group"
        )

        # Retrieve the actual arguments passed to logger.exception
        args, kwargs = mock_logger.exception.call_args

        # Check if the first argument of logger.exception contains the correct message
        self.assertTrue(
            "Delete failed" in str(args[0]),
            f"Expected 'Delete failed' in {args[0]}",
        )


class TestCreateEKSNodegroup(unittest.TestCase):
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
        # Check if start_ec2_instance was called since the EC2 instance already exists
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
        # Check if create_ec2_instance was called since the EC2 instance doesn't exist
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
