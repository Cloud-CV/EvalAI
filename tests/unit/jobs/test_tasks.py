from unittest.mock import MagicMock, patch

from jobs.models import Submission
from jobs.tasks import (
    download_file_and_publish_submission_message,
    tag_submission_artifact_retention_tags,
)


@patch("jobs.tasks.get_participant_team_id_of_user_for_a_challenge")
@patch("jobs.tasks.ParticipantTeam.objects.get")
@patch("jobs.tasks.User.objects.get")
@patch("jobs.tasks.ChallengePhase.objects.get")
@patch("jobs.tasks.get_file_from_url")
@patch("jobs.tasks.SimpleUploadedFile")
@patch("jobs.tasks.SubmissionSerializer")
@patch("jobs.tasks.publish_submission_message")
@patch("jobs.tasks.shutil.rmtree")
@patch("jobs.s3_retention.enqueue_submission_artifact_retention_tagging")
@patch("jobs.tasks.open", create=True)
def test_download_file_and_publish_submission_message_success(
    mock_open,
    mock_enqueue_tagging,
    mock_rmtree,
    mock_publish,
    mock_serializer,
    mock_simple_uploaded_file,
    mock_get_file_from_url,
    mock_challenge_phase_get,
    mock_user_get,
    mock_participant_team_get,
    mock_get_participant_team_id,
):
    mock_user = MagicMock()
    mock_user_get.return_value = mock_user

    mock_challenge_phase = MagicMock()
    mock_challenge_phase.challenge.pk = 1
    mock_challenge_phase.pk = 2
    mock_challenge_phase.challenge.is_submission_paused = False
    mock_challenge_phase.is_submission_paused = False
    mock_challenge_phase_get.return_value = mock_challenge_phase

    mock_get_participant_team_id.return_value = 3
    mock_participant_team = MagicMock()
    mock_participant_team_get.return_value = mock_participant_team

    mock_get_file_from_url.return_value = {
        "temp_dir_path": "/tmp/test",
        "name": "file.txt",
    }

    mock_file = MagicMock()
    mock_open.return_value.__enter__.return_value = mock_file

    mock_serializer_instance = MagicMock()
    mock_serializer_instance.is_valid.return_value = True
    mock_serializer_instance.instance.pk = 123
    mock_serializer_instance.instance.input_file.name = (
        "submission_files/foo/bar.txt"
    )
    mock_serializer.return_value = mock_serializer_instance

    request_data = {
        "file_url": "http://test/file.txt",
        "method_name": "test",
        "method_description": "desc",
        "project_url": "http://project",
        "publication_url": "http://pub",
    }

    download_file_and_publish_submission_message(
        request_data, user_pk=1, request_method="POST", challenge_phase_id=2
    )

    mock_serializer.assert_called()
    mock_enqueue_tagging.assert_called_once_with(
        mock_serializer_instance.instance,
        ["submission_files/foo/bar.txt"],
    )
    mock_publish.assert_called()
    mock_rmtree.assert_called()


@patch("jobs.s3_retention.tag_submission_artifacts_for_retention")
@patch("jobs.tasks.Submission.objects")
def test_tag_submission_artifact_retention_tags_calls_retention_helper(
    mock_submission_objects, mock_tag_fn
):
    mock_submission = MagicMock()
    qs = MagicMock()
    mock_submission_objects.select_related.return_value = qs
    qs.get.return_value = mock_submission

    tag_submission_artifact_retention_tags(42, ["media/path/file.bin"])

    mock_submission_objects.select_related.assert_called_once_with(
        "challenge_phase",
        "challenge_phase__challenge",
    )
    qs.get.assert_called_once_with(pk=42)
    mock_tag_fn.assert_called_once_with(
        mock_submission,
        ["media/path/file.bin"],
    )


@patch("jobs.s3_retention.tag_submission_artifacts_for_retention")
@patch("jobs.tasks.Submission.objects")
def test_tag_submission_artifact_retention_tags_handles_missing_submission(
    mock_submission_objects,
    mock_tag_fn,
):
    qs = MagicMock()
    mock_submission_objects.select_related.return_value = qs
    qs.get.side_effect = Submission.DoesNotExist()

    tag_submission_artifact_retention_tags(999999, ["x"])

    mock_tag_fn.assert_not_called()


@patch("jobs.tasks.get_participant_team_id_of_user_for_a_challenge")
@patch("jobs.tasks.ParticipantTeam.objects.get")
@patch("jobs.tasks.User.objects.get")
@patch("jobs.tasks.ChallengePhase.objects.get")
@patch("jobs.tasks.get_file_from_url")
@patch("jobs.tasks.shutil.rmtree")
@patch("jobs.tasks.logger")
def test_download_file_and_publish_submission_message_exception(
    mock_logger,
    mock_rmtree,
    mock_get_file_from_url,
    mock_challenge_phase_get,
    mock_user_get,
    mock_participant_team_get,
    mock_get_participant_team_id,
):
    mock_user = MagicMock()
    mock_user_get.return_value = mock_user

    mock_challenge_phase = MagicMock()
    mock_challenge_phase.challenge.pk = 1
    mock_challenge_phase.pk = 2
    mock_challenge_phase.challenge.is_submission_paused = False
    mock_challenge_phase.is_submission_paused = False
    mock_challenge_phase_get.return_value = mock_challenge_phase

    mock_get_participant_team_id.return_value = 3
    mock_participant_team = MagicMock()
    mock_participant_team_get.return_value = mock_participant_team

    mock_get_file_from_url.side_effect = Exception("Download failed")

    request_data = {
        "file_url": "http://test/file.txt",
        "method_name": "test",
        "method_description": "desc",
        "project_url": "http://project",
        "publication_url": "http://pub",
    }

    download_file_and_publish_submission_message(
        request_data, user_pk=1, request_method="POST", challenge_phase_id=2
    )

    mock_logger.exception.assert_called()
    mock_rmtree.assert_not_called()


