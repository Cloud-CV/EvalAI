from challenges.models import Challenge
import pytest
from unittest.mock import patch, MagicMock
from jobs.sender import publish_submission_message  # Adjust the import according to your module structure
from botocore.exceptions import ClientError
from jobs.sender import get_or_create_sqs_queue


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
def test_publish_submission_message_challenge_does_not_exist(mock_logger, mock_challenge_get, message):
    # Simulate Challenge.DoesNotExist exception
    mock_challenge_get.side_effect = Challenge.DoesNotExist

    response = publish_submission_message(message)

    # Assert logger.exception is called with the correct message
    mock_logger.exception.assert_called_once_with(
        "Challenge does not exist for the given id {}".format(message["challenge_pk"])
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
    message
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
            {"title": "Participant Team Name", "value": "Test Team", "short": True},
            {"title": "Submission Id", "value": message["submission_pk"], "short": True},
        ],
    }
    mock_send_slack_notification.assert_called_once_with(mock_challenge.slack_webhook_url, expected_slack_message)

    # Assert the function returns the SQS response
    assert response == {"MessageId": "12345"}


@patch("jobs.sender.boto3.resource")
@patch("jobs.sender.settings")
def test_get_or_create_sqs_queue_use_host_sqs(mock_settings, mock_boto3_resource):
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
def test_get_or_create_sqs_queue_default(mock_settings, mock_boto3_resource):
    mock_settings.DEBUG = False
    mock_settings.TEST = False

    mock_challenge = MagicMock()
    mock_challenge.use_host_sqs = False

    mock_sqs = MagicMock()
    mock_boto3_resource.return_value = mock_sqs

    queue_name = "test-queue"
    queue = get_or_create_sqs_queue(queue_name, mock_challenge)

    mock_boto3_resource.assert_called_once_with(
        "sqs",
        region_name="us-east-1",
        aws_secret_access_key="x",
        aws_access_key_id="x",
    )
    assert queue == mock_sqs.get_queue_by_name.return_value

@patch("jobs.sender.boto3.resource")
@patch("jobs.sender.settings")
def test_get_or_create_sqs_queue_create_queue(mock_settings, mock_boto3_resource):
    mock_settings.DEBUG = False
    mock_settings.TEST = False

    mock_challenge = MagicMock()
    mock_challenge.use_host_sqs = False
    mock_challenge.sqs_retention_period = 1209600  # 14 days

    mock_sqs = MagicMock()
    mock_boto3_resource.return_value = mock_sqs

    mock_sqs.get_queue_by_name.side_effect = ClientError(
        {"Error": {"Code": "AWS.SimpleQueueService.NonExistentQueue"}}, "GetQueueUrl"
    )

    queue_name = "test-queue"
    queue = get_or_create_sqs_queue(queue_name, mock_challenge)

    mock_sqs.create_queue.assert_called_once_with(
        QueueName=queue_name,
        Attributes={"MessageRetentionPeriod": str(mock_challenge.sqs_retention_period)},
    )
    assert queue == mock_sqs.create_queue.return_value
