import os
import shutil
import tempfile
from datetime import timedelta
from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.utils import timezone
from freezegun import freeze_time

from apps.challenges.models import Challenge, ChallengePhase
from apps.hosts.models import ChallengeHostTeam
from apps.jobs.models import Submission
from apps.participants.models import ParticipantTeam


class BaseTestCase(TestCase):
    """Base test case with common setup for cleanup submissions tests."""

    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="password"
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Participant Team", created_by=self.user
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        # Create test directory for files
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test data."""
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_challenge(self, title="Test Challenge", end_date=None):
        """Helper method to create a challenge."""
        if end_date is None:
            end_date = timezone.now() - timedelta(
                days=400
            )  # Expired challenge

        return Challenge.objects.create(
            title=title,
            description="Test challenge description",
            terms_and_conditions="Test terms",
            submission_guidelines="Test guidelines",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=500),
            end_date=end_date,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
        )

    def create_challenge_phase(self, challenge, name="Test Phase"):
        """Helper method to create a challenge phase."""
        return ChallengePhase.objects.create(
            name=name,
            description="Test phase description",
            leaderboard_public=False,
            is_public=True,
            start_date=timezone.now() - timedelta(days=500),
            end_date=timezone.now() - timedelta(days=400),
            challenge=challenge,
            test_annotation=SimpleUploadedFile(
                "test_file.txt",
                b"Test file content",
                content_type="text/plain",
            ),
        )

    def create_submission(
        self, challenge_phase, status="submitted", file_size=1024
    ):
        """Helper method to create a submission."""
        # Create a mock file with specified size
        file_content = b"x" * file_size
        input_file = SimpleUploadedFile(
            f"submission_{status}.zip",
            file_content,
            content_type="application/zip",
        )

        return Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=challenge_phase,
            created_by=self.user,
            status=status,
            input_file=input_file,
            is_public=True,
        )


@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
class TestCleanupSubmissionsScript(BaseTestCase):
    """Test cases for the cleanup_submissions.py script."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()

        # Import the script module
        import sys

        sys.path.append(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "scripts", "data"
            )
        )

        # Mock Django setup to avoid actual Django initialization in tests
        with patch("django.setup"):
            from cleanup_submissions import (
                ExpiredSubmissionsDeleter,
                setup_logging,
            )

        self.ExpiredSubmissionsDeleter = ExpiredSubmissionsDeleter
        self.setup_logging = setup_logging

    def test_setup_logging_dry_run(self):
        """Test logging setup for dry run mode."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            self.setup_logging(dry_run=True)

            # Verify logger was configured
            mock_logger.setLevel.assert_called_with(20)  # logging.INFO
            mock_logger.handlers.clear.assert_called()
            mock_logger.addHandler.assert_called()
            mock_logger.propagate = False

    def test_setup_logging_execute(self):
        """Test logging setup for execute mode."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            self.setup_logging(dry_run=False)

            # Verify logger was configured
            mock_logger.setLevel.assert_called_with(20)  # logging.INFO
            mock_logger.handlers.clear.assert_called()
            mock_logger.addHandler.assert_called()
            mock_logger.propagate = False

    def test_setup_logging_cloudwatch_required(self):
        """Test that CloudWatch logging is always enabled."""
        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # Test with enable_cloudwatch=False (should still enable CloudWatch)
            self.setup_logging(dry_run=True, enable_cloudwatch=False)

            # Verify logger was configured
            mock_logger.setLevel.assert_called_with(20)  # logging.INFO
            mock_logger.handlers.clear.assert_called()
            mock_logger.addHandler.assert_called()
            mock_logger.propagate = False

    def test_expired_submissions_deleter_init(self):
        """Test ExpiredSubmissionsDeleter initialization."""
        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)

        self.assertTrue(deleter.dry_run)
        self.assertEqual(deleter.total_space_freed, 0)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=False)
        self.assertFalse(deleter.dry_run)
        self.assertEqual(deleter.total_space_freed, 0)

    def test_get_file_size_with_size_attribute(self):
        """Test get_file_size method with file.size attribute."""
        deleter = self.ExpiredSubmissionsDeleter()

        # Mock file field with size attribute
        mock_file = MagicMock()
        mock_file.size = 1024

        size = deleter.get_file_size(mock_file)
        self.assertEqual(size, 1024)

    def test_get_file_size_with_storage_backend(self):
        """Test get_file_size method with storage backend."""
        deleter = self.ExpiredSubmissionsDeleter()

        # Mock file field with storage backend
        mock_file = MagicMock()
        mock_file.size = None
        mock_file.storage = Mock()
        mock_file.storage.size.return_value = 2048
        mock_file.name = "test_file.txt"

        size = deleter.get_file_size(mock_file)
        self.assertEqual(size, 2048)
        mock_file.storage.size.assert_called_with("test_file.txt")

    def test_get_file_size_none_file(self):
        """Test get_file_size method with None file."""
        deleter = self.ExpiredSubmissionsDeleter()

        size = deleter.get_file_size(None)
        self.assertEqual(size, 0)

    def test_get_file_size_exception_handling(self):
        """Test get_file_size method exception handling."""
        deleter = self.ExpiredSubmissionsDeleter()

        # Mock file field that raises exception
        mock_file = Mock()
        mock_file.size = None
        mock_file.storage = Mock()
        mock_file.storage.size.side_effect = Exception("Storage error")

        size = deleter.get_file_size(mock_file)
        self.assertEqual(size, 0)

    def test_format_bytes(self):
        """Test format_bytes method."""
        deleter = self.ExpiredSubmissionsDeleter()

        # Test different sizes
        self.assertEqual(deleter.format_bytes(0), "0 B")
        self.assertEqual(deleter.format_bytes(1024), "1.00 KB")
        self.assertEqual(deleter.format_bytes(1024 * 1024), "1.00 MB")
        self.assertEqual(deleter.format_bytes(1024 * 1024 * 1024), "1.00 GB")

    def test_get_expired_challenges(self):
        """Test get_expired_challenges method."""
        # Create expired challenge
        expired_challenge = self.create_challenge(
            title="Expired Challenge",
            end_date=timezone.now() - timedelta(days=400),
        )

        # Create non-expired challenge
        active_challenge = self.create_challenge(
            title="Active Challenge",
            end_date=timezone.now() + timedelta(days=100),
        )

        deleter = self.ExpiredSubmissionsDeleter()
        deleter.deletion_cutoff_date = timezone.now() - timedelta(days=365)

        expired_challenges = deleter.get_expired_challenges()

        self.assertIn(expired_challenge, expired_challenges)
        self.assertNotIn(active_challenge, expired_challenges)

    def test_get_submissions_for_challenge(self):
        """Test get_submissions_for_challenge method."""
        challenge = self.create_challenge()
        phase1 = self.create_challenge_phase(challenge, "Phase 1")
        phase2 = self.create_challenge_phase(challenge, "Phase 2")

        # Create submissions for different phases
        submission1 = self.create_submission(phase1, "submitted")
        submission2 = self.create_submission(phase2, "finished")

        deleter = self.ExpiredSubmissionsDeleter()
        submissions = deleter.get_submissions_for_challenge(challenge)

        self.assertIn(submission1, submissions)
        self.assertIn(submission2, submissions)
        self.assertEqual(len(submissions), 2)

    def test_get_submission_stats(self):
        """Test get_submission_stats method."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)

        # Create submissions with different statuses
        submission1 = self.create_submission(phase, "submitted", 1024)
        submission2 = self.create_submission(phase, "finished", 2048)
        submission3 = self.create_submission(phase, "failed", 512)

        deleter = self.ExpiredSubmissionsDeleter()
        stats = deleter.get_submission_stats(
            [submission1, submission2, submission3]
        )

        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["by_status"]["submitted"], 1)
        self.assertEqual(stats["by_status"]["finished"], 1)
        self.assertEqual(stats["by_status"]["failed"], 1)
        self.assertEqual(stats["by_phase"]["Test Phase"], 3)

    def test_get_submission_stats_empty_list(self):
        """Test get_submission_stats method with empty list."""
        deleter = self.ExpiredSubmissionsDeleter()
        stats = deleter.get_submission_stats([])

        self.assertEqual(stats["total"], 0)
        self.assertEqual(stats["by_status"], {})
        self.assertEqual(stats["by_phase"], {})
        self.assertIsNone(stats["oldest"])
        self.assertIsNone(stats["newest"])

    def test_delete_submission_folder_dry_run(self):
        """Test delete_submission_folder method in dry run mode."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)

        # Mock AWS credentials and S3 client
        mock_aws_keys = {
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }

        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_creds, patch(
            "base.utils.get_boto3_client"
        ) as mock_get_client, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            mock_get_creds.return_value = mock_aws_keys
            mock_s3_client = MagicMock()
            mock_get_client.return_value = mock_s3_client
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock S3 list_objects_v2 response
            mock_s3_client.get_paginator.return_value.paginate.return_value = [
                {
                    "Contents": [
                        {"Key": f"submission_{submission.id}/file1.txt"}
                    ]
                }
            ]

            deleted_count = deleter.delete_submission_folder(submission)

            # Verify dry run behavior
            self.assertEqual(deleted_count, 1)
            # Verify no actual deletion was called
            mock_s3_client.delete_objects.assert_not_called()
            # Verify listing was called
            mock_s3_client.get_paginator.assert_called_with("list_objects_v2")

    def test_delete_submission_folder_execute(self):
        """Test delete_submission_folder method in execute mode."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=False)

        # Mock AWS credentials and S3 client
        mock_aws_keys = {
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }

        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_creds, patch(
            "base.utils.get_boto3_client"
        ) as mock_get_client, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            mock_get_creds.return_value = mock_aws_keys
            mock_s3_client = MagicMock()
            mock_get_client.return_value = mock_s3_client
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock S3 list_objects_v2 response
            mock_s3_client.get_paginator.return_value.paginate.return_value = [
                {
                    "Contents": [
                        {"Key": f"submission_{submission.id}/file1.txt"}
                    ]
                }
            ]

            deleted_count = deleter.delete_submission_folder(submission)

            # Verify actual deletion behavior
            self.assertEqual(deleted_count, 1)
            # Verify deletion was called
            mock_s3_client.delete_objects.assert_called_once()
            # Verify listing was called
            mock_s3_client.get_paginator.assert_called_with("list_objects_v2")

    def test_delete_submission_folder_no_objects(self):
        """Test delete_submission_folder method when no objects found."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=False)

        # Mock AWS credentials and S3 client
        mock_aws_keys = {
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }

        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_creds, patch(
            "base.utils.get_boto3_client"
        ) as mock_get_client, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            mock_get_creds.return_value = mock_aws_keys
            mock_s3_client = MagicMock()
            mock_get_client.return_value = mock_s3_client
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock S3 list_objects_v2 response with no contents
            mock_s3_client.get_paginator.return_value.paginate.return_value = [
                {}  # No Contents key
            ]

            deleted_count = deleter.delete_submission_folder(submission)

            # Verify behavior when no objects found
            self.assertEqual(deleted_count, 0)
            # Verify no deletion was called
            mock_s3_client.delete_objects.assert_not_called()

    def test_delete_submission_folder_exception_handling(self):
        """Test delete_submission_folder method exception handling."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=False)

        # Mock AWS credentials and S3 client
        mock_aws_keys = {
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }

        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_creds, patch(
            "base.utils.get_boto3_client"
        ) as mock_get_client, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            mock_get_creds.return_value = mock_aws_keys
            mock_s3_client = MagicMock()
            mock_get_client.return_value = mock_s3_client
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock S3 client to raise exception
            mock_s3_client.get_paginator.side_effect = Exception("S3 error")

            deleted_count = deleter.delete_submission_folder(submission)

            # Verify exception handling
            self.assertEqual(deleted_count, 0)
            # Verify error was logged
            mock_logger.error.assert_called()

    def test_delete_submission_files_dry_run(self):
        """Test delete_submission_files method in dry run mode."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)

        with patch.object(
            deleter, "delete_submission_folder"
        ) as mock_delete_folder, patch("logging.getLogger") as mock_get_logger:

            mock_delete_folder.return_value = 3  # 3 files would be deleted
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            deleted_count = deleter.delete_submission_files(submission)

            # Verify dry run behavior
            self.assertEqual(deleted_count, 3)
            mock_delete_folder.assert_called_once_with(submission)
            # Verify space was not added to total (dry run)
            self.assertEqual(deleter.total_space_freed, 0)

    def test_delete_submission_files_execute(self):
        """Test delete_submission_files method in execute mode."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=False)

        with patch.object(
            deleter, "delete_submission_folder"
        ) as mock_delete_folder, patch.object(
            deleter, "calculate_submission_space"
        ) as mock_calc_space:

            mock_delete_folder.return_value = 3  # 3 files deleted
            mock_calc_space.return_value = 1024  # 1KB

            deleted_count = deleter.delete_submission_files(submission)

            # Verify execute behavior
            self.assertEqual(deleted_count, 3)
            mock_delete_folder.assert_called_once_with(submission)
            # Verify space was added to total
            self.assertEqual(deleter.total_space_freed, 1024)

    def test_delete_submissions_files_dry_run(self):
        """Test delete_submissions_files method in dry run mode."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission1 = self.create_submission(phase)
        submission2 = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)

        # Mock AWS credentials and S3 client
        mock_aws_keys = {
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }

        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_creds, patch(
            "base.utils.get_boto3_client"
        ) as mock_get_client, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            mock_get_creds.return_value = mock_aws_keys
            mock_s3_client = MagicMock()
            mock_get_client.return_value = mock_s3_client
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock S3 list_objects_v2 response for both submissions
            mock_s3_client.get_paginator.return_value.paginate.return_value = [
                {
                    "Contents": [
                        {"Key": f"submission_{submission1.id}/file1.txt"},
                        {"Key": f"submission_{submission1.id}/file2.txt"},
                    ]
                },
                {
                    "Contents": [
                        {"Key": f"submission_{submission2.id}/file3.txt"}
                    ]
                },
            ]

            deleted_count, files_deleted = deleter.delete_submissions_files(
                [submission1, submission2]
            )

            # Verify dry run behavior
            self.assertEqual(deleted_count, 2)  # 2 submissions
            self.assertEqual(files_deleted, 3)  # 3 files total
            # Verify no actual deletion was called
            mock_s3_client.delete_objects.assert_not_called()
            # Verify listing was called
            mock_s3_client.get_paginator.assert_called_with("list_objects_v2")

    def test_delete_submissions_files_execute(self):
        """Test delete_submissions_files method in execute mode."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission1 = self.create_submission(phase)
        submission2 = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=False)

        with patch.object(
            deleter, "delete_submission_files"
        ) as mock_delete_files, patch.object(
            deleter, "calculate_submission_space"
        ) as mock_calc_space, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            # Mock return values for individual submission deletions
            mock_delete_files.side_effect = [
                2,
                1,
            ]  # 2 files from first submission, 1 from second
            mock_calc_space.return_value = 1024
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            deleted_count, files_deleted = deleter.delete_submissions_files(
                [submission1, submission2]
            )

            # Verify execute behavior
            self.assertEqual(deleted_count, 2)  # 2 submissions processed
            self.assertEqual(files_deleted, 3)  # 3 files total (2+1)
            # Verify delete_submission_files was called for each submission
            self.assertEqual(mock_delete_files.call_count, 2)

    def test_delete_submissions_files_exception_handling(self):
        """Test delete_submissions_files method exception handling."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission1 = self.create_submission(phase)
        submission2 = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=False)

        with patch.object(
            deleter, "delete_submission_files"
        ) as mock_delete_files, patch("logging.getLogger") as mock_get_logger:

            # First call succeeds (2 files), second call raises exception
            mock_delete_files.side_effect = [2, Exception("Delete error")]
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            deleted_count, files_deleted = deleter.delete_submissions_files(
                [submission1, submission2]
            )

            # Verify exception handling
            self.assertEqual(
                deleted_count, 1
            )  # Only first submission processed
            self.assertEqual(
                files_deleted, 2
            )  # Only files from first submission
            # Verify error was logged
            mock_logger.error.assert_called()

    def test_delete_submissions_files_empty_list(self):
        """Test delete_submissions_files method with empty list."""
        deleter = self.ExpiredSubmissionsDeleter()

        deleted_count, files_deleted = deleter.delete_submissions_files([])
        self.assertEqual(deleted_count, 0)
        self.assertEqual(files_deleted, 0)

    @freeze_time("2024-01-15")
    def test_run_method_dry_run(self):
        """Test run method in dry run mode."""
        # Create expired challenge with submissions
        challenge = self.create_challenge(
            end_date=timezone.now() - timedelta(days=400)
        )
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)
        deleter.deletion_cutoff_date = timezone.now() - timedelta(days=365)

        with patch.object(
            deleter, "delete_submissions_files"
        ) as mock_delete_files, patch("logging.getLogger") as mock_get_logger:

            mock_delete_files.return_value = (1, 2)  # 1 submission, 2 files
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = deleter.run()

            self.assertEqual(result["deleted_count"], 1)
            self.assertEqual(result["files_deleted"], 2)  # 2 files
            self.assertEqual(result["challenges_processed"], 1)
            self.assertGreater(result["space_freed"], 0)
            # Verify submission still exists in database (only files deleted)
            self.assertTrue(
                Submission.objects.filter(id=submission.id).exists()
            )
            # Verify S3 deletion was called
            mock_delete_files.assert_called_once()

    @freeze_time("2024-01-15")
    def test_run_method_execute(self):
        """Test run method in execute mode."""
        # Create expired challenge with submissions
        challenge = self.create_challenge(
            end_date=timezone.now() - timedelta(days=400)
        )
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=False)
        deleter.deletion_cutoff_date = timezone.now() - timedelta(days=365)

        with patch.object(
            deleter, "delete_submissions_files"
        ) as mock_delete_files, patch("logging.getLogger") as mock_get_logger:

            mock_delete_files.return_value = (1, 2)  # 1 submission, 2 files
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = deleter.run()

            self.assertEqual(result["deleted_count"], 1)
            self.assertEqual(result["files_deleted"], 2)  # 2 files
            self.assertEqual(result["challenges_processed"], 1)
            self.assertGreater(result["space_freed"], 0)
            # Verify submission still exists in database (only files deleted)
            self.assertTrue(
                Submission.objects.filter(id=submission.id).exists()
            )
            # Verify S3 deletion was called
            mock_delete_files.assert_called_once()

    def test_run_method_no_expired_challenges(self):
        """Test run method when no expired challenges exist."""
        # Create only active challenges
        self.create_challenge(end_date=timezone.now() + timedelta(days=100))

        deleter = self.ExpiredSubmissionsDeleter()
        deleter.deletion_cutoff_date = timezone.now() - timedelta(days=365)

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            result = deleter.run()

            self.assertEqual(result["deleted_count"], 0)
            self.assertEqual(result["files_deleted"], 0)
            self.assertEqual(result["challenges_processed"], 0)
            self.assertEqual(result["space_freed"], 0)

    def test_file_counting_in_dry_run(self):
        """Test that file counting works correctly in dry run mode."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission1 = self.create_submission(phase)
        submission2 = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)

        # Mock AWS credentials and S3 client
        mock_aws_keys = {
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }

        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_creds, patch(
            "base.utils.get_boto3_client"
        ) as mock_get_client, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            mock_get_creds.return_value = mock_aws_keys
            mock_s3_client = MagicMock()
            mock_get_client.return_value = mock_s3_client
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock different file counts for each submission
            mock_s3_client.get_paginator.return_value.paginate.side_effect = [
                [
                    {
                        "Contents": [
                            {"Key": f"submission_{submission1.id}/file1.txt"},
                            {"Key": f"submission_{submission1.id}/file2.txt"},
                        ]
                    }
                ],
                [
                    {
                        "Contents": [
                            {"Key": f"submission_{submission2.id}/file3.txt"},
                            {"Key": f"submission_{submission2.id}/file4.txt"},
                            {"Key": f"submission_{submission2.id}/file5.txt"},
                        ]
                    }
                ],
            ]

            deleted_count, files_deleted = deleter.delete_submissions_files(
                [submission1, submission2]
            )

            # Verify file counting
            self.assertEqual(deleted_count, 2)  # 2 submissions
            self.assertEqual(files_deleted, 5)  # 2 + 3 files
            # Verify no actual deletion was called
            mock_s3_client.delete_objects.assert_not_called()

    def test_file_counting_with_no_files(self):
        """Test file counting when submissions have no files."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)

        # Mock AWS credentials and S3 client
        mock_aws_keys = {
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }

        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_creds, patch(
            "base.utils.get_boto3_client"
        ) as mock_get_client, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            mock_get_creds.return_value = mock_aws_keys
            mock_s3_client = MagicMock()
            mock_get_client.return_value = mock_s3_client
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock empty response (no files)
            mock_s3_client.get_paginator.return_value.paginate.return_value = [
                {}  # No Contents key
            ]

            deleted_count, files_deleted = deleter.delete_submissions_files(
                [submission]
            )

            # Verify behavior when no files found
            self.assertEqual(deleted_count, 1)  # 1 submission processed
            self.assertEqual(files_deleted, 0)  # 0 files
            # Verify no deletion was called
            mock_s3_client.delete_objects.assert_not_called()

    def test_file_counting_with_all_file_types(self):
        """Test file counting when submissions have all possible file types."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)

        # Mock AWS credentials and S3 client
        mock_aws_keys = {
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }

        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_creds, patch(
            "base.utils.get_boto3_client"
        ) as mock_get_client, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            mock_get_creds.return_value = mock_aws_keys
            mock_s3_client = MagicMock()
            mock_get_client.return_value = mock_s3_client
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock S3 response with all possible file types
            mock_s3_client.get_paginator.return_value.paginate.return_value = [
                {
                    "Contents": [
                        {
                            "Key": f"media/submission_files/submission_{submission.id}/"
                            f"submission_{submission.id}.zip"
                        },
                        {
                            "Key": f"media/submission_files/submission_{submission.id}/"
                            f"submission_input_{submission.id}.npz"
                        },
                        {
                            "Key": f"media/submission_files/submission_{submission.id}/"
                            f"stdout_{submission.id}.txt"
                        },
                        {
                            "Key": f"media/submission_files/submission_{submission.id}/"
                            f"stderr_{submission.id}.txt"
                        },
                        {
                            "Key": f"media/submission_files/submission_{submission.id}/"
                            f"env_log_{submission.id}.log"
                        },
                        {
                            "Key": f"media/submission_files/submission_{submission.id}/"
                            f"result_{submission.id}.json"
                        },
                        {
                            "Key": f"media/submission_files/submission_{submission.id}/"
                            f"metadata_{submission.id}.json"
                        },
                    ]
                }
            ]

            deleted_count, files_deleted = deleter.delete_submissions_files(
                [submission]
            )

            # Verify all file types are counted
            self.assertEqual(deleted_count, 1)  # 1 submission processed
            self.assertEqual(files_deleted, 7)  # All 7 file types counted
            # Verify no deletion was called (dry run)
            mock_s3_client.delete_objects.assert_not_called()

    def test_file_counting_with_partial_files(self):
        """Test file counting when submissions have only some file types."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)

        # Mock AWS credentials and S3 client
        mock_aws_keys = {
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_ACCESS_KEY_ID": "test-key",
            "AWS_SECRET_ACCESS_KEY": "test-secret",
        }

        with patch(
            "challenges.utils.get_aws_credentials_for_challenge"
        ) as mock_get_creds, patch(
            "base.utils.get_boto3_client"
        ) as mock_get_client, patch(
            "logging.getLogger"
        ) as mock_get_logger:

            mock_get_creds.return_value = mock_aws_keys
            mock_s3_client = MagicMock()
            mock_get_client.return_value = mock_s3_client
            mock_logger = MagicMock()
            mock_get_logger.return_value = mock_logger

            # Mock S3 response with only some file types
            mock_s3_client.get_paginator.return_value.paginate.return_value = [
                {
                    "Contents": [
                        {
                            "Key": f"media/submission_files/submission_{submission.id}/"
                            f"submission_{submission.id}.zip"
                        },
                        {
                            "Key": f"media/submission_files/submission_{submission.id}/"
                            f"metadata_{submission.id}.json"
                        },
                    ]
                }
            ]

            deleted_count, files_deleted = deleter.delete_submissions_files(
                [submission]
            )

            # Verify partial file types are counted
            self.assertEqual(deleted_count, 1)  # 1 submission processed
            self.assertEqual(files_deleted, 2)  # Only 2 file types counted
            # Verify no deletion was called (dry run)
            mock_s3_client.delete_objects.assert_not_called()

    def test_return_value_structure(self):
        """Test that the return value structure is correct."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase)

        deleter = self.ExpiredSubmissionsDeleter(dry_run=True)

        with patch.object(
            deleter, "delete_submissions_files"
        ) as mock_delete_files:
            mock_delete_files.return_value = (3, 7)  # 3 submissions, 7 files

            result = deleter.run()

            # Verify return value structure
            self.assertIn("deleted_count", result)
            self.assertIn("files_deleted", result)
            self.assertIn("challenges_processed", result)
            self.assertIn("space_freed", result)
            self.assertIn("cutoff_date", result)

            # Verify values
            self.assertEqual(result["deleted_count"], 3)
            self.assertEqual(result["files_deleted"], 7)
        """Test calculate_submission_space method."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase, file_size=1024)

        deleter = self.ExpiredSubmissionsDeleter()
        space = deleter.calculate_submission_space(submission)

        # Should include input file size
        self.assertGreaterEqual(space, 1024)

    def test_calculate_submission_space_with_additional_files(self):
        """Test calculate_submission_space method with additional files."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase, file_size=1024)

        # Mock additional file fields
        submission.stdout_file = SimpleUploadedFile(
            "stdout.txt", b"stdout content", content_type="text/plain"
        )
        submission.stderr_file = SimpleUploadedFile(
            "stderr.txt", b"stderr content", content_type="text/plain"
        )

        deleter = self.ExpiredSubmissionsDeleter()
        space = deleter.calculate_submission_space(submission)

        # Should include all file sizes
        self.assertGreater(space, 1024)

    def test_calculate_submission_space_all_file_fields(self):
        """Test calculate_submission_space method with all possible file fields."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase, file_size=1024)

        # Mock all possible file fields with different sizes
        submission.submission_input_file = SimpleUploadedFile(
            "submission_input.npz",
            b"x" * 2048,
            content_type="application/octet-stream",
        )
        submission.stdout_file = SimpleUploadedFile(
            "stdout.txt", b"stdout content", content_type="text/plain"
        )
        submission.stderr_file = SimpleUploadedFile(
            "stderr.txt", b"stderr content", content_type="text/plain"
        )
        submission.environment_log_file = SimpleUploadedFile(
            "env_log.log",
            b"environment log content",
            content_type="text/plain",
        )
        submission.submission_result_file = SimpleUploadedFile(
            "result.json",
            b'{"result": "test"}',
            content_type="application/json",
        )
        submission.submission_metadata_file = SimpleUploadedFile(
            "metadata.json",
            b'{"metadata": "test"}',
            content_type="application/json",
        )

        deleter = self.ExpiredSubmissionsDeleter()
        space = deleter.calculate_submission_space(submission)

        # Should include all file sizes: 1024 + 2048 + 13 + 13 + 22 + 15 + 18 = 3153
        expected_min_size = 1024 + 2048 + 13 + 13 + 22 + 15 + 18
        self.assertGreaterEqual(space, expected_min_size)

    def test_calculate_submission_space_missing_file_fields(self):
        """Test calculate_submission_space method when file fields are missing."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase, file_size=1024)

        # Ensure no additional file fields are set
        submission.submission_input_file = None
        submission.stdout_file = None
        submission.stderr_file = None
        submission.environment_log_file = None
        submission.submission_result_file = None
        submission.submission_metadata_file = None

        deleter = self.ExpiredSubmissionsDeleter()
        space = deleter.calculate_submission_space(submission)

        # Should only include input file size
        self.assertEqual(space, 1024)

    def test_calculate_submission_space_no_files(self):
        """Test calculate_submission_space method when no files exist."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)

        # Create submission without input file
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=phase,
            created_by=self.user,
            status="submitted",
            is_public=True,
        )

        deleter = self.ExpiredSubmissionsDeleter()
        space = deleter.calculate_submission_space(submission)

        # Should return 0 when no files exist
        self.assertEqual(space, 0)

    def test_calculate_submission_space_partial_files(self):
        """Test calculate_submission_space method with some file fields missing."""
        challenge = self.create_challenge()
        phase = self.create_challenge_phase(challenge)
        submission = self.create_submission(phase, file_size=1024)

        # Only set some file fields
        submission.submission_input_file = SimpleUploadedFile(
            "submission_input.npz",
            b"x" * 2048,
            content_type="application/octet-stream",
        )
        submission.submission_metadata_file = SimpleUploadedFile(
            "metadata.json",
            b'{"metadata": "test"}',
            content_type="application/json",
        )
        # Leave other fields as None

        deleter = self.ExpiredSubmissionsDeleter()
        space = deleter.calculate_submission_space(submission)

        # Should include only the files that exist: 1024 + 2048 + 18 = 3090
        expected_size = 1024 + 2048 + 18
        self.assertEqual(space, expected_size)