@patch("jobs.tasks.get_participant_team_id_of_user_for_a_challenge")
@patch("jobs.tasks.ParticipantTeam.objects.get")
@patch("jobs.tasks.User.objects.get")
@patch("jobs.tasks.ChallengePhase.objects.get")
@patch("jobs.tasks.get_file_from_url")
@patch("jobs.tasks.shutil.rmtree")
@patch("jobs.tasks.logger")
@patch("jobs.tasks.open", create=True)
def test_download_file_and_publish_submission_message_exception_with_temp_dir(
    mock_open,
    mock_logger,
    mock_rmtree,
    mock_get_file_from_url,
    mock_challenge_phase_get,
    mock_user_get,
    mock_participant_team_get,
    mock_get_participant_team_id,
):
    mock_user = MagicMock()
    mock_user_get.return_value = mock_user

    mock_challenge_phase = MagicMock()
    mock_challenge_phase.challenge.pk = 1
    mock_challenge_phase.pk = 2
    mock_challenge_phase.challenge.is_submission_paused = False
    mock_challenge_phase.is_submission_paused = False
    mock_challenge_phase_get.return_value = mock_challenge_phase

    mock_get_participant_team_id.return_value = 3
    mock_participant_team = MagicMock()
    mock_participant_team_get.return_value = mock_participant_team

    mock_get_file_from_url.return_value = {
        "temp_dir_path": "/tmp/test",
        "name": "file.txt",
    }
    mock_open.side_effect = Exception("File open failed")

    request_data = {
        "file_url": "http://test/file.txt",
        "method_name": "test",
        "method_description": "desc",
        "project_url": "http://project",
        "publication_url": "http://pub",
    }

    download_file_and_publish_submission_message(
        request_data, user_pk=1, request_method="POST", challenge_phase_id=2
    )

    mock_rmtree.assert_called_once_with("/tmp/test")
    assert mock_logger.exception.call_count == 1


@patch("jobs.tasks.User.objects.get")
@patch("jobs.tasks.ChallengePhase.objects.get")
@patch("jobs.tasks.get_participant_team_id_of_user_for_a_challenge")
@patch("jobs.tasks.ParticipantTeam.objects.get")
@patch("jobs.tasks.publish_submission_message")
@patch("jobs.tasks.logger")
def test_download_file_and_publish_submission_message_skipped_when_challenge_paused(
    mock_logger,
    mock_publish,
    mock_participant_team_get,
    mock_get_participant_team_id,
    mock_challenge_phase_get,
    mock_user_get,
):
    mock_user_get.return_value = MagicMock()
    mock_challenge_phase = MagicMock()
    mock_challenge_phase.challenge.pk = 42
    mock_challenge_phase.pk = 99
    mock_challenge_phase.challenge.is_submission_paused = True
    mock_challenge_phase.is_submission_paused = False
    mock_challenge_phase_get.return_value = mock_challenge_phase

    request_data = {
        "file_url": "http://test/file.txt",
        "method_name": "test",
        "method_description": "desc",
        "project_url": "http://project",
        "publication_url": "http://pub",
    }

    download_file_and_publish_submission_message(
        request_data, user_pk=1, request_method="POST", challenge_phase_id=99
    )

    mock_logger.warning.assert_called_once()
    mock_publish.assert_not_called()
    mock_get_participant_team_id.assert_not_called()
    mock_participant_team_get.assert_not_called()


@patch("jobs.tasks.User.objects.get")
@patch("jobs.tasks.ChallengePhase.objects.get")
@patch("jobs.tasks.get_participant_team_id_of_user_for_a_challenge")
@patch("jobs.tasks.ParticipantTeam.objects.get")
@patch("jobs.tasks.publish_submission_message")
@patch("jobs.tasks.logger")
def test_download_file_and_publish_submission_message_skipped_when_phase_paused(
    mock_logger,
    mock_publish,
    mock_participant_team_get,
    mock_get_participant_team_id,
    mock_challenge_phase_get,
    mock_user_get,
):
    mock_user_get.return_value = MagicMock()
    mock_challenge_phase = MagicMock()
    mock_challenge_phase.challenge.pk = 42
    mock_challenge_phase.pk = 99
    mock_challenge_phase.challenge.is_submission_paused = False
    mock_challenge_phase.is_submission_paused = True
    mock_challenge_phase_get.return_value = mock_challenge_phase

    request_data = {
        "file_url": "http://test/file.txt",
        "method_name": "test",
        "method_description": "desc",
        "project_url": "http://project",
        "publication_url": "http://pub",
    }

    download_file_and_publish_submission_message(
        request_data, user_pk=1, request_method="POST", challenge_phase_id=99
    )

    mock_logger.warning.assert_called_once()
    mock_publish.assert_not_called()
    mock_get_participant_team_id.assert_not_called()
    mock_participant_team_get.assert_not_called()
