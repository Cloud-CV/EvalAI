import os
import unittest
from unittest import TestCase, mock
from unittest.mock import MagicMock, Mock, patch
from urllib.error import HTTPError

from jobs.utils import (
    calculate_distinct_sorted_leaderboard_data,
    get_file_from_url,
    get_leaderboard_data_model,
    get_remaining_submission_for_a_phase,
    handle_submission_rerun,
    handle_submission_resume,
    is_url_valid,
    reorder_submissions_comparator_to_key,
)


class TestUtils(unittest.TestCase):
    @patch("urllib.request.urlopen")
    def test_is_url_valid(self, mock_urlopen):
        # Test with a valid URL
        mock_urlopen.return_value = True
        self.assertTrue(is_url_valid("http://example.com"))

        # Test with an invalid URL
        mock_urlopen.side_effect = HTTPError(
            None, 404, "Not Found", None, None
        )
        self.assertFalse(is_url_valid("http://invalid-url.com"))

    @patch("requests.get")
    def test_get_file_from_url(self, mock_get):
        mock_response = MagicMock()
        mock_response.iter_content = lambda chunk_size: [b"test data"]
        mock_get.return_value = mock_response

        file_obj = get_file_from_url("http://example.com/file.txt")
        self.assertEqual(file_obj["name"], "file.txt")
        self.assertTrue(os.path.exists(file_obj["temp_dir_path"]))

    @patch("challenges.models.LeaderboardData.objects.exclude")
    @patch("challenges.models.LeaderboardData.objects.filter")
    def test_calculate_distinct_sorted_leaderboard_data(
        self, mock_filter, mock_exclude
    ):
        mock_user = MagicMock()
        mock_challenge_obj = MagicMock()
        mock_challenge_phase_split = MagicMock()
        mock_leaderboard_data = MagicMock()
        mock_filter.return_value = mock_leaderboard_data
        mock_exclude.return_value = mock_leaderboard_data

        (
            leaderboard_data,
            status_code,
        ) = calculate_distinct_sorted_leaderboard_data(
            mock_user,
            mock_challenge_obj,
            mock_challenge_phase_split,
            True,
            "order_by",
        )
        self.assertEqual(status_code, 200)

    @patch("jobs.utils.Submission")
    @patch("jobs.utils.get_participant_team_id_of_user_for_a_challenge")
    @patch("jobs.utils.get_challenge_phase_model")
    @patch("jobs.utils.get_challenge_model")
    def test_get_remaining_submission_for_a_phase_max_limit(
        self,
        mock_get_challenge_model,
        mock_get_challenge_phase_model,
        mock_get_team_id,
        mock_Submission,
    ):
        mock_user = MagicMock()
        mock_get_challenge_model.return_value = MagicMock()
        mock_challenge_phase = MagicMock()
        mock_challenge_phase.max_submissions = 1
        mock_challenge_phase.max_submissions_per_month = 5
        mock_challenge_phase.max_submissions_per_day = 2
        mock_get_challenge_phase_model.return_value = mock_challenge_phase
        mock_get_team_id.return_value = 123

        mock_qs = MagicMock()
        mock_qs.count.return_value = 1
        mock_Submission.objects.filter.return_value.exclude.return_value = (
            mock_qs
        )
        mock_qs.filter.return_value = mock_qs

        response, status_code = get_remaining_submission_for_a_phase(
            mock_user, 1, 1
        )
        self.assertEqual(status_code, 200)
        self.assertTrue(response["submission_limit_exceeded"])
        self.assertIn(
            "You have exhausted maximum submission limit!", response["message"]
        )

    @patch("jobs.utils.Submission")
    @patch("jobs.utils.get_participant_team_id_of_user_for_a_challenge")
    @patch("jobs.utils.get_challenge_phase_model")
    @patch("jobs.utils.get_challenge_model")
    def test_get_remaining_submission_for_a_phase_monthly_and_daily_limit(
        self,
        mock_get_challenge_model,
        mock_get_challenge_phase_model,
        mock_get_team_id,
        mock_Submission,
    ):
        # Setup mocks
        mock_user = MagicMock()
        mock_get_challenge_model.return_value = MagicMock()
        mock_challenge_phase = MagicMock()
        mock_challenge_phase.max_submissions = 10
        mock_challenge_phase.max_submissions_per_month = 2
        mock_challenge_phase.max_submissions_per_day = 1
        mock_get_challenge_phase_model.return_value = mock_challenge_phase
        mock_get_team_id.return_value = 123

        mock_qs = MagicMock()
        mock_Submission.objects.filter.return_value.exclude.return_value = (
            mock_qs
        )
        mock_qs.filter.return_value = mock_qs

        mock_qs.count.side_effect = [1, 2, 0]
        response, status_code = get_remaining_submission_for_a_phase(
            mock_user, 1, 1
        )
        self.assertEqual(status_code, 200)
        self.assertIn(
            "You have exhausted this month's submission limit!",
            response["message"],
        )
        self.assertIn("remaining_time", response)

        mock_qs.count.side_effect = [1, 2, 1]
        response, status_code = get_remaining_submission_for_a_phase(
            mock_user, 1, 1
        )
        self.assertEqual(status_code, 200)
        self.assertIn(
            "Both daily and monthly submission limits are exhausted!",
            response["message"],
        )
        self.assertIn("remaining_time", response)

    @patch("jobs.utils.Submission")
    @patch("jobs.utils.get_participant_team_id_of_user_for_a_challenge")
    @patch("jobs.utils.get_challenge_phase_model")
    @patch("jobs.utils.get_challenge_model")
    def test_get_remaining_submission_for_a_phase_both_monthly_and_daily_limit(
        self,
        mock_get_challenge_model,
        mock_get_challenge_phase_model,
        mock_get_team_id,
        mock_Submission,
    ):
        mock_user = MagicMock()
        mock_get_challenge_model.return_value = MagicMock()
        mock_challenge_phase = MagicMock()
        mock_challenge_phase.max_submissions = 10
        mock_challenge_phase.max_submissions_per_month = 2
        mock_challenge_phase.max_submissions_per_day = 1
        mock_get_challenge_phase_model.return_value = mock_challenge_phase
        mock_get_team_id.return_value = 123

        mock_qs = MagicMock()

        mock_qs.count.side_effect = [1, 2, 1]
        mock_Submission.objects.filter.return_value.exclude.return_value = (
            mock_qs
        )
        mock_qs.filter.return_value = mock_qs

        response, status_code = get_remaining_submission_for_a_phase(
            mock_user, 1, 1
        )
        self.assertEqual(status_code, 200)

        mock_qs.count.side_effect = [1, 2, 2]
        response, status_code = get_remaining_submission_for_a_phase(
            mock_user, 1, 1
        )
        self.assertEqual(status_code, 200)
        self.assertIn(
            "Both daily and monthly submission limits are exhausted!",
            response["message"],
        )
        self.assertIn("remaining_time", response)

    @patch("jobs.utils.LeaderboardData")
    def test_calculate_distinct_sorted_leaderboard_data_missing_labels_key(
        self, mock_LeaderboardData
    ):
        mock_user = MagicMock()
        mock_challenge_obj = MagicMock()
        mock_challenge_phase_split = MagicMock()
        mock_leaderboard = MagicMock()

        mock_leaderboard.schema = {"default_order_by": "score"}
        mock_challenge_phase_split.leaderboard = mock_leaderboard
        mock_challenge_phase_split.is_leaderboard_order_descending = False
        mock_challenge_phase_split.challenge_phase.is_partial_submission_evaluation_enabled = (
            False
        )
        mock_challenge_phase_split.visibility = 1
        mock_challenge_phase_split.show_execution_time = False
        mock_challenge_phase_split.show_leaderboard_by_latest_submission = (
            False
        )
        mock_challenge_obj.creator.get_all_challenge_host_email.return_value = (
            []
        )
        mock_challenge_obj.banned_email_ids = []

        response, status_code = calculate_distinct_sorted_leaderboard_data(
            mock_user,
            mock_challenge_obj,
            mock_challenge_phase_split,
            True,
            "score",
        )

        self.assertEqual(status_code, 400)
        self.assertIn("labels key is missing", response["error"])

    @patch("challenges.models.LeaderboardData.objects.exclude")
    @patch("challenges.models.LeaderboardData.objects.filter")
    def test_calculate_distinct_sorted_leaderboard_data_order_by_in_labels(
        self, mock_filter, mock_exclude
    ):
        mock_user = MagicMock()
        mock_challenge_obj = MagicMock()
        mock_challenge_phase_split = MagicMock()
        mock_leaderboard_data = MagicMock()
        mock_filter.return_value = mock_leaderboard_data
        mock_exclude.return_value = mock_leaderboard_data

        mock_leaderboard = MagicMock()
        mock_leaderboard.schema = {
            "default_order_by": "score",
            "labels": ["score", "order_by"],
            "metadata": {"score": {"sort_ascending": False}},
        }
        mock_challenge_phase_split.leaderboard = mock_leaderboard
        mock_challenge_phase_split.is_leaderboard_order_descending = False
        mock_challenge_phase_split.challenge_phase.is_partial_submission_evaluation_enabled = (
            False
        )
        mock_challenge_phase_split.visibility = 1
        mock_challenge_phase_split.show_execution_time = False
        mock_challenge_phase_split.show_leaderboard_by_latest_submission = (
            False
        )
        mock_challenge_obj.creator.get_all_challenge_host_email.return_value = (
            []
        )
        mock_challenge_obj.banned_email_ids = []

        (
            leaderboard_data,
            status_code,
        ) = calculate_distinct_sorted_leaderboard_data(
            mock_user,
            mock_challenge_obj,
            mock_challenge_phase_split,
            True,
            "order_by",
        )
        self.assertEqual(status_code, 200)


