"""
Tests for stale submission handling functionality.

This module tests the following:
1. Management command to handle stale submissions
2. API endpoint to get and manage stale submissions
3. Utility functions for detecting and handling stale submissions
"""

from datetime import timedelta
from unittest.mock import patch, MagicMock

from allauth.account.models import EmailAddress
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse_lazy
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from io import StringIO
from jobs.models import Submission
from jobs.utils import (
    fail_stale_submission,
    get_stale_submissions,
    requeue_submission,
)
from participants.models import Participant, ParticipantTeam
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class TestGetStaleSubmissions(TestCase):
    """Tests for the get_stale_submissions utility function."""

    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            email="test@test.com",
            password="testpass",
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Host Team",
            created_by=self.user,
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=10),
            published=True,
        )

        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            description="Test description",
            challenge=self.challenge,
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=5),
            max_submissions_per_day=10,
            max_submissions_per_month=100,
            max_submissions=1000,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Team",
            created_by=self.user,
        )

        Participant.objects.create(
            user=self.user,
            team=self.participant_team,
            status=Participant.SELF,
        )

    def _create_submission(self, status, hours_ago):
        """Helper to create a submission with a specific status and age."""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=status,
        )
        # Update submitted_at to the desired time
        Submission.objects.filter(pk=submission.pk).update(
            submitted_at=timezone.now() - timedelta(hours=hours_ago)
        )
        return Submission.objects.get(pk=submission.pk)

    def test_no_stale_submissions(self):
        """Test that recent submissions are not marked as stale."""
        # Create a recent submission
        self._create_submission(Submission.SUBMITTED, hours_ago=1)

        stale = get_stale_submissions(timeout_hours=24)
        self.assertEqual(stale.count(), 0)

    def test_stale_submitted_submission(self):
        """Test that old submissions in SUBMITTED status are detected."""
        self._create_submission(Submission.SUBMITTED, hours_ago=48)

        stale = get_stale_submissions(timeout_hours=24)
        self.assertEqual(stale.count(), 1)
        self.assertEqual(stale.first().status, Submission.SUBMITTED)

    def test_stale_running_submission(self):
        """Test that old submissions in RUNNING status are detected."""
        self._create_submission(Submission.RUNNING, hours_ago=48)

        stale = get_stale_submissions(timeout_hours=24)
        self.assertEqual(stale.count(), 1)
        self.assertEqual(stale.first().status, Submission.RUNNING)

    def test_finished_submissions_not_stale(self):
        """Test that finished submissions are not marked as stale."""
        self._create_submission(Submission.FINISHED, hours_ago=48)

        stale = get_stale_submissions(timeout_hours=24)
        self.assertEqual(stale.count(), 0)

    def test_failed_submissions_not_stale(self):
        """Test that failed submissions are not marked as stale."""
        self._create_submission(Submission.FAILED, hours_ago=48)

        stale = get_stale_submissions(timeout_hours=24)
        self.assertEqual(stale.count(), 0)

    def test_filter_by_challenge(self):
        """Test filtering stale submissions by challenge."""
        # Create stale submission for our challenge
        self._create_submission(Submission.SUBMITTED, hours_ago=48)

        # Create another challenge and submission
        other_challenge = Challenge.objects.create(
            title="Other Challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=10),
        )
        other_phase = ChallengePhase.objects.create(
            name="Other Phase",
            challenge=other_challenge,
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=5),
            max_submissions_per_day=10,
            max_submissions_per_month=100,
            max_submissions=1000,
        )
        other_submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=other_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )
        Submission.objects.filter(pk=other_submission.pk).update(
            submitted_at=timezone.now() - timedelta(hours=48)
        )

        # Filter by original challenge
        stale = get_stale_submissions(
            timeout_hours=24, challenge_id=self.challenge.pk
        )
        self.assertEqual(stale.count(), 1)
        self.assertEqual(
            stale.first().challenge_phase.challenge.pk, self.challenge.pk
        )

    def test_custom_timeout(self):
        """Test that custom timeout values work correctly."""
        self._create_submission(Submission.SUBMITTED, hours_ago=12)

        # With 24 hour timeout, should not be stale
        stale = get_stale_submissions(timeout_hours=24)
        self.assertEqual(stale.count(), 0)

        # With 6 hour timeout, should be stale
        stale = get_stale_submissions(timeout_hours=6)
        self.assertEqual(stale.count(), 1)


