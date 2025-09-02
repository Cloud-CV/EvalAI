#!/usr/bin/env python3
"""
Script to clean up expired submissions from EvalAI challenges.

WHY THIS SCRIPT IS NEEDED:
=======================
1. **Storage Management**: Over time, EvalAI accumulates a large number of
   submission files (input files, output files, logs, etc.) that consume
   significant disk space.

2. **Performance**: Large numbers of old submissions can slow down database
   queries and file system operations, affecting overall platform performance.

3. **Cost Optimization**: Reducing storage usage helps minimize hosting costs,
   especially in cloud environments where storage is billed per GB.

4. **Data Retention Policy**: This script implements a data retention policy
   by automatically removing submission files from challenges that have been expired
   for a specified number of days (e.g., 365 days for 1 year).

5. **Compliance**: Helps maintain compliance with data retention policies
   by systematically cleaning up old data.

WHAT THIS SCRIPT DOES:
====================
- Identifies challenges that ended more than the specified number of days ago
- Calculates the total disk space used by submissions in those challenges
- Provides detailed statistics about submissions (by status, phase, etc.)
- Safely deletes submission files from S3 while keeping database records
- Deletes submission folders 'media/submission_files/submission_<submission_id>/' from the main S3 bucket
- Generates comprehensive logs for audit purposes
- Sends all logs to AWS CloudWatch for centralized monitoring

SAFETY FEATURES:
==============
- DRY RUN mode to preview what would be deleted without making changes
- Detailed logging of all operations
- Comprehensive error handling and reporting
- Required AWS CloudWatch logging for centralized log management and audit
  trails

CLOUDWATCH REQUIREMENTS:
======================
This script requires AWS CloudWatch logging for audit and monitoring purposes.
Set the following environment variables:
- DJANGO_SETTINGS_MODULE: Your Django settings module (e.g., 'settings.dev',
  'settings.prod')
- AWS_ACCESS_KEY_ID: Your AWS access key
- AWS_SECRET_ACCESS_KEY: Your AWS secret key
- AWS_DEFAULT_REGION: AWS region (default: us-east-1)
- CLOUDWATCH_LOG_GROUP: CloudWatch log group name (default:
  /evalai/cleanup-submissions/{environment})

The script automatically detects the environment (staging/production) from
Django settings:
- If settings.ENVIRONMENT is set, it uses that value
- Otherwise, it defaults to 'production'

The script will automatically create the log group and stream if they don't
exist. All operations are logged to CloudWatch with timestamps for compliance
and monitoring.

IMPORTANT: This script must be run from the project root directory (where
manage.py is located). The DJANGO_SETTINGS_MODULE environment variable must be
set to your Django settings module.

Usage:
    python scripts/data/cleanup_submissions.py --dry-run --days 365
    python scripts/data/cleanup_submissions.py --execute --days 365
    python scripts/data/cleanup_submissions.py --help

Examples:
    # Preview deletion of submission folders from challenges expired 1 year ago
    export DJANGO_SETTINGS_MODULE=settings.dev
    python scripts/data/cleanup_submissions.py --dry-run --days 365

    # Preview deletion of submission folders from challenges expired 6 months ago
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/data/cleanup_submissions.py --dry-run --days 180

    # Actually delete submission folders from challenges expired 1 year ago
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/data/cleanup_submissions.py --execute --days 365

    # Delete submission folders from challenges expired 2 years ago
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/data/cleanup_submissions.py --execute --days 730
"""

import argparse
import logging
import os
import sys
from datetime import timedelta
from typing import Any, Dict, List

# Add the project root to the Python path
sys.path.insert(
    0,
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ),
)

# Ensure we're using the correct app structure
if os.path.exists(
    os.path.join(
        os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ),
        "apps",
    )
):
    print("✅ Project structure detected correctly")
else:
    print("❌ Project structure not found")
    sys.exit(1)

# Set Django settings module from environment
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    print("❌ DJANGO_SETTINGS_MODULE environment variable is not set.")
    print(
        "Please set it to your Django settings module (e.g., 'settings.dev')"
    )
    sys.exit(1)

# Django setup
import django  # noqa: E402

try:
    django.setup()
    print("✅ Django setup completed successfully!")
except Exception as e:
    print(f"❌ Django setup failed: {str(e)}")
    print(
        "Please ensure you're running this script from the project root directory"
    )
    print("and that Django settings are properly configured.")
    sys.exit(1)

