import os
import shutil
from datetime import timedelta
from unittest.mock import patch

import pytest
import rest_framework
from challenges.aws_utils import calculate_submission_retention_date
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from participants.models import ParticipantTeam


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="user", email="user@test.com", password="password"
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge", created_by=self.user
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
        shutil.rmtree("/tmp/evalai")


class SubmissionTestCase(BaseTestCase):
    def setUp(self):
        super(SubmissionTestCase, self).setUp()

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            is_public=True,
        )

    def test__str__(self):
        self.assertEqual(
            "{}".format(self.submission.id), self.submission.__str__()
        )


@pytest.mark.django_db
class TestSubmissionModel:
    def setup_method(self, method):
        self.user = User.objects.create_user(
            username="testuser", password="password"
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
        )
        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            challenge=self.challenge,
            max_submissions=2,
            max_submissions_per_day=2,
            max_submissions_per_month=2,
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Participant Team", created_by=self.user
        )

    def test_max_submissions_per_day_reached(self):
        Submission.objects.all().delete()

        self.challenge_phase.max_submissions = 100
        self.challenge_phase.max_submissions_per_day = 2
        self.challenge_phase.max_submissions_per_month = 100
        self.challenge_phase.save()

        for _ in range(2):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now(),
            )

        with pytest.raises(
            rest_framework.exceptions.PermissionDenied,
            match=r"The maximum number of submission for today has been reached",
        ):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now(),
            )

    def test_max_submissions_limit_reached(self):
        self.challenge_phase.max_submissions = 2
        self.challenge_phase.max_submissions_per_day = 100
        self.challenge_phase.max_submissions_per_month = 100
        self.challenge_phase.save()

        Submission.objects.all().delete()
        assert Submission.objects.count() == 0

        for _ in range(2):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
            )

        with pytest.raises(
            rest_framework.exceptions.PermissionDenied,
            match=r"The maximum number of submissions has been reached",
        ):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
            )

    def test_max_submissions_per_month_reached(self):
        Submission.objects.all().delete()

        self.challenge_phase.max_submissions = 100
        self.challenge_phase.max_submissions_per_day = 100
        self.challenge_phase.max_submissions_per_month = 2
        self.challenge_phase.save()

        for day in [1, 2]:
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now().replace(day=day),
            )

        with pytest.raises(
            rest_framework.exceptions.PermissionDenied,
            match=r"The maximum number of submission for this month has been reached",
        ):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now().replace(day=3),
            )


class SubmissionRetentionTest(TestCase):
    """Test retention-related functionality in Submission model"""

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
            start_date=timezone.now() - timedelta(days=15),
            end_date=timezone.now() - timedelta(days=5),
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

    def test_submission_retention_fields_defaults(self):
        """Test that retention fields have correct default values"""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )

        # Check default values
        self.assertIsNone(submission.retention_eligible_date)
        self.assertFalse(submission.is_artifact_deleted)
        self.assertIsNone(submission.artifact_deletion_date)

    def test_submission_retention_eligible_date_setting(self):
        """Test setting retention eligible date"""
        retention_date = timezone.now() + timedelta(days=30)

        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            retention_eligible_date=retention_date,
        )

        self.assertEqual(submission.retention_eligible_date, retention_date)

    def test_submission_artifact_deletion_tracking(self):
        """Test tracking of artifact deletion"""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )

        # Initially not deleted
        self.assertFalse(submission.is_artifact_deleted)
        self.assertIsNone(submission.artifact_deletion_date)

        # Mark as deleted
        deletion_date = timezone.now()
        submission.is_artifact_deleted = True
        submission.artifact_deletion_date = deletion_date
        submission.save()

        # Verify tracking
        submission.refresh_from_db()
        self.assertTrue(submission.is_artifact_deleted)
        self.assertEqual(submission.artifact_deletion_date, deletion_date)

    def test_submission_retention_queryset_filtering(self):
        """Test filtering submissions by retention status"""
        # Create submissions with different retention statuses
        eligible_submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            retention_eligible_date=timezone.now() - timedelta(days=1),
            is_artifact_deleted=False,
        )

        Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            retention_eligible_date=timezone.now() + timedelta(days=10),
            is_artifact_deleted=False,
        )

        already_deleted_submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            retention_eligible_date=timezone.now() - timedelta(days=1),
            is_artifact_deleted=True,
        )

        # Test filtering for eligible submissions
        eligible_submissions = Submission.objects.filter(
            retention_eligible_date__lte=timezone.now(),
            is_artifact_deleted=False,
        )

        self.assertEqual(eligible_submissions.count(), 1)
        self.assertEqual(eligible_submissions.first(), eligible_submission)

        # Test filtering for deleted submissions
        deleted_submissions = Submission.objects.filter(
            is_artifact_deleted=True
        )
        self.assertEqual(deleted_submissions.count(), 1)
        self.assertEqual(
            deleted_submissions.first(), already_deleted_submission
        )

    def test_submission_retention_field_constraints(self):
        """Test retention field constraints and validation"""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )

        # Test that deletion date can only be set when is_artifact_deleted is True
        submission.is_artifact_deleted = False
        submission.artifact_deletion_date = timezone.now()
        submission.save()

        # This should be allowed (business logic, not database constraint)
        submission.refresh_from_db()
        self.assertIsNotNone(submission.artifact_deletion_date)

        # Test that retention_eligible_date can be in the future
        future_date = timezone.now() + timedelta(days=60)
        submission.retention_eligible_date = future_date
        submission.save()

        submission.refresh_from_db()
        self.assertEqual(submission.retention_eligible_date, future_date)


