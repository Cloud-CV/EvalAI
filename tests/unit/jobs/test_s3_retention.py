from datetime import timedelta
from unittest.mock import MagicMock, patch

from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from jobs.s3_retention import (
    backfill_submission_artifact_tags,
    build_submission_artifact_s3_tags,
    get_submission_artifact_s3_key,
    tag_submission_artifacts_for_retention,
)
from participants.models import ParticipantTeam


class S3RetentionTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="user", email="user@test.com", password="password"
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
            challenge_usage_type=Challenge.INTERNAL,
        )
        self.challenge_phase = ChallengePhase.objects.create(
            name="Challenge Phase",
            description="Description for Challenge Phase",
            leaderboard_public=False,
            is_public=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            challenge=self.challenge,
            max_submissions_per_day=100000,
            max_submissions=100000,
            submission_artifact_retention_policy=ChallengePhase.DAYS_14,
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user
        )
        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            input_file=SimpleUploadedFile(
                "submission.json",
                b"{}",
                content_type="application/json",
            ),
            is_public=True,
        )

    def test_build_submission_artifact_s3_tags_uses_phase_policy(self):
        tags = build_submission_artifact_s3_tags(self.submission)

        self.assertEqual("submission", tags["evalai-object-type"])
        self.assertEqual(str(self.challenge.pk), tags["challenge-id"])
        self.assertEqual(
            str(self.challenge_phase.pk), tags["challenge-phase-id"]
        )
        self.assertEqual(ChallengePhase.DAYS_14, tags["retention-tier"])

    def test_get_submission_artifact_s3_key_adds_media_prefix(self):
        key = get_submission_artifact_s3_key(
            "submission_files/submission_1/file.json"
        )

        self.assertEqual("media/submission_files/submission_1/file.json", key)

    def test_backfill_dry_run_reports_tags_without_calling_s3(self):
        s3_client = MagicMock()

        summary = backfill_submission_artifact_tags(
            challenge_phase_ids=[self.challenge_phase.pk],
            dry_run=True,
            s3_client=s3_client,
            bucket_name="test-bucket",
        )

        self.assertEqual(1, summary["submissions_seen"])
        self.assertEqual(1, summary["objects_seen"])
        self.assertEqual(1, summary["objects_to_tag"])
        self.assertEqual(0, summary["objects_tagged"])
        s3_client.put_object_tagging.assert_not_called()

    def test_backfill_execute_applies_expected_tag_set(self):
        s3_client = MagicMock()

        summary = backfill_submission_artifact_tags(
            challenge_phase_ids=[self.challenge_phase.pk],
            dry_run=False,
            s3_client=s3_client,
            bucket_name="test-bucket",
        )

        self.assertEqual(1, summary["objects_tagged"])
        s3_client.put_object_tagging.assert_called_once()
        _, kwargs = s3_client.put_object_tagging.call_args
        self.assertEqual("test-bucket", kwargs["Bucket"])
        self.assertEqual(
            get_submission_artifact_s3_key(self.submission.input_file.name),
            kwargs["Key"],
        )
        self.assertIn(
            {"Key": "retention-tier", "Value": ChallengePhase.DAYS_14},
            kwargs["Tagging"]["TagSet"],
        )

    def test_tag_submission_artifacts_skips_test_mode(self):
        with self.settings(TEST=True), patch(
            "jobs.s3_retention.boto3.client"
        ) as mock_client:
            tag_submission_artifacts_for_retention(
                self.submission,
                [self.submission.input_file.name],
            )

        mock_client.assert_not_called()