class TestRequeueSubmission(TestCase):
    """Tests for the requeue_submission utility function."""

    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            email="test@test.com",
            password="testpass",
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Host Team",
            created_by=self.user,
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=10),
            published=True,
        )

        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            description="Test description",
            challenge=self.challenge,
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=5),
            max_submissions_per_day=10,
            max_submissions_per_month=100,
            max_submissions=1000,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Team",
            created_by=self.user,
        )

        Participant.objects.create(
            user=self.user,
            team=self.participant_team,
            status=Participant.SELF,
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.RUNNING,
            started_at=timezone.now() - timedelta(hours=24),
        )

    @patch("jobs.utils.publish_submission_message")
    def test_requeue_submission_success(self, mock_publish):
        """Test that requeue_submission resets status and publishes message."""
        result = requeue_submission(self.submission)

        self.assertTrue(result)

        # Refresh from database
        self.submission.refresh_from_db()

        # Status should be reset to SUBMITTED
        self.assertEqual(self.submission.status, Submission.SUBMITTED)
        self.assertIsNone(self.submission.started_at)

        # Message should be published
        mock_publish.assert_called_once()
        call_args = mock_publish.call_args[0][0]
        self.assertEqual(call_args["challenge_pk"], self.challenge.pk)
        self.assertEqual(call_args["phase_pk"], self.challenge_phase.pk)
        self.assertEqual(call_args["submission_pk"], self.submission.pk)

    @patch("jobs.utils.publish_submission_message")
    def test_requeue_submission_failure(self, mock_publish):
        """Test that requeue_submission handles errors gracefully."""
        mock_publish.side_effect = Exception("Queue error")

        result = requeue_submission(self.submission)

        self.assertFalse(result)


class TestFailStaleSubmission(TestCase):
    """Tests for the fail_stale_submission utility function."""

    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            email="test@test.com",
            password="testpass",
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Host Team",
            created_by=self.user,
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=10),
            published=True,
        )

        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            description="Test description",
            challenge=self.challenge,
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=5),
            max_submissions_per_day=10,
            max_submissions_per_month=100,
            max_submissions=1000,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Team",
            created_by=self.user,
        )

        Participant.objects.create(
            user=self.user,
            team=self.participant_team,
            status=Participant.SELF,
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.RUNNING,
        )

    def test_fail_stale_submission_success(self):
        """Test that fail_stale_submission marks submission as failed."""
        result = fail_stale_submission(self.submission)

        self.assertTrue(result)

        # Refresh from database
        self.submission.refresh_from_db()

        self.assertEqual(self.submission.status, Submission.FAILED)
        self.assertIsNotNone(self.submission.completed_at)
        self.assertIn("timeout", self.submission.output.lower())

    def test_fail_stale_submission_with_reason(self):
        """Test that custom reason is saved in output."""
        reason = "Custom failure reason for testing"
        result = fail_stale_submission(self.submission, reason=reason)

        self.assertTrue(result)

        self.submission.refresh_from_db()
        self.assertEqual(self.submission.output, reason)