# Import models using a safer approach to avoid conflicts
import importlib  # noqa: E402

# Django imports after setup
from datetime import datetime  # noqa: E402

from django.conf import settings  # noqa: E402
from django.utils import timezone  # noqa: E402


def safe_import(module_path, class_names):
    """Safely import classes from a module."""
    try:
        module = importlib.import_module(module_path)
        return [getattr(module, class_name) for class_name in class_names]
    except Exception as e:
        print(f"❌ Failed to import from {module_path}: {str(e)}")
        return None


# Import models safely
print("🔍 Importing models safely...")
challenge_models = safe_import(
    "challenges.models", ["Challenge", "ChallengePhase"]
)
if challenge_models:
    Challenge, ChallengePhase = challenge_models
    print("✅ Successfully imported Challenge and ChallengePhase")
else:
    sys.exit(1)

# Import utilities safely
print("🔍 Importing utilities...")
try:
    from challenges.utils import (  # noqa: E402
        get_aws_credentials_for_challenge,
    )

    print("✅ Successfully imported get_aws_credentials_for_challenge")
except Exception as e:
    print(f"❌ Failed to import get_aws_credentials_for_challenge: {str(e)}")
    sys.exit(1)

try:
    from jobs.models import Submission  # noqa: E402

    print("✅ Successfully imported Submission")
except Exception as e:
    print(f"❌ Failed to import Submission: {str(e)}")
    sys.exit(1)

try:
    from base.utils import get_boto3_client  # noqa: E402

    print("✅ Successfully imported get_boto3_client")
except Exception as e:
    print(f"❌ Failed to import get_boto3_client: {str(e)}")
    sys.exit(1)


class CloudWatchHandler(logging.Handler):
    """Custom logging handler for AWS CloudWatch."""

    def __init__(self, log_group_name, log_stream_name, region_name=None):
        super().__init__()
        self.log_group_name = log_group_name
        self.log_stream_name = log_stream_name
        self.region_name = region_name
        self.logs_client = None
        self.sequence_token = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize AWS CloudWatch Logs client."""
        try:
            import boto3

            self.logs_client = boto3.client(
                "logs",
                region_name=self.region_name
                or os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            )
            self._create_log_group()
            self._create_log_stream()
        except ImportError:
            print("⚠️ boto3 not installed. CloudWatch logging disabled.")
            self.logs_client = None
        except Exception as e:
            print(f"⚠️ Failed to initialize CloudWatch client: {str(e)}")
            self.logs_client = None

    def _create_log_group(self):
        """Create CloudWatch log group if it doesn't exist."""
        if not self.logs_client:
            return

        try:
            self.logs_client.create_log_group(logGroupName=self.log_group_name)
            print(f"📊 Created CloudWatch log group: {self.log_group_name}")
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            print(
                f"📊 Using existing CloudWatch log group: {self.log_group_name}"
            )
        except Exception as e:
            print(f"⚠️ Failed to create log group: {str(e)}")

    def _create_log_stream(self):
        """Create CloudWatch log stream if it doesn't exist."""
        if not self.logs_client:
            return

        try:
            self.logs_client.create_log_stream(
                logGroupName=self.log_group_name,
                logStreamName=self.log_stream_name,
            )
            print(f"📊 Created CloudWatch log stream: {self.log_stream_name}")
        except self.logs_client.exceptions.ResourceAlreadyExistsException:
            print(
                f"📊 Using existing CloudWatch log stream: {self.log_stream_name}"
            )
        except Exception as e:
            print(f"⚠️ Failed to create log stream: {str(e)}")

    def emit(self, record):
        """Emit a log record to CloudWatch."""
        if not self.logs_client:
            return

        try:
            # Format the log message
            msg = self.format(record)

            # Prepare the log event
            log_event = {
                "timestamp": int(
                    record.created * 1000
                ),  # CloudWatch expects milliseconds
                "message": msg,
            }

            # Put log events
            if self.sequence_token:
                response = self.logs_client.put_log_events(
                    logGroupName=self.log_group_name,
                    logStreamName=self.log_stream_name,
                    logEvents=[log_event],
                    sequenceToken=self.sequence_token,
                )
            else:
                response = self.logs_client.put_log_events(
                    logGroupName=self.log_group_name,
                    logStreamName=self.log_stream_name,
                    logEvents=[log_event],
                )

            # Update sequence token for next call
            if "nextSequenceToken" in response:
                self.sequence_token = response["nextSequenceToken"]

        except self.logs_client.exceptions.InvalidSequenceTokenException as e:
            # Handle sequence token errors
            try:
                self.sequence_token = str(e).split("given: ")[1].split(",")[0]
                self.emit(record)  # Retry with correct token
            except Exception:
                print(f"⚠️ Failed to handle sequence token: {str(e)}")
        except Exception as e:
            print(f"⚠️ Failed to send log to CloudWatch: {str(e)}")