class TestHandleSubmissionResume(unittest.TestCase):
    @mock.patch("jobs.utils.SubmissionSerializer")
    @mock.patch("jobs.utils.timezone.now")
    @mock.patch("jobs.utils.requests.get")
    def test_handle_submission_resume(
        self, mock_requests_get, mock_timezone_now, mock_SubmissionSerializer
    ):
        # Set up mock objects
        mock_submission = mock.Mock()
        mock_submission.challenge_phase.challenge.is_docker_based = True
        mock_submission.challenge_phase.challenge.is_static_dataset_code_upload = (
            False
        )
        mock_submission.input_file.url = "http://example.com/input_file"
        mock_submission.pk = 1
        mock_submission.challenge_phase.pk = 2
        mock_submission.challenge_phase.challenge.pk = 3

        mock_serializer = mock_SubmissionSerializer.return_value
        mock_serializer.is_valid.return_value = True

        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "submitted_image_uri": "http://example.com/image_uri"
        }
        mock_requests_get.return_value = mock_response

        mock_timezone_now.return_value = "mocked_time"

        # Call the function
        result = handle_submission_resume(mock_submission, "resumed")

        # Assert the results
        mock_SubmissionSerializer.assert_called_once_with(
            mock_submission, data={"status": "resumed"}, partial=True
        )
        self.assertTrue(mock_serializer.is_valid.called)
        self.assertEqual(mock_submission.rerun_resumed_at, "mocked_time")
        self.assertTrue(mock_serializer.save.called)
        mock_requests_get.assert_called_once_with(
            "http://example.com/input_file"
        )
        self.assertEqual(
            result,
            {
                "challenge_pk": 3,
                "phase_pk": 2,
                "submission_pk": 1,
                "is_static_dataset_code_upload_submission": False,
                "submitted_image_uri": "http://example.com/image_uri",
            },
        )
        # Test the except block
        mock_requests_get.side_effect = Exception("Failed to get input_file")
        with self.assertLogs("jobs.utils", level="ERROR") as cm:
            message = handle_submission_resume(mock_submission, "resumed")
            self.assertIn("Failed to get input_file", cm.output[0])
            self.assertIsNone(message)

        # Test the line 276
        mock_submission.challenge_phase.challenge.is_static_dataset_code_upload = (
            True
        )
        mock_requests_get.side_effect = None
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "submitted_image_uri": "some_uri"
        }

        message = handle_submission_resume(mock_submission, "resumed")
        self.assertTrue(message["is_static_dataset_code_upload_submission"])

    @mock.patch("jobs.utils.SubmissionSerializer")
    @mock.patch("jobs.utils.timezone.now")
    @mock.patch("jobs.utils.requests.get")
    def test_handle_submission_rerun(
        self, mock_requests_get, mock_timezone_now, mock_SubmissionSerializer
    ):
        # Set up mock objects
        mock_submission = mock.Mock()
        mock_submission.challenge_phase.challenge.is_docker_based = True
        mock_submission.challenge_phase.challenge.is_static_dataset_code_upload = (
            False
        )
        mock_submission.input_file.url = "http://example.com/input_file"
        mock_submission.pk = 1
        mock_submission.challenge_phase.pk = 2
        mock_submission.challenge_phase.challenge.pk = 3

        # Mock the _meta attribute and local_fields
        mock_submission._meta.local_fields = []

        mock_serializer = mock_SubmissionSerializer.return_value
        mock_serializer.is_valid.return_value = True

        # Test the normal flow
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "submitted_image_uri": "some_uri"
        }

        message = handle_submission_rerun(mock_submission, "resumed")
        self.assertEqual(message["challenge_pk"], 3)
        self.assertEqual(message["phase_pk"], 2)
        self.assertIsNone(
            message["submission_pk"]
        )  # Adjusted to check for None
        self.assertFalse(message["is_static_dataset_code_upload_submission"])
        self.assertEqual(message["submitted_image_uri"], "some_uri")

        # Test the except block
        mock_requests_get.side_effect = Exception("Failed to get input_file")
        with self.assertLogs("jobs.utils", level="ERROR") as cm:
            message = handle_submission_rerun(mock_submission, "resumed")
            self.assertIn("Failed to get input_file", cm.output[0])
            self.assertIsNone(message)

        # Test the line 234
        mock_submission.challenge_phase.challenge.is_static_dataset_code_upload = (
            True
        )
        mock_requests_get.side_effect = None
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "submitted_image_uri": "some_uri"
        }

        message = handle_submission_rerun(mock_submission, "resumed")
        self.assertTrue(message["is_static_dataset_code_upload_submission"])


