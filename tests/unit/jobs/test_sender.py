import os
from unittest.mock import MagicMock, patch

import botocore
import pytest
from challenges.models import Challenge
from jobs.sender import get_or_create_sqs_queue, publish_submission_message


@pytest.fixture
def message():
    return {
        "challenge_pk": 1,
        "phase_pk": 1,
        "submission_pk": 1,
        "submitted_image_uri": "http://example.com/image",
        "is_static_dataset_code_upload_submission": False,
    }


@patch("jobs.sender.Challenge.objects.get")
@patch("jobs.sender.logger")
def test_publish_submission_message_challenge_does_not_exist(
    mock_logger, mock_challenge_get, message
):
    # Simulate Challenge.DoesNotExist exception
    mock_challenge_get.side_effect = Challenge.DoesNotExist

    response = publish_submission_message(message)

    # Assert logger.exception is called with the correct message
    mock_logger.exception.assert_called_once_with(
        "Challenge does not exist for the given id {}".format(
            message["challenge_pk"]
        )
    )
    # Assert the function returns None
    assert response is None


@patch("jobs.sender.get_or_create_sqs_queue")
@patch("jobs.sender.increment_statsd_counter")
@patch("jobs.sender.get_submission_model")
@patch("jobs.sender.send_slack_notification")
@patch("jobs.sender.Challenge.objects.get")
def test_publish_submission_message_success(
    mock_challenge_get,
    mock_send_slack_notification,
    mock_get_submission_model,
    mock_increment_statsd_counter,
    mock_get_or_create_sqs_queue,
    message,
):
    # Mock Challenge object
    mock_challenge = MagicMock()
    mock_challenge.queue = "test-queue"
    mock_challenge.slack_webhook_url = "http://slack-webhook-url"
    mock_challenge.remote_evaluation = False
    mock_challenge.title = "Test Challenge"
    mock_challenge_get.return_value = mock_challenge

    # Mock SQS queue
    mock_queue = MagicMock()
    mock_queue.send_message.return_value = {"MessageId": "12345"}
    mock_get_or_create_sqs_queue.return_value = mock_queue

    # Mock Submission object
    mock_submission = MagicMock()
    mock_submission.participant_team.team_name = "Test Team"
    mock_submission.challenge_phase.name = "Test Phase"
    mock_get_submission_model.return_value = mock_submission

    response = publish_submission_message(message)

    # Assert send_slack_notification is called with the correct parameters
    expected_slack_message = {
        "text": "A *new submission* has been uploaded to Test Challenge",
        "fields": [
            {"title": "Challenge Phase", "value": "Test Phase", "short": True},
            {
                "title": "Participant Team Name",
                "value": "Test Team",
                "short": True,
            },
            {
                "title": "Submission Id",
                "value": message["submission_pk"],
                "short": True,
            },
        ],
    }
    mock_send_slack_notification.assert_called_once_with(
        mock_challenge.slack_webhook_url, expected_slack_message
    )

    # Assert the function returns the SQS response
    assert response == {"MessageId": "12345"}


@patch("jobs.sender.boto3.resource")
@patch("jobs.sender.settings")
def test_get_or_create_sqs_queue_use_host_sqs(
    mock_settings, mock_boto3_resource
):
    mock_settings.DEBUG = False
    mock_settings.TEST = False

    mock_challenge = MagicMock()
    mock_challenge.use_host_sqs = True
    mock_challenge.queue_aws_region = "us-west-2"
    mock_challenge.aws_secret_access_key = "secret"
    mock_challenge.aws_access_key_id = "key"

    mock_sqs = MagicMock()
    mock_boto3_resource.return_value = mock_sqs

    queue_name = "test-queue"
    queue = get_or_create_sqs_queue(queue_name, mock_challenge)

    mock_boto3_resource.assert_called_once_with(
        "sqs",
        region_name=mock_challenge.queue_aws_region,
        aws_secret_access_key=mock_challenge.aws_secret_access_key,
        aws_access_key_id=mock_challenge.aws_access_key_id,
    )
    assert queue == mock_sqs.get_queue_by_name.return_value