# Setup logging with file, console, and CloudWatch handlers
def setup_logging(dry_run: bool = True, enable_cloudwatch: bool = True):
    """Setup logging configuration with file, console, and CloudWatch output."""
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
    os.makedirs(log_dir, exist_ok=True)

    # Create log filename with timestamp and run type
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_type = "dry_run" if dry_run else "execute"
    log_filename = os.path.join(
        log_dir, f"cleanup_submissions_{run_type}_{timestamp}.log"
    )

    # Get the logger
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # Create file handler
    file_handler = logging.FileHandler(log_filename)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # CloudWatch logging is now required
    # Determine environment from Django settings
    try:
        if hasattr(settings, "ENVIRONMENT"):
            environment = settings.ENVIRONMENT
        else:
            environment = "production"
    except Exception:
        # Fallback if Django settings are not available
        environment = "production"

    cloudwatch_log_group = os.environ.get(
        "CLOUDWATCH_LOG_GROUP", f"/evalai/cleanup-submissions/{environment}"
    )
    cloudwatch_log_stream = f"cleanup-submissions-{run_type}-{timestamp}"
    cloudwatch_region = os.environ.get("AWS_DEFAULT_REGION", "us-east-1")

    cloudwatch_handler = CloudWatchHandler(
        log_group_name=cloudwatch_log_group,
        log_stream_name=cloudwatch_log_stream,
        region_name=cloudwatch_region,
    )
    cloudwatch_handler.setLevel(logging.INFO)
    cloudwatch_handler.setFormatter(formatter)
    logger.addHandler(cloudwatch_handler)
    logger.info(
        f"☁️ CloudWatch logging enabled: {cloudwatch_log_group}/{cloudwatch_log_stream}"
    )

    # Prevent propagation to root logger
    logger.propagate = False

    logger.info(f"🚀 Logging initialized. Log file: {log_filename}")
    return logger


# Initialize a basic logger for early messages
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
logger.addHandler(console_handler)
logger.propagate = False

logger.info("Logger setup completed!")
logger.info("✅ Logger is working correctly!")