class SubmissionRetentionModelMetaTest(TestCase):
    """Additional tests for retention field metadata (indexes & help_text)."""

    def test_retention_field_metadata(self):
        field = Submission._meta.get_field("retention_eligible_date")
        artifact_deleted_field = Submission._meta.get_field(
            "is_artifact_deleted"
        )
        deletion_date_field = Submission._meta.get_field(
            "artifact_deletion_date"
        )

        # Indexes
        self.assertTrue(field.db_index)
        self.assertTrue(artifact_deleted_field.db_index)

        # Help text
        self.assertEqual(
            field.help_text,
            "Date when submission artifacts become eligible for deletion",
        )
        self.assertEqual(
            artifact_deleted_field.help_text,
            "Flag indicating whether submission artifacts have been deleted",
        )
        self.assertEqual(
            deletion_date_field.help_text,
            "Timestamp when submission artifacts were deleted",
        )


class SubmissionRetentionCalculationTest(TestCase):
    """Unit tests for calculate_submission_retention_date helper."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="calcuser", email="calc@example.com", password="pass"
        )
        self.host_team = ChallengeHostTeam.objects.create(
            team_name="Calc Host Team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Calc Challenge",
            description="Desc",
            terms_and_conditions="T&C",
            submission_guidelines="Guide",
            creator=self.host_team,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
        )

    def _create_phase(self, **kwargs):
        defaults = dict(
            name="Phase",
            description="Desc",
            leaderboard_public=True,
            start_date=timezone.now() - timedelta(days=15),
            challenge=self.challenge,
            test_annotation="ta.txt",
            max_submissions_per_day=5,
            max_submissions_per_month=50,
            max_submissions=100,
        )
        defaults.update(kwargs)
        return ChallengePhase.objects.create(**defaults)

    def test_ended_private_phase(self):
        end_date = timezone.now() - timedelta(days=5)
        phase = self._create_phase(end_date=end_date, is_public=False)
        expected = end_date + timedelta(days=30)
        self.assertEqual(calculate_submission_retention_date(phase), expected)

    def test_public_phase_returns_none(self):
        phase = self._create_phase(
            end_date=timezone.now() - timedelta(days=5), is_public=True
        )
        self.assertIsNone(calculate_submission_retention_date(phase))

    def test_no_end_date_returns_none(self):
        phase = self._create_phase(end_date=None, is_public=False)
        self.assertIsNone(calculate_submission_retention_date(phase))

    def test_future_end_date(self):
        end_date = timezone.now() + timedelta(days=10)
        phase = self._create_phase(end_date=end_date, is_public=False)
        expected = end_date + timedelta(days=30)
        self.assertEqual(calculate_submission_retention_date(phase), expected)


class SubmissionRetentionSignalTest(TestCase):
    """Tests for signal-based automatic retention updates."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="signaluser", email="signal@example.com", password="pass"
        )
        self.host_team = ChallengeHostTeam.objects.create(
            team_name="Signal Host Team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Signal Challenge",
            description="Desc",
            terms_and_conditions="T&C",
            submission_guidelines="Guide",
            creator=self.host_team,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
        )
        self.team = ParticipantTeam.objects.create(
            team_name="Signal Participant", created_by=self.user
        )

    def _create_phase(self, **kwargs):
        defaults = dict(
            name="Phase",
            description="Desc",
            leaderboard_public=True,
            start_date=timezone.now() - timedelta(days=10),
            challenge=self.challenge,
            test_annotation="ta.txt",
            max_submissions_per_day=5,
            max_submissions_per_month=50,
            max_submissions=100,
        )
        defaults.update(kwargs)
        return ChallengePhase.objects.create(**defaults)

    def _create_submission(self, phase):
        return Submission.objects.create(
            participant_team=self.team,
            challenge_phase=phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )

    def test_initial_retention_set_on_create(self):
        end_date = timezone.now() + timedelta(days=5)
        phase = self._create_phase(end_date=end_date, is_public=False)
        sub = self._create_submission(phase)
        sub.refresh_from_db()
        self.assertEqual(
            sub.retention_eligible_date, end_date + timedelta(days=30)
        )

    def test_no_retention_for_public_phase(self):
        phase = self._create_phase(
            end_date=timezone.now() - timedelta(days=5), is_public=True
        )
        sub = self._create_submission(phase)
        sub.refresh_from_db()
        self.assertIsNone(sub.retention_eligible_date)

    @patch("challenges.signals.logger")
    def test_retention_updates_on_end_date_change(self, mock_logger):
        phase = self._create_phase(
            end_date=timezone.now() + timedelta(days=5), is_public=False
        )
        sub = self._create_submission(phase)
        new_end = timezone.now() + timedelta(days=15)
        phase.end_date = new_end
        phase.save()
        sub.refresh_from_db()
        self.assertEqual(
            sub.retention_eligible_date, new_end + timedelta(days=30)
        )
        mock_logger.info.assert_called()

    @patch("challenges.signals.logger")
    def test_retention_cleared_when_phase_becomes_public(self, mock_logger):
        phase = self._create_phase(
            end_date=timezone.now() - timedelta(days=5), is_public=False
        )
        sub = self._create_submission(phase)
        phase.is_public = True
        phase.save()
        sub.refresh_from_db()
        self.assertIsNone(sub.retention_eligible_date)
        mock_logger.info.assert_called()