@patch("jobs.sender.boto3.resource")
@patch("jobs.sender.settings")
def test_get_or_create_sqs_queue_challenge_use_host_sqs(
    mock_settings, mock_boto3_resource
):
    # Test case where challenge.use_host_sqs is True
    mock_settings.DEBUG = False
    mock_settings.TEST = False

    mock_challenge = MagicMock()
    mock_challenge.use_host_sqs = True
    mock_challenge.queue_aws_region = "us-east-1"
    mock_challenge.aws_access_key_id = "foobar_key"
    mock_challenge.aws_secret_access_key = "foobar_secret"

    mock_sqs = MagicMock()
    mock_boto3_resource.return_value = mock_sqs

    queue_name = "test-queue"
    queue = get_or_create_sqs_queue(queue_name, mock_challenge)

    mock_boto3_resource.assert_called_once_with(
        "sqs",
        region_name="us-east-1",
        aws_access_key_id="foobar_key",
        aws_secret_access_key="foobar_secret",
    )
    assert queue == mock_sqs.get_queue_by_name.return_value


@patch("jobs.sender.boto3.resource")
@patch("jobs.sender.settings")
def test_get_or_create_sqs_queue_no_challenge(
    mock_settings, mock_boto3_resource
):
    # Test case where challenge is None
    mock_settings.DEBUG = False
    mock_settings.TEST = False

    mock_sqs = MagicMock()
    mock_boto3_resource.return_value = mock_sqs

    queue_name = "test-queue"
    queue = get_or_create_sqs_queue(queue_name)

    mock_boto3_resource.assert_called_once_with(
        "sqs",
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
    )
    assert queue == mock_sqs.get_queue_by_name.return_value


@patch("jobs.sender.boto3.resource")
@patch("jobs.sender.settings")
def test_get_or_create_sqs_queue_non_existent_queue(
    mock_settings, mock_boto3_resource
):
    # Test case where the queue does not exist, and it gets created
    mock_settings.DEBUG = False
    mock_settings.TEST = False

    mock_challenge = MagicMock()
    mock_challenge.use_host_sqs = False
    mock_challenge.sqs_retention_period = "1209600"
    mock_challenge.sqs_visibility_timeout = "600"

    mock_sqs = MagicMock()
    mock_boto3_resource.return_value = mock_sqs

    mock_sqs.get_queue_by_name.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AWS.SimpleQueueService.NonExistentQueue"}},
        "GetQueueUrl",
    )

    mock_created_queue = MagicMock()
    mock_sqs.create_queue.return_value = mock_created_queue

    queue_name = "test-queue"
    queue = get_or_create_sqs_queue(queue_name, mock_challenge)

    mock_sqs.create_queue.assert_called_once_with(
        QueueName=queue_name,
        Attributes={
            "MessageRetentionPeriod": mock_challenge.sqs_retention_period,
            "VisibilityTimeout": mock_challenge.sqs_visibility_timeout,
        },
    )
    assert queue == mock_created_queue


@patch("jobs.sender.boto3.resource")
@patch("jobs.sender.settings")
def test_get_or_create_sqs_queue_debug_or_test(
    mock_settings, mock_boto3_resource
):
    # Test case where settings.DEBUG or settings.TEST is True
    mock_settings.DEBUG = True
    mock_settings.TEST = False

    mock_sqs = MagicMock()
    mock_boto3_resource.return_value = mock_sqs

    queue_name = "test-queue"
    queue = get_or_create_sqs_queue(queue_name)

    mock_boto3_resource.assert_called_once_with(
        "sqs",
        endpoint_url=os.environ.get("AWS_SQS_ENDPOINT", "http://sqs:9324"),
        region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID", "x"),
    )
    assert (
        queue_name != "evalai_submission_queue"
    )  # 'queue_name' is not modified in the test, so assert the original value was passed correctly
    assert queue  # Ensure queue was returned


@patch("jobs.sender.boto3.resource")
@patch("jobs.sender.settings")
def test_get_or_create_sqs_queue_empty_queue_name(
    mock_settings, mock_boto3_resource
):
    # Test case where queue_name is empty
    mock_settings.DEBUG = False
    mock_settings.TEST = False

    mock_sqs = MagicMock()
    mock_boto3_resource.return_value = mock_sqs

    queue_name = ""
    queue = get_or_create_sqs_queue(queue_name)

    mock_sqs.get_queue_by_name.assert_called_once_with(
        QueueName="evalai_submission_queue"
    )
    assert queue  # Ensure queue was returned