class ExpiredSubmissionsDeleter:
    """Class to handle deletion of submission files from expired challenges."""

    def __init__(self, dry_run: bool = True):
        self.dry_run = dry_run
        self.deletion_cutoff_date = (
            None  # Will be set by main() based on --days argument
        )
        self.total_space_freed = 0  # Track space that would be freed (in dry run) or actually freed (in execute)

    def get_file_size(self, file_field) -> int:
        """Get the size of a file field in bytes."""
        try:
            if not file_field:
                return 0

            # First try to get size directly from the field
            if hasattr(file_field, "size") and file_field.size is not None:
                return file_field.size

            # If that doesn't work, try to get size from storage backend
            if hasattr(file_field, "storage") and hasattr(
                file_field.storage, "size"
            ):
                try:
                    return file_field.storage.size(file_field.name)
                except Exception:
                    pass

            # If all else fails, return 0
            return 0

        except Exception:
            return 0

    def calculate_submission_space(self, submission: Submission) -> int:
        """Calculate the total space used by a submission including all related files."""
        total_size = 0

        # Main input file
        if submission.input_file:
            total_size += self.get_file_size(submission.input_file)

        # Submission input file
        if (
            hasattr(submission, "submission_input_file")
            and submission.submission_input_file
        ):
            total_size += self.get_file_size(submission.submission_input_file)

        # Output files (if they exist)
        if hasattr(submission, "stdout_file") and submission.stdout_file:
            total_size += self.get_file_size(submission.stdout_file)

        if hasattr(submission, "stderr_file") and submission.stderr_file:
            total_size += self.get_file_size(submission.stderr_file)

        if (
            hasattr(submission, "environment_log_file")
            and submission.environment_log_file
        ):
            total_size += self.get_file_size(submission.environment_log_file)

        if (
            hasattr(submission, "submission_result_file")
            and submission.submission_result_file
        ):
            total_size += self.get_file_size(submission.submission_result_file)

        if (
            hasattr(submission, "submission_metadata_file")
            and submission.submission_metadata_file
        ):
            total_size += self.get_file_size(
                submission.submission_metadata_file
            )

        return total_size

    def format_bytes(self, size_bytes: int) -> str:
        """Convert bytes to human readable format."""
        if size_bytes == 0:
            return "0 B"

        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1

        return f"{size_bytes:.2f} {size_names[i]}"

    def get_expired_challenges(self) -> List[Challenge]:
        """Get challenges that ended before the cutoff date."""
        expired_challenges = Challenge.objects.filter(
            is_docker_based=False,
            end_date__lt=self.deletion_cutoff_date,
        ).order_by("end_date")

        logger.info(
            f"🔍 Found {expired_challenges.count()} challenges that expired before {self.deletion_cutoff_date}"
        )
        return list(expired_challenges)

    def get_submissions_for_challenge(
        self, challenge: Challenge
    ) -> List[Submission]:
        """Get all submissions for a specific challenge."""
        # Get all phases for this challenge
        phases = ChallengePhase.objects.filter(challenge=challenge)

        # Get submissions for all phases
        submissions = (
            Submission.objects.filter(challenge_phase__in=phases)
            .select_related(
                "challenge_phase", "participant_team", "created_by"
            )
            .order_by("submitted_at")
        )

        return list(submissions)

    def get_submission_stats(
        self, submissions: List[Submission]
    ) -> Dict[str, Any]:
        """Get statistics about submissions including space usage."""
        if not submissions:
            return {
                "total": 0,
                "by_status": {},
                "by_phase": {},
                "oldest": None,
                "newest": None,
                "total_space": 0,
                "space_by_status": {},
                "space_by_phase": {},
            }

        stats = {
            "total": len(submissions),
            "by_status": {},
            "by_phase": {},
            "oldest": min(s.submitted_at for s in submissions),
            "newest": max(s.submitted_at for s in submissions),
            "total_space": 0,
            "space_by_status": {},
            "space_by_phase": {},
        }

        # Count by status and calculate space
        for submission in submissions:
            status = submission.status
            stats["by_status"][status] = stats["by_status"].get(status, 0) + 1

            phase_name = submission.challenge_phase.name
            stats["by_phase"][phase_name] = (
                stats["by_phase"].get(phase_name, 0) + 1
            )

            # Calculate space for this submission
            submission_space = self.calculate_submission_space(submission)
            stats["total_space"] += submission_space
            stats["space_by_status"][status] = (
                stats["space_by_status"].get(status, 0) + submission_space
            )
            stats["space_by_phase"][phase_name] = (
                stats["space_by_phase"].get(phase_name, 0) + submission_space
            )

        return stats

    def delete_submission_folder(self, submission: Submission) -> int:
        """
        Delete the submission folder from S3.
        Based on the URL structure: https://evalai.s3.amazonaws.com/media/submission_files/submission_308757/
        We delete the folder 'media/submission_files/submission_<submission_id>/' directly.
        """
        try:
            challenge_pk = submission.challenge_phase.challenge.pk
            aws_keys = get_aws_credentials_for_challenge(challenge_pk)
            s3_client = get_boto3_client("s3", aws_keys)
            bucket_name = aws_keys["AWS_STORAGE_BUCKET_NAME"]
            prefix = f"media/submission_files/submission_{submission.id}/"

            # List all objects with the prefix
            objects_to_delete = []
            paginator = s3_client.get_paginator("list_objects_v2")
            pages = paginator.paginate(Bucket=bucket_name, Prefix=prefix)
            for page in pages:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        objects_to_delete.append({"Key": obj["Key"]})

            if not objects_to_delete:
                if not self.dry_run:
                    logger.info(
                        f"🤔 No S3 objects found for submission {submission.id} with prefix {prefix}"
                    )
                return 0

            if self.dry_run:
                logger.info(
                    f"🔍 DRY RUN: Would delete {len(objects_to_delete)} files from submission {submission.id} folder"
                )
                return len(objects_to_delete)

            logger.info(
                f"🗑️ Deleting {len(objects_to_delete)} files from submission {submission.id} folder"
            )

            # Delete the objects
            s3_client.delete_objects(
                Bucket=bucket_name, Delete={"Objects": objects_to_delete}
            )

            logger.info(
                f"✅ Successfully deleted folder for submission {submission.id}"
            )
            return len(objects_to_delete)

        except Exception as e:
            logger.error(
                f"❌ Error processing folder for submission {submission.id}: {str(e)}"
            )
            return 0

    def delete_submission_files(self, submission: Submission) -> int:
        """Delete all files associated with a submission from S3 by deleting the folder."""
        submission_space = self.calculate_submission_space(submission)
        if self.dry_run:
            logger.info(f"🔍 DRY RUN: Processing submission {submission.id}")
            if submission_space > 0:
                logger.info(
                    f"  🔍 Would free {self.format_bytes(submission_space)}"
                )

        # Delete submission folder within the main bucket
        deleted_object_count = self.delete_submission_folder(submission)

        if not self.dry_run and deleted_object_count > 0:
            self.total_space_freed += submission_space

        return deleted_object_count

    def delete_submissions_files(self, submissions: List[Submission]) -> tuple:
        """Delete files from S3 for multiple submissions. Returns (submission_count, file_count)."""
        if not submissions:
            return (0, 0)

        if self.dry_run:
            # In dry run, we need to count the actual files that would be deleted
            total_files_to_delete = 0
            submission_folders_to_delete = (
                []
            )  # Track folders that will be deleted

            for submission in submissions:
                try:
                    # Mock the deletion to count files without actually deleting
                    challenge_pk = submission.challenge_phase.challenge.pk
                    aws_keys = get_aws_credentials_for_challenge(challenge_pk)
                    s3_client = get_boto3_client("s3", aws_keys)
                    bucket_name = aws_keys["AWS_STORAGE_BUCKET_NAME"]
                    prefix = (
                        f"media/submission_files/submission_{submission.id}/"
                    )

                    # List all objects with the prefix to count them
                    objects_to_count = []
                    paginator = s3_client.get_paginator("list_objects_v2")
                    pages = paginator.paginate(
                        Bucket=bucket_name, Prefix=prefix
                    )
                    for page in pages:
                        if "Contents" in page:
                            for obj in page["Contents"]:
                                objects_to_count.append({"Key": obj["Key"]})

                    # Debug: Log what we found
                    if not objects_to_count:
                        logger.debug(
                            f"🔍 No files found for submission {submission.id} with prefix: {prefix}"
                        )
                    else:
                        logger.debug(
                            f"🔍 Found {len(objects_to_count)} files for submission {submission.id}"
                        )
                        submission_folders_to_delete.append(
                            f"media/submission_files/submission_{submission.id}/"
                        )

                    total_files_to_delete += len(objects_to_count)
                except Exception as e:
                    logger.warning(
                        f"⚠️ Could not count files for submission {submission.id}: {str(e)}"
                    )
                    continue

            # Log the folders that will be deleted
            if submission_folders_to_delete:
                logger.info(
                    "📁 DRY RUN: Submission folders that would be deleted:"
                )
                for folder in submission_folders_to_delete:
                    logger.info(f"   📁 {folder}")
            else:
                logger.info(
                    "📁 DRY RUN: No submission folders found to delete"
                )

            logger.info(
                f"🔍 DRY RUN: Would delete {total_files_to_delete} files from {len(submissions)} submissions"
            )
            return (len(submissions), total_files_to_delete)

        deleted_count = 0
        total_objects_deleted = 0
        deleted_folders = []  # Track folders that are actually deleted

        for submission in submissions:
            try:
                # Calculate space before deletion for logging
                submission_space = self.calculate_submission_space(submission)

                # Log before deletion
                if not self.dry_run:
                    logger.info(
                        f"🗑️ Deleting files from submission {submission.id} "
                        f"(Challenge: {submission.challenge_phase.challenge.title}, "
                        f"Phase: {submission.challenge_phase.name}, "
                        f"Status: {submission.status}, "
                        f"Submitted: {submission.submitted_at}, "
                        f"Space: {self.format_bytes(submission_space)})"
                    )

                # Delete files from S3
                deleted_objects = self.delete_submission_files(submission)

                if deleted_objects > 0:
                    deleted_count += 1
                    total_objects_deleted += deleted_objects
                    deleted_folders.append(
                        f"media/submission_files/submission_{submission.id}/"
                    )

                if not self.dry_run and deleted_objects > 0:
                    logger.info(
                        f"✅ Processed submission {submission.id}, deleted {deleted_objects} objects."
                    )

            except Exception as e:
                logger.error(
                    f"❌ Error processing submission {submission.id}: {str(e)}"
                )
                continue

        # Log the folders that were actually deleted
        if not self.dry_run and deleted_folders:
            logger.info("📁 EXECUTE: Submission folders that were deleted:")
            for folder in deleted_folders:
                logger.info(f"   📁 {folder}")
        elif not self.dry_run:
            logger.info("📁 EXECUTE: No submission folders were deleted")

        if self.dry_run:
            logger.info(
                f"🔍 DRY RUN: Would delete {total_objects_deleted} objects from {deleted_count} submissions."
            )

        return (deleted_count, total_objects_deleted)

    def run(self) -> Dict[str, Any]:
        """Main method to run the deletion process."""
        logger.info("🚀 Starting expired submission files deletion process")
        logger.info(f"📅 Deletion cutoff date: {self.deletion_cutoff_date}")
        logger.info(f"🔍 Dry run: {self.dry_run}")

        # Get expired challenges
        expired_challenges = self.get_expired_challenges()

        if not expired_challenges:
            logger.info("❌ No expired challenges found")
            return {
                "deleted_count": 0,  # No submissions to delete
                "challenges_processed": 0,
                "space_freed": 0,  # No space to free
            }

        total_deleted = 0  # Count of submissions that would be deleted (dry run) or were deleted (execute)
        challenges_processed = 0
        total_space_freed = (
            0  # Space that would be freed (dry run) or was freed (execute)
        )
        total_files_deleted = 0  # Count of individual files that would be deleted (dry run) or were deleted (execute)

        for challenge in expired_challenges:
            logger.info(
                f"\n📊 Processing challenge: {challenge.title} (ID: {challenge.id})"
            )
            logger.info(f"📅 Challenge ended: {challenge.end_date}")
            logger.info(
                f"⏰ Days since expiration: {(timezone.now() - challenge.end_date).days}"
            )

            # Get submissions for this challenge
            submissions = self.get_submissions_for_challenge(challenge)

            if not submissions:
                logger.info("❌ No submissions found for this challenge")
                continue

            # Get and log statistics
            stats = self.get_submission_stats(submissions)
            logger.info("📈 Submission statistics:")
            logger.info(f"  Total submissions: {stats['total']}")
            logger.info(f"  Oldest submission: {stats['oldest']}")
            logger.info(f"  Newest submission: {stats['newest']}")
            logger.info(
                f"  Total space used: {self.format_bytes(stats['total_space'])}"
            )
            logger.info(f"  By status: {stats['by_status']}")
            logger.info(f"  By phase: {stats['by_phase']}")

            # Log space breakdown by status
            if stats["space_by_status"]:
                logger.info("  💾 Space by status:")
                for status, space in stats["space_by_status"].items():
                    logger.info(f"    {status}: {self.format_bytes(space)}")

            # Log space breakdown by phase
            if stats["space_by_phase"]:
                logger.info("  📁 Space by phase:")
                for phase, space in stats["space_by_phase"].items():
                    logger.info(f"    {phase}: {self.format_bytes(space)}")

            # Delete submission files
            deleted_count, files_deleted = self.delete_submissions_files(
                submissions
            )

            total_deleted += deleted_count
            total_files_deleted += files_deleted
            total_space_freed += stats["total_space"]
            challenges_processed += 1

            if self.dry_run:
                logger.info(
                    f"🔍 DRY RUN: Would delete files from {deleted_count} submissions from challenge {challenge.title}"
                )
            else:
                logger.info(
                    f"🗑️ Deleted files from {deleted_count} submissions from challenge {challenge.title}"
                )
            if self.dry_run:
                logger.info(
                    f"💾 DRY RUN: Space that would be freed: {self.format_bytes(stats['total_space'])}"
                )
            else:
                logger.info(
                    f"💾 Space freed: {self.format_bytes(stats['total_space'])}"
                )

        logger.info("\n🎉 Deletion process completed!")
        logger.info(f"📊 Challenges processed: {challenges_processed}")
        if self.dry_run:
            logger.info(
                f"🔍 DRY RUN: Total submissions that would have files deleted: {total_deleted}"
            )
            logger.info(
                f"🔍 DRY RUN: Total files that would be deleted: {total_files_deleted}"
            )
            logger.info(
                f"💾 DRY RUN: Total space that would be freed: {self.format_bytes(total_space_freed)}"
            )
        else:
            logger.info(
                f"🗑️ Total submissions with files deleted: {total_deleted}"
            )
            logger.info(f"🗑️ Total files deleted: {total_files_deleted}")
            logger.info(
                f"💾 Total space freed: {self.format_bytes(total_space_freed)}"
            )

        return {
            # Count of submissions that would be deleted (dry run) or were deleted (execute)
            "deleted_count": total_deleted,
            "challenges_processed": challenges_processed,
            "cutoff_date": self.deletion_cutoff_date,
            # Space that would be freed (dry run) or was freed (execute)
            "space_freed": total_space_freed,
            # Count of individual files that would be deleted (dry run) or were deleted (execute)
            "files_deleted": total_files_deleted,
        }