class TestCloudWatchIntegration(BaseTestCase):
    """Test CloudWatch integration functionality."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()

        # Import the script module
        import sys

        sys.path.append(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "scripts", "data"
            )
        )

        # Mock Django setup to avoid actual Django initialization in tests
        with patch("django.setup"):
            from cleanup_submissions import CloudWatchHandler

        self.CloudWatchHandler = CloudWatchHandler

    def test_cloudwatch_handler_initialization(self):
        """Test CloudWatchHandler initialization."""
        with patch("boto3.client") as mock_boto3:
            mock_client = Mock()
            mock_boto3.return_value = mock_client

            handler = self.CloudWatchHandler(
                log_group_name="/test/log-group",
                log_stream_name="test-stream",
                region_name="us-east-1",
            )

            self.assertEqual(handler.log_group_name, "/test/log-group")
            self.assertEqual(handler.log_stream_name, "test-stream")
            self.assertEqual(handler.region_name, "us-east-1")

    def test_cloudwatch_handler_without_boto3(self):
        """Test CloudWatchHandler when boto3 is not available."""
        with patch(
            "boto3.client", side_effect=ImportError("No module named 'boto3'")
        ):
            handler = self.CloudWatchHandler(
                log_group_name="/test/log-group", log_stream_name="test-stream"
            )

            # Should handle missing boto3 gracefully
            self.assertIsNone(handler.logs_client)

    def test_cloudwatch_handler_emit(self):
        """Test CloudWatchHandler emit method."""
        with patch("boto3.client") as mock_boto3:
            mock_client = Mock()
            mock_boto3.return_value = mock_client

            handler = self.CloudWatchHandler(
                log_group_name="/test/log-group", log_stream_name="test-stream"
            )

            # Mock the log record
            record = Mock()
            record.created = 1640995200.0  # 2022-01-01 00:00:00
            record.getMessage.return_value = "Test log message"

            # Test emit
            handler.emit(record)

            # Verify boto3 was called
            mock_boto3.assert_called_with("logs", region_name="us-east-1")


class TestEnvironmentDetection(BaseTestCase):
    """Test environment detection functionality."""

    def setUp(self):
        """Set up test environment."""
        super().setUp()

        # Import the script module
        import sys

        sys.path.append(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "scripts", "data"
            )
        )

        # Mock Django setup to avoid actual Django initialization in tests
        with patch("django.setup"):
            from cleanup_submissions import setup_logging

        self.setup_logging = setup_logging

    def test_environment_detection_from_settings(self):
        """Test environment detection from Django settings."""
        # Test with ENVIRONMENT setting
        with patch("django.conf.settings") as mock_settings:
            mock_settings.ENVIRONMENT = "staging"

            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                self.setup_logging(dry_run=True)

                # Verify logger was configured
                mock_logger.setLevel.assert_called_with(20)
                mock_logger.handlers.clear.assert_called()
                mock_logger.addHandler.assert_called()

    def test_environment_detection_default_production(self):
        """Test environment detection defaults to production."""
        # Test with no ENVIRONMENT setting (should be production)
        with patch("django.conf.settings") as mock_settings:
            delattr(
                mock_settings, "ENVIRONMENT"
            )  # Remove ENVIRONMENT attribute

            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                self.setup_logging(dry_run=True)

                # Verify logger was configured
                mock_logger.setLevel.assert_called_with(20)
                mock_logger.handlers.clear.assert_called()
                mock_logger.addHandler.assert_called()

    def test_environment_detection_exception_handling(self):
        """Test environment detection handles exceptions gracefully."""
        # Test with exception when accessing settings
        with patch(
            "django.conf.settings", side_effect=Exception("Settings error")
        ):
            with patch("logging.getLogger") as mock_get_logger:
                mock_logger = Mock()
                mock_get_logger.return_value = mock_logger

                self.setup_logging(dry_run=True)

                # Verify logger was configured (should default to production)
                mock_logger.setLevel.assert_called_with(20)
                mock_logger.handlers.clear.assert_called()
                mock_logger.addHandler.assert_called()


class TestCleanupSubmissionsIntegration(BaseTestCase):
    """Integration tests for the cleanup submissions script."""

    def setUp(self):
        """Set up integration test environment."""
        super().setUp()

        # Create multiple challenges with different expiration dates
        self.expired_challenge_1 = self.create_challenge(
            title="Expired Challenge 1",
            end_date=timezone.now() - timedelta(days=400),
        )
        self.expired_challenge_2 = self.create_challenge(
            title="Expired Challenge 2",
            end_date=timezone.now() - timedelta(days=500),
        )
        self.active_challenge = self.create_challenge(
            title="Active Challenge",
            end_date=timezone.now() + timedelta(days=100),
        )

        # Create phases and submissions
        self.phase1 = self.create_challenge_phase(
            self.expired_challenge_1, "Phase 1"
        )
        self.phase2 = self.create_challenge_phase(
            self.expired_challenge_2, "Phase 2"
        )

        self.submission1 = self.create_submission(
            self.phase1, "submitted", 1024
        )
        self.submission2 = self.create_submission(
            self.phase1, "finished", 2048
        )
        self.submission3 = self.create_submission(self.phase2, "failed", 512)

    def test_integration_dry_run(self):
        """Integration test for dry run mode."""
        # Import and test the actual script
        import sys

        sys.path.append(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "scripts", "data"
            )
        )

        with patch("django.setup"):
            from cleanup_submissions import ExpiredSubmissionsDeleter

        deleter = ExpiredSubmissionsDeleter(dry_run=True)
        deleter.deletion_cutoff_date = timezone.now() - timedelta(days=365)

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            result = deleter.run()

            # Should process both expired challenges
            self.assertEqual(result["challenges_processed"], 2)
            # Should count all submissions
            self.assertEqual(result["deleted_count"], 3)
            # Should calculate total space
            self.assertGreater(result["space_freed"], 0)
            # Should not actually delete anything
            self.assertTrue(
                Submission.objects.filter(id=self.submission1.id).exists()
            )
            self.assertTrue(
                Submission.objects.filter(id=self.submission2.id).exists()
            )
            self.assertTrue(
                Submission.objects.filter(id=self.submission3.id).exists()
            )

    def test_integration_execute(self):
        """Integration test for execute mode."""
        # Import and test the actual script
        import sys

        sys.path.append(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "scripts", "data"
            )
        )

        with patch("django.setup"):
            from cleanup_submissions import ExpiredSubmissionsDeleter

        deleter = ExpiredSubmissionsDeleter(dry_run=False)
        deleter.deletion_cutoff_date = timezone.now() - timedelta(days=365)

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            result = deleter.run()

            # Should process both expired challenges
            self.assertEqual(result["challenges_processed"], 2)
            # Should delete all submissions
            self.assertEqual(result["deleted_count"], 3)
            # Should calculate total space
            self.assertGreater(result["space_freed"], 0)
            # Should actually delete everything
            self.assertFalse(
                Submission.objects.filter(id=self.submission1.id).exists()
            )
            self.assertFalse(
                Submission.objects.filter(id=self.submission2.id).exists()
            )
            self.assertFalse(
                Submission.objects.filter(id=self.submission3.id).exists()
            )


class TestCleanupSubmissionsEdgeCases(BaseTestCase):
    """Test edge cases for the cleanup submissions script."""

    def test_challenge_with_no_submissions(self):
        """Test handling of challenges with no submissions."""
        self.create_challenge(end_date=timezone.now() - timedelta(days=400))

        import sys

        sys.path.append(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "scripts", "data"
            )
        )

        with patch("django.setup"):
            from cleanup_submissions import ExpiredSubmissionsDeleter

        deleter = ExpiredSubmissionsDeleter(dry_run=True)
        deleter.deletion_cutoff_date = timezone.now() - timedelta(days=365)

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            result = deleter.run()

            # Should process the challenge but find no submissions
            self.assertEqual(result["challenges_processed"], 1)
            self.assertEqual(result["deleted_count"], 0)
            self.assertEqual(result["space_freed"], 0)

    def test_submission_with_missing_files(self):
        """Test handling of submissions with missing files."""
        challenge = self.create_challenge(
            end_date=timezone.now() - timedelta(days=400)
        )
        phase = self.create_challenge_phase(challenge)

        # Create submission without input file
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=phase,
            created_by=self.user,
            status="submitted",
            is_public=True,
        )

        import sys

        sys.path.append(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "scripts", "data"
            )
        )

        with patch("django.setup"):
            from cleanup_submissions import ExpiredSubmissionsDeleter

        deleter = ExpiredSubmissionsDeleter()
        space = deleter.calculate_submission_space(submission)

        # Should handle missing files gracefully
        self.assertEqual(space, 0)

    def test_large_number_of_submissions(self):
        """Test handling of large number of submissions."""
        challenge = self.create_challenge(
            end_date=timezone.now() - timedelta(days=400)
        )
        phase = self.create_challenge_phase(challenge)

        # Create many submissions
        submissions = []
        for i in range(100):
            submission = self.create_submission(phase, f"status_{i % 3}", 1024)
            submissions.append(submission)

        import sys

        sys.path.append(
            os.path.join(
                os.path.dirname(__file__), "..", "..", "..", "scripts", "data"
            )
        )

        with patch("django.setup"):
            from cleanup_submissions import ExpiredSubmissionsDeleter

        deleter = ExpiredSubmissionsDeleter(dry_run=True)
        deleter.deletion_cutoff_date = timezone.now() - timedelta(days=365)

        with patch("logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            result = deleter.run()

            # Should handle large number of submissions
            self.assertEqual(result["challenges_processed"], 1)
            self.assertEqual(result["deleted_count"], 100)
            self.assertGreater(result["space_freed"], 0)