class TestHandleStaleSubmissionsCommand(TestCase):
    """Tests for the handle_stale_submissions management command."""

    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            email="test@test.com",
            password="testpass",
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Host Team",
            created_by=self.user,
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=10),
            published=True,
        )

        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            description="Test description",
            challenge=self.challenge,
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=5),
            max_submissions_per_day=10,
            max_submissions_per_month=100,
            max_submissions=1000,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Team",
            created_by=self.user,
        )

        Participant.objects.create(
            user=self.user,
            team=self.participant_team,
            status=Participant.SELF,
        )

    def _create_stale_submission(self, status):
        """Helper to create a stale submission."""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=status,
        )
        Submission.objects.filter(pk=submission.pk).update(
            submitted_at=timezone.now() - timedelta(hours=48)
        )
        return Submission.objects.get(pk=submission.pk)

    def test_command_report_action(self):
        """Test that report action lists stale submissions without changes."""
        submission = self._create_stale_submission(Submission.SUBMITTED)

        out = StringIO()
        call_command(
            "handle_stale_submissions",
            "--timeout-hours=24",
            "--action=report",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("Found 1 stale submission", output)
        self.assertIn(str(submission.id), output)

        # Verify submission wasn't changed
        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.SUBMITTED)

    @patch("jobs.management.commands.handle_stale_submissions.publish_submission_message")
    def test_command_requeue_action(self, mock_publish):
        """Test that requeue action resets and requeues submissions."""
        submission = self._create_stale_submission(Submission.SUBMITTED)

        out = StringIO()
        call_command(
            "handle_stale_submissions",
            "--timeout-hours=24",
            "--action=requeue",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("Successfully requeueed", output)

        # Verify submission was reset
        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.SUBMITTED)

        # Verify message was published
        mock_publish.assert_called()

    def test_command_fail_action(self):
        """Test that fail action marks submissions as failed."""
        submission = self._create_stale_submission(Submission.RUNNING)

        out = StringIO()
        call_command(
            "handle_stale_submissions",
            "--timeout-hours=24",
            "--action=fail",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("Successfully failed", output)

        # Verify submission was marked as failed
        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.FAILED)

    def test_command_dry_run(self):
        """Test that dry-run doesn't modify submissions."""
        submission = self._create_stale_submission(Submission.SUBMITTED)
        original_status = submission.status

        out = StringIO()
        call_command(
            "handle_stale_submissions",
            "--timeout-hours=24",
            "--action=fail",
            "--dry-run",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("[DRY RUN]", output)

        # Verify submission wasn't changed
        submission.refresh_from_db()
        self.assertEqual(submission.status, original_status)

    def test_command_filter_by_challenge(self):
        """Test filtering by challenge ID."""
        self._create_stale_submission(Submission.SUBMITTED)

        out = StringIO()
        call_command(
            "handle_stale_submissions",
            "--timeout-hours=24",
            "--action=report",
            "--challenge-id={}".format(self.challenge.pk),
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("Found 1 stale submission", output)

        # Test with non-existent challenge
        out = StringIO()
        call_command(
            "handle_stale_submissions",
            "--timeout-hours=24",
            "--action=report",
            "--challenge-id=99999",
            stdout=out,
        )

        output = out.getvalue()
        self.assertIn("No stale submissions found", output)


class TestStaleSubmissionsAPI(APITestCase):
    """Tests for the stale submissions API endpoint."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        # Create challenge host user
        self.host_user = User.objects.create(
            username="hostuser",
            email="host@test.com",
            password="testpass",
        )

        EmailAddress.objects.create(
            user=self.host_user,
            email="host@test.com",
            primary=True,
            verified=True,
        )

        # Create regular user
        self.regular_user = User.objects.create(
            username="regularuser",
            email="regular@test.com",
            password="testpass",
        )

        EmailAddress.objects.create(
            user=self.regular_user,
            email="regular@test.com",
            primary=True,
            verified=True,
        )

        # Create challenge host team and challenge
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Host Team",
            created_by=self.host_user,
        )

        ChallengeHost.objects.create(
            user=self.host_user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=10),
            published=True,
        )

        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            description="Test description",
            challenge=self.challenge,
            start_date=timezone.now() - timedelta(days=5),
            end_date=timezone.now() + timedelta(days=5),
            max_submissions_per_day=10,
            max_submissions_per_month=100,
            max_submissions=1000,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Team",
            created_by=self.regular_user,
        )

        Participant.objects.create(
            user=self.regular_user,
            team=self.participant_team,
            status=Participant.SELF,
        )

        self.url = reverse_lazy(
            "jobs:get_stale_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )

    def _create_stale_submission(self, status):
        """Helper to create a stale submission."""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.regular_user,
            status=status,
        )
        Submission.objects.filter(pk=submission.pk).update(
            submitted_at=timezone.now() - timedelta(hours=48)
        )
        return Submission.objects.get(pk=submission.pk)

    def test_get_stale_submissions_as_host(self):
        """Test that challenge host can get stale submissions."""
        submission = self._create_stale_submission(Submission.SUBMITTED)

        self.client.force_authenticate(user=self.host_user)
        response = self.client.get(self.url, {"timeout_hours": 24})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["total_count"], 1)
        self.assertEqual(response.data["submissions"][0]["id"], submission.id)

    def test_get_stale_submissions_as_regular_user(self):
        """Test that regular users cannot access stale submissions."""
        self._create_stale_submission(Submission.SUBMITTED)

        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_stale_submissions_unauthenticated(self):
        """Test that unauthenticated users cannot access stale submissions."""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch("jobs.views.requeue_submission")
    def test_requeue_stale_submissions(self, mock_requeue):
        """Test requeuing stale submissions via API."""
        mock_requeue.return_value = True
        submission = self._create_stale_submission(Submission.SUBMITTED)

        self.client.force_authenticate(user=self.host_user)
        response = self.client.post(
            self.url,
            {
                "submission_ids": [submission.id],
                "action": "requeue",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(submission.id, response.data["results"]["successful"])

    @patch("jobs.views.fail_stale_submission")
    def test_fail_stale_submissions(self, mock_fail):
        """Test failing stale submissions via API."""
        mock_fail.return_value = True
        submission = self._create_stale_submission(Submission.RUNNING)

        self.client.force_authenticate(user=self.host_user)
        response = self.client.post(
            self.url,
            {
                "submission_ids": [submission.id],
                "action": "fail",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn(submission.id, response.data["results"]["successful"])

    def test_post_without_submission_ids(self):
        """Test that POST without submission_ids returns error."""
        self.client.force_authenticate(user=self.host_user)
        response = self.client.post(
            self.url,
            {"action": "requeue"},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_post_with_invalid_action(self):
        """Test that POST with invalid action returns error."""
        submission = self._create_stale_submission(Submission.SUBMITTED)

        self.client.force_authenticate(user=self.host_user)
        response = self.client.post(
            self.url,
            {
                "submission_ids": [submission.id],
                "action": "invalid_action",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