def main():
    """Main function to parse arguments and run the deletion process."""
    global logger

    # Test Django configuration
    try:
        logger.info(
            f"Django Setting Module: {os.getenv('DJANGO_SETTINGS_MODULE')}"
        )
        logger.info(f"Database: {settings.DATABASES['default']['ENGINE']}")
    except Exception as e:
        logger.error(f"Django configuration error: {str(e)}")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Clean up expired submission files from EvalAI challenges. "
        "Requires DJANGO_SETTINGS_MODULE environment variable and "
        "AWS CloudWatch logging."
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be deleted without actually deleting",
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete the submission files (use with caution!)",
    )

    parser.add_argument(
        "--days",
        type=int,
        required=True,
        help="Number of days after challenge end date to consider for cleanup "
        "(e.g., 365 for 1 year, 180 for 6 months)",
    )

    parser.add_argument(
        "--challenge-id", type=int, help="Only process a specific challenge ID"
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.dry_run and not args.execute:
        logger.error("You must specify either --dry-run or --execute")
        sys.exit(1)

    if args.dry_run and args.execute:
        logger.error("You cannot specify both --dry-run and --execute")
        sys.exit(1)

    # Set up proper logging with CloudWatch enabled
    logger = setup_logging(dry_run=args.dry_run)

    # Create deleter instance
    deleter = ExpiredSubmissionsDeleter(dry_run=args.dry_run)

    # Set the cutoff date based on the required days argument
    if args.days <= 0:
        logger.error(
            "Days argument must be positive (e.g., 365 for 1 year, "
            "180 for 6 months)"
        )
        sys.exit(1)

    deleter.deletion_cutoff_date = timezone.now() - timedelta(days=args.days)
    logger.info(
        f"🔧 Using cutoff: {args.days} days ago "
        f"({deleter.deletion_cutoff_date})"
    )

    # Run the deletion process
    try:
        result = deleter.run()

        if args.dry_run:
            logger.info(
                "🔍 DRY RUN COMPLETED - No actual deletions were performed"
            )
        else:
            logger.info(
                "✅ DELETION COMPLETED - Submission files have been deleted"
            )

        # logger.info summary
        logger.info("\n" + "=" * 50)
        logger.info("SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Challenges processed: {result['challenges_processed']}")
        if args.dry_run:
            logger.info(
                f"Submissions that would have files deleted: {result['deleted_count']}"
            )
            logger.info(
                f"Files that would be deleted: {result['files_deleted']}"
            )
            logger.info(
                f"Space that would be freed: {deleter.format_bytes(result['space_freed'])}"
            )
        else:
            logger.info(
                f"Submissions with files deleted: {result['deleted_count']}"
            )
            logger.info(f"Files deleted: {result['files_deleted']}")
            logger.info(
                f"Space freed: {deleter.format_bytes(result['space_freed'])}"
            )
        logger.info(f"Cutoff date: {result['cutoff_date']}")
        logger.info("=" * 50)

    except Exception as e:
        logger.error(f"❌ Error during deletion process: {str(e)}")
        import traceback

        logger.error(f"📋 Traceback: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
