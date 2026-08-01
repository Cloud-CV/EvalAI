from io import StringIO
from unittest.mock import MagicMock, patch

import botocore
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.fixture
def mock_challenge():
    challenge = MagicMock()
    challenge.pk = 1
    challenge.queue = "test-challenge-queue.fifo"
    return challenge


@patch("jobs.management.commands.purge_challenge_sqs_queue.get_sqs_queue")
@patch(
    "jobs.management.commands.purge_challenge_sqs_queue.Challenge.objects.get"
)
def test_purge_challenge_sqs_queue_success(
    mock_challenge_get, mock_get_queue, mock_challenge
):
    mock_challenge_get.return_value = mock_challenge
    mock_queue = MagicMock()
    mock_get_queue.return_value = mock_queue

    out = StringIO()
    call_command(
        "purge_challenge_sqs_queue",
        str(mock_challenge.pk),
        "--yes",
        stdout=out,
    )

    mock_challenge_get.assert_called_once_with(pk=mock_challenge.pk)
    mock_get_queue.assert_called_once_with(
        mock_challenge.queue, mock_challenge
    )
    mock_queue.purge.assert_called_once_with()
    assert "Purged queue" in out.getvalue()
    assert mock_challenge.queue in out.getvalue()


@patch(
    "jobs.management.commands.purge_challenge_sqs_queue.Challenge.objects.get"
)
def test_purge_challenge_sqs_queue_missing_challenge(mock_challenge_get):
    from challenges.models import Challenge

    mock_challenge_get.side_effect = Challenge.DoesNotExist

    with pytest.raises(CommandError, match="does not exist"):
        call_command("purge_challenge_sqs_queue", "999", "--yes")


@patch(
    "jobs.management.commands.purge_challenge_sqs_queue.Challenge.objects.get"
)
def test_purge_challenge_sqs_queue_empty_queue_name(mock_challenge_get):
    challenge = MagicMock()
    challenge.pk = 1
    challenge.queue = ""
    mock_challenge_get.return_value = challenge

    with pytest.raises(CommandError, match="no queue name"):
        call_command("purge_challenge_sqs_queue", "1", "--yes")


@patch("jobs.management.commands.purge_challenge_sqs_queue.get_sqs_queue")
@patch(
    "jobs.management.commands.purge_challenge_sqs_queue.Challenge.objects.get"
)
def test_purge_challenge_sqs_queue_missing_sqs_queue(
    mock_challenge_get, mock_get_queue, mock_challenge
):
    mock_challenge_get.return_value = mock_challenge
    mock_get_queue.side_effect = botocore.exceptions.ClientError(
        {"Error": {"Code": "AWS.SimpleQueueService.NonExistentQueue"}},
        "GetQueueUrl",
    )

    with pytest.raises(CommandError, match="does not exist"):
        call_command(
            "purge_challenge_sqs_queue",
            str(mock_challenge.pk),
            "--yes",
        )

    mock_challenge_get.assert_called_once_with(pk=mock_challenge.pk)
    mock_get_queue.assert_called_once_with(
        mock_challenge.queue, mock_challenge
    )


@patch("jobs.management.commands.purge_challenge_sqs_queue.get_sqs_queue")
@patch(
    "jobs.management.commands.purge_challenge_sqs_queue.Challenge.objects.get"
)
@patch("builtins.input", return_value="n")
def test_purge_challenge_sqs_queue_aborts_without_yes(
    mock_input, mock_challenge_get, mock_get_queue, mock_challenge
):
    mock_challenge_get.return_value = mock_challenge

    out = StringIO()
    call_command(
        "purge_challenge_sqs_queue",
        str(mock_challenge.pk),
        stdout=out,
    )

    mock_get_queue.assert_not_called()
    assert "Aborted" in out.getvalue()