class TestGetLeaderboardDataModel(TestCase):
    @mock.patch("jobs.utils.LeaderboardData.objects.get")
    def test_get_leaderboard_data_model(self, mock_get):
        # Arrange
        mock_leaderboard_data = mock.Mock()
        mock_get.return_value = mock_leaderboard_data
        submission_pk = 1
        challenge_phase_split_pk = 2

        # Act
        result = get_leaderboard_data_model(
            submission_pk, challenge_phase_split_pk
        )

        # Assert
        mock_get.assert_called_once_with(
            submission=submission_pk,
            challenge_phase_split__pk=challenge_phase_split_pk,
            is_disabled=False,
        )
        self.assertEqual(result, mock_leaderboard_data)


class TestReorderSubmissionsComparator(TestCase):
    def setUp(self):
        self.user = Mock()
        self.challenge_obj = Mock()
        self.challenge_phase_split = Mock()
        self.leaderboard = Mock()
        self.challenge_phase_split.leaderboard = self.leaderboard
        self.leaderboard.schema = {
            "default_order_by": "score",
            "labels": ["score", "time"],
            "metadata": {"score": {"sort_ascending": False}},
        }
        self.challenge_obj.creator.get_all_challenge_host_email.return_value = [
            "host@example.com"
        ]
        self.challenge_obj.banned_email_ids = ["banned@example.com"]
        self.challenge_phase_split.challenge_phase.is_public = True
        self.challenge_phase_split.visibility = Mock()
        self.challenge_phase_split.show_execution_time = False
        self.challenge_phase_split.show_leaderboard_by_latest_submission = (
            False
        )

    @patch("challenges.models.LeaderboardData.objects")
    @patch("hosts.utils.is_user_a_staff_or_host")
    def test_banned_email_ids(
        self, mock_is_user_a_staff_or_host, mock_leaderboard_data_objects
    ):
        mock_is_user_a_staff_or_host.return_value = False
        mock_leaderboard_data_objects.exclude.return_value.filter.return_value.order_by.return_value = [
            {
                "submission__participant_team": 1,
                "error": None,
                "filtering_score": 10,
                "result": {"score": 10, "time": 5},
            }
        ]
        ParticipantTeam = Mock()
        ParticipantTeam.objects.get.return_value.get_all_participants_email.return_value = [
            "banned@example.com"
        ]

        with patch("challenges.models.ParticipantTeam", ParticipantTeam):
            result, status_code = calculate_distinct_sorted_leaderboard_data(
                self.user,
                self.challenge_obj,
                self.challenge_phase_split,
                False,
                "score",
            )

        self.assertEqual(status_code, 200)
        self.assertEqual(result, [])

    @patch("challenges.models.LeaderboardData.objects")
    @patch("hosts.utils.is_user_a_staff_or_host")
    def test_team_in_all_banned_participant_team(
        self, mock_is_user_a_staff_or_host, mock_leaderboard_data_objects
    ):
        mock_is_user_a_staff_or_host.return_value = False
        mock_leaderboard_data_objects.exclude.return_value.filter.return_value.order_by.return_value = [
            {
                "submission__participant_team": 1,
                "error": None,
                "filtering_score": 10,
                "result": {"score": 10, "time": 5},
            }
        ]
        ParticipantTeam = Mock()
        ParticipantTeam.objects.get.return_value.get_all_participants_email.return_value = [
            "banned@example.com"
        ]

        with patch("challenges.models.ParticipantTeam", ParticipantTeam):
            result, status_code = calculate_distinct_sorted_leaderboard_data(
                self.user,
                self.challenge_obj,
                self.challenge_phase_split,
                False,
                "score",
            )

        self.assertEqual(status_code, 200)
        self.assertEqual(result, [])

    def test_all_comparisons(self):
        def dummy_comparator(a, b):
            return a - b

        KeyClass = reorder_submissions_comparator_to_key(dummy_comparator)
        key1 = KeyClass(5)
        key2 = KeyClass(5)
        key3 = KeyClass(4)
        key4 = KeyClass(6)

        # __eq__
        self.assertTrue(key1 == key2)
        self.assertFalse(key1 == key3)

        # __ne__
        self.assertFalse(key1 != key2)
        self.assertTrue(key1 != key3)

        # __lt__
        self.assertTrue(key1 < key2)
        self.assertFalse(key1 < key3)

        # __le__
        self.assertTrue(key1 <= key2)
        self.assertFalse(key1 <= key3)

        # __gt__
        self.assertFalse(key1 > key2)
        self.assertTrue(key4 > key1)

        # __ge__
        self.assertTrue(key1 >= key2)
        self.assertTrue(key4 >= key1)
        self.assertFalse(key3 >= key1)


class Submission:
    SUBMITTED = "SUBMITTED"
    SUBMITTING = "SUBMITTING"
    RESUMING = "RESUMING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"

    def __init__(self, status, submitted_at):
        self.status = status
        self.submitted_at = submitted_at


def reorder_submissions_comparator(submission_1, submission_2):
    submissions_in_progress_status = [
        Submission.SUBMITTED,
        Submission.SUBMITTING,
        Submission.RESUMING,
        Submission.QUEUED,
        Submission.RUNNING,
    ]
    if (
        submission_1.status in submissions_in_progress_status
        and submission_2.status in submissions_in_progress_status
    ):
        return (submission_1.submitted_at > submission_2.submitted_at) - (
            submission_1.submitted_at < submission_2.submitted_at
        )
    return (submission_1.submitted_at < submission_2.submitted_at) - (
        submission_1.submitted_at > submission_2.submitted_at
    )
