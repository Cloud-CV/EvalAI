from io import StringIO
from unittest.mock import patch
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from participants.models import ParticipantTeam


class ManageRetentionCommandTest(TestCase):
    """Test the manage_retention management command"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass"
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Host Team", created_by=self.user
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Test Description",
            terms_and_conditions="Test Terms",
            submission_guidelines="Test Guidelines",
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
        )

        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            description="Test Phase Description",
            leaderboard_public=True,
            start_date=timezone.now() - timezone.timedelta(days=15),
            end_date=timezone.now() - timezone.timedelta(days=5),
            challenge=self.challenge,
            test_annotation="test_annotation.txt",
            is_public=False,
            max_submissions_per_day=5,
            max_submissions_per_month=50,
            max_submissions=100,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Participant Team", created_by=self.user
        )

    def test_manage_retention_no_action(self):
        """Test command with no action specified"""
        out = StringIO()
        call_command("manage_retention", stdout=out)

        # Should show help when no action is provided
        self.assertIn("usage", out.getvalue().lower())

    @patch("challenges.aws_utils.cleanup_expired_submission_artifacts")
    def test_manage_retention_cleanup_action(self, mock_cleanup):
        """Test cleanup action"""
        mock_cleanup.return_value = {
            "total_processed": 5,
            "successful_deletions": 4,
            "failed_deletions": 1,
            "errors": [{"submission_id": 123, "error": "Test error"}],
        }

        out = StringIO()
        call_command("manage_retention", "cleanup", stdout=out)

        mock_cleanup.assert_called_once()
        output = out.getvalue()
        self.assertIn("4 submissions successfully cleaned up", output)
        self.assertIn("1 failed deletions", output)

    @patch("challenges.aws_utils.cleanup_expired_submission_artifacts")
    def test_manage_retention_cleanup_dry_run(self, mock_cleanup):
        """Test cleanup action with dry run"""
        # Create eligible submissions
        Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            retention_eligible_date=timezone.now()
            - timezone.timedelta(days=1),
            is_artifact_deleted=False,
        )

        out = StringIO()
        call_command("manage_retention", "cleanup", "--dry-run", stdout=out)

        # Should not call the actual cleanup function
        mock_cleanup.assert_not_called()

        output = out.getvalue()
        self.assertIn("DRY RUN", output)
        self.assertIn("1 submissions would be cleaned up", output)

    @patch("challenges.aws_utils.update_submission_retention_dates")
    def test_manage_retention_update_dates_action(self, mock_update):
        """Test update-dates action"""
        mock_update.return_value = {"updated_submissions": 10, "errors": []}

        out = StringIO()
        call_command("manage_retention", "update-dates", stdout=out)

        mock_update.assert_called_once()
        output = out.getvalue()
        self.assertIn("Updated retention dates for 10 submissions", output)

    @patch("challenges.aws_utils.update_submission_retention_dates")
    def test_manage_retention_update_dates_with_errors(self, mock_update):
        """Test update-dates action with errors"""
        mock_update.return_value = {
            "updated_submissions": 8,
            "errors": [
                {"phase_id": 1, "challenge_id": 1, "error": "Test error 1"},
                {"phase_id": 2, "challenge_id": 1, "error": "Test error 2"},
            ],
        }

        out = StringIO()
        err = StringIO()
        call_command(
            "manage_retention", "update-dates", stdout=out, stderr=err
        )

        mock_update.assert_called_once()
        output = out.getvalue()
        error_output = err.getvalue()

        self.assertIn("Updated retention dates for 8 submissions", output)
        self.assertIn("2 errors occurred", error_output)

    @patch("challenges.aws_utils.send_retention_warning_notifications")
    def test_manage_retention_send_warnings_action(self, mock_send_warnings):
        """Test send-warnings action"""
        mock_send_warnings.return_value = {
            "notifications_sent": 3,
            "errors": [],
        }

        out = StringIO()
        call_command("manage_retention", "send-warnings", stdout=out)

        mock_send_warnings.assert_called_once()
        output = out.getvalue()
        self.assertIn("Sent 3 retention warning notifications", output)

    @patch("challenges.aws_utils.set_cloudwatch_log_retention")
    def test_manage_retention_set_log_retention_success(
        self, mock_set_retention
    ):
        """Test set-log-retention action - success"""
        mock_set_retention.return_value = {
            "success": True,
            "retention_days": 30,
            "log_group": f"/aws/ecs/challenge-{self.challenge.pk}",
        }

        out = StringIO()
        call_command(
            "manage_retention",
            "set-log-retention",
            str(self.challenge.pk),
            stdout=out,
        )

        mock_set_retention.assert_called_once_with(self.challenge.pk, None)
        output = out.getvalue()
        self.assertIn("Successfully set log retention to 30 days", output)

    @patch("challenges.aws_utils.set_cloudwatch_log_retention")
    def test_manage_retention_set_log_retention_with_days(
        self, mock_set_retention
    ):
        """Test set-log-retention action with custom days"""
        mock_set_retention.return_value = {
            "success": True,
            "retention_days": 90,
            "log_group": f"/aws/ecs/challenge-{self.challenge.pk}",
        }

        out = StringIO()
        call_command(
            "manage_retention",
            "set-log-retention",
            str(self.challenge.pk),
            "--days",
            "90",
            stdout=out,
        )

        mock_set_retention.assert_called_once_with(self.challenge.pk, 90)
        output = out.getvalue()
        self.assertIn("Successfully set log retention to 90 days", output)

    @patch("challenges.aws_utils.set_cloudwatch_log_retention")
    def test_manage_retention_set_log_retention_failure(
        self, mock_set_retention
    ):
        """Test set-log-retention action - failure"""
        mock_set_retention.return_value = {
            "success": False,
            "error": "AWS Error: Access denied",
        }

        err = StringIO()
        call_command(
            "manage_retention",
            "set-log-retention",
            str(self.challenge.pk),
            stderr=err,
        )

        mock_set_retention.assert_called_once_with(self.challenge.pk, None)
        error_output = err.getvalue()
        self.assertIn(
            "Failed to set log retention: AWS Error: Access denied",
            error_output,
        )

    def test_manage_retention_set_log_retention_invalid_challenge(self):
        """Test set-log-retention action with invalid challenge ID"""
        err = StringIO()

        with self.assertRaises(CommandError):
            call_command(
                "manage_retention", "set-log-retention", "99999", stderr=err
            )

    @patch("challenges.aws_utils.delete_submission_files_from_storage")
    def test_manage_retention_force_delete_success(self, mock_delete):
        """Test force-delete action - success"""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )

        mock_delete.return_value = {
            "success": True,
            "deleted_files": ["file1.zip", "file2.txt"],
            "failed_files": [],
            "submission_id": submission.pk,
        }

        out = StringIO()
        call_command(
            "manage_retention",
            "force-delete",
            str(submission.pk),
            "--confirm",
            stdout=out,
        )

        mock_delete.assert_called_once_with(submission)
        output = out.getvalue()
        self.assertIn("Successfully deleted submission artifacts", output)
        self.assertIn("2 files deleted", output)

    @patch("challenges.aws_utils.delete_submission_files_from_storage")
    def test_manage_retention_force_delete_without_confirm(self, mock_delete):
        """Test force-delete action without confirmation"""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )

        err = StringIO()
        call_command(
            "manage_retention", "force-delete", str(submission.pk), stderr=err
        )

        # Should not call delete function without confirmation
        mock_delete.assert_not_called()
        error_output = err.getvalue()
        self.assertIn("This action is irreversible", error_output)

    def test_manage_retention_force_delete_invalid_submission(self):
        """Test force-delete action with invalid submission ID"""
        err = StringIO()

        with self.assertRaises(CommandError):
            call_command(
                "manage_retention",
                "force-delete",
                "99999",
                "--confirm",
                stderr=err,
            )

    def test_manage_retention_status_action_specific_challenge(self):
        """Test status action for specific challenge"""
        out = StringIO()
        call_command(
            "manage_retention",
            "status",
            "--challenge-id",
            str(self.challenge.pk),
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn(
            f"Retention status for challenge: {self.challenge.title}", output
        )
        self.assertIn("Test Phase", output)

    def test_manage_retention_status_action_overall(self):
        """Test status action for overall retention status"""
        # Create some test submissions
        Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            retention_eligible_date=timezone.now()
            - timezone.timedelta(days=1),
            is_artifact_deleted=False,
        )

        Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            retention_eligible_date=timezone.now()
            + timezone.timedelta(days=10),
            is_artifact_deleted=False,
        )

        out = StringIO()
        call_command("manage_retention", "status", stdout=out)

        output = out.getvalue()
        self.assertIn("Overall retention status", output)
        self.assertIn("Submissions eligible for cleanup now: 1", output)
        self.assertIn(
            "Submissions eligible for cleanup in next 30 days: 1", output
        )

    def test_cleanup_subcommand_success(self):
        """Test cleanup subcommand with successful cleanup"""
        # Create a submission eligible for cleanup
        Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            retention_eligible_date=timezone.now()
            - timezone.timedelta(days=1),
            is_artifact_deleted=False,
        )

        with patch(
            "challenges.aws_utils.cleanup_expired_submission_artifacts"
        ) as mock_cleanup:
            mock_cleanup.return_value = {
                "total_processed": 1,
                "successful_deletions": 1,
                "failed_deletions": 0,
                "errors": [],
            }

            call_command("manage_retention", "cleanup")
            mock_cleanup.assert_called_once()
