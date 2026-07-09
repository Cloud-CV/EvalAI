import os
import shutil
from datetime import timedelta
from unittest.mock import patch

from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from jobs.queue_timeout import (
    fail_stuck_submissions,
    get_stuck_submission_queryset,
    is_submission_queue_timed_out,
)
from jobs.tasks import fail_stuck_submissions_task
from participants.models import ParticipantTeam


class QueueTimeoutBaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="user", email="user@test.com", password="password"
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            submission_queue_time_limit=7200,
        )

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
            )

    def tearDown(self):
        shutil.rmtree("/tmp/evalai", ignore_errors=True)

    def _create_submission(self, status=Submission.SUBMITTED, submitted_at=None):
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            submission = Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=status,
                input_file=self.challenge_phase.test_annotation,
                is_public=True,
            )
        if submitted_at is not None:
            Submission.objects.filter(pk=submission.pk).update(
                submitted_at=submitted_at
            )
            submission.refresh_from_db()
        return submission


class TestIsSubmissionQueueTimedOut(QueueTimeoutBaseTestCase):
    def test_returns_false_when_within_limit(self):
        submission = self._create_submission(
            submitted_at=timezone.now() - timedelta(hours=1)
        )

        self.assertFalse(is_submission_queue_timed_out(submission))

    def test_returns_true_when_past_limit(self):
        submission = self._create_submission(
            submitted_at=timezone.now() - timedelta(hours=3)
        )

        self.assertTrue(is_submission_queue_timed_out(submission))

    def test_returns_false_when_disabled_for_challenge(self):
        self.challenge.submission_queue_time_limit = 0
        self.challenge.save()
        submission = self._create_submission(
            submitted_at=timezone.now() - timedelta(hours=10)
        )

        self.assertFalse(is_submission_queue_timed_out(submission))

    def test_uses_rerun_resumed_at_when_present(self):
        submission = self._create_submission(
            submitted_at=timezone.now() - timedelta(hours=10)
        )
        resumed_at = timezone.now() - timedelta(minutes=30)
        Submission.objects.filter(pk=submission.pk).update(
            rerun_resumed_at=resumed_at
        )
        submission.refresh_from_db()

        self.assertFalse(is_submission_queue_timed_out(submission))


class TestFailStuckSubmissions(QueueTimeoutBaseTestCase):
    @patch("jobs.queue_timeout.trigger_eks_node_autoscale")
    def test_fails_old_submitted_submission(self, mock_autoscale):
        submission = self._create_submission(
            submitted_at=timezone.now() - timedelta(hours=3)
        )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            failed_count = fail_stuck_submissions()

        self.assertEqual(failed_count, 1)
        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.FAILED)
        self.assertIsNotNone(submission.completed_at)
        self.assertTrue(submission.stderr_file)
        mock_autoscale.assert_called_once()

    @patch("jobs.queue_timeout.trigger_eks_node_autoscale")
    def test_skips_recent_submission(self, mock_autoscale):
        self._create_submission(submitted_at=timezone.now() - timedelta(minutes=30))

        failed_count = fail_stuck_submissions()

        self.assertEqual(failed_count, 0)
        mock_autoscale.assert_not_called()

    @patch("jobs.queue_timeout.trigger_eks_node_autoscale")
    def test_dry_run_does_not_update_submission(self, mock_autoscale):
        submission = self._create_submission(
            submitted_at=timezone.now() - timedelta(hours=3)
        )

        failed_count = fail_stuck_submissions(dry_run=True)

        self.assertEqual(failed_count, 1)
        submission.refresh_from_db()
        self.assertEqual(submission.status, Submission.SUBMITTED)
        mock_autoscale.assert_not_called()

    @patch("jobs.queue_timeout.trigger_eks_node_autoscale")
    def test_filters_by_challenge_pk(self, mock_autoscale):
        other_challenge = Challenge.objects.create(
            title="Other Challenge",
            description="Description",
            terms_and_conditions="Terms",
            submission_guidelines="Guidelines",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            submission_queue_time_limit=7200,
        )
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            other_phase = ChallengePhase.objects.create(
                name="Other Phase",
                description="Description",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=other_challenge,
                test_annotation=SimpleUploadedFile(
                    "other.txt", b"content", content_type="text/plain"
                ),
            )
            other_submission = Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=other_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=other_phase.test_annotation,
            )
        Submission.objects.filter(pk=other_submission.pk).update(
            submitted_at=timezone.now() - timedelta(hours=3)
        )

        stuck_submission = self._create_submission(
            submitted_at=timezone.now() - timedelta(hours=3)
        )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            failed_count = fail_stuck_submissions(challenge_pk=self.challenge.pk)

        self.assertEqual(failed_count, 1)
        stuck_submission.refresh_from_db()
        other_submission.refresh_from_db()
        self.assertEqual(stuck_submission.status, Submission.FAILED)
        self.assertEqual(other_submission.status, Submission.SUBMITTED)

    def test_get_stuck_submission_queryset_includes_queue_states(self):
        submitted = self._create_submission(status=Submission.SUBMITTED)
        queued = self._create_submission(status=Submission.QUEUED)
        running = self._create_submission(status=Submission.RUNNING)

        stuck_pks = set(
            get_stuck_submission_queryset().values_list("pk", flat=True)
        )

        self.assertIn(submitted.pk, stuck_pks)
        self.assertIn(queued.pk, stuck_pks)
        self.assertNotIn(running.pk, stuck_pks)


class TestFailStuckSubmissionsTask(QueueTimeoutBaseTestCase):
    @patch("jobs.queue_timeout.fail_stuck_submissions", return_value=2)
    def test_task_delegates_to_helper(self, mock_fail):
        result = fail_stuck_submissions_task()

        self.assertEqual(result, 2)
        mock_fail.assert_called_once_with()
