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
- Lists challenges by category (ongoing, past, upcoming, not approved by admin) sorted by S3 space usage
- Calculates and displays S3 space usage for each challenge's submissions
- Identifies challenges that ended more than the specified number of days ago
- Identifies challenges not approved by admin and older than 30 days
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
    python scripts/s3/cleanup_submissions.py --dry-run --days 365
    python scripts/s3/cleanup_submissions.py --execute --days 365
    python scripts/s3/cleanup_submissions.py --dry-run --past-challenges-only
    python scripts/s3/cleanup_submissions.py --execute --past-challenges-only
    python scripts/s3/cleanup_submissions.py --dry-run --past-challenges-min-days 90
    python scripts/s3/cleanup_submissions.py --execute --past-challenges-min-days 90
    python scripts/s3/cleanup_submissions.py --dry-run --not-approved-by-admin
    python scripts/s3/cleanup_submissions.py --execute --not-approved-by-admin
    python scripts/s3/cleanup_submissions.py --list-challenges
    python scripts/s3/cleanup_submissions.py --help

Examples:
    # Preview deletion of submission folders from challenges expired 1 year ago
    export DJANGO_SETTINGS_MODULE=settings.dev
    python scripts/s3/cleanup_submissions.py --dry-run --days 365

    # Preview deletion of submission folders from challenges expired 6 months ago
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/s3/cleanup_submissions.py --dry-run --days 180

    # Actually delete submission folders from challenges expired 1 year ago
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/s3/cleanup_submissions.py --execute --days 365

    # Delete submission folders from challenges expired 2 years ago
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/s3/cleanup_submissions.py --execute --days 730

    # Preview deletion of submission folders from ALL past challenges (regardless of when they ended)
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/s3/cleanup_submissions.py --dry-run --past-challenges-only

    # Actually delete submission folders from ALL past challenges
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/s3/cleanup_submissions.py --execute --past-challenges-only

    # Preview deletion of submission folders from past challenges that ended at least 90 days ago
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/s3/cleanup_submissions.py --dry-run --past-challenges-min-days 90

    # Actually delete submission folders from past challenges that ended at least 90 days ago
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/s3/cleanup_submissions.py --execute --past-challenges-min-days 90

    # Preview deletion of submission folders from challenges not approved by admin and older than 30 days
    export DJANGO_SETTINGS_MODULE=settings.dev
    python scripts/s3/cleanup_submissions.py --dry-run --not-approved-by-admin

    # Actually delete submission folders from challenges not approved by admin and older than 30 days
    export DJANGO_SETTINGS_MODULE=settings.prod
    python scripts/s3/cleanup_submissions.py --execute --not-approved-by-admin

    # List all challenges by category (ongoing, past, upcoming, not approved)
    export DJANGO_SETTINGS_MODULE=settings.dev
    python scripts/s3/cleanup_submissions.py --list-challenges
"""

import argparse
import importlib
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Try to import boto3 for CloudWatch logging
try:
    import boto3
except ImportError:
    boto3 = None

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

# Django imports after setup
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
            if boto3 is None:
                print("⚠️ boto3 not installed. CloudWatch logging disabled.")
                self.logs_client = None
                return

            self.logs_client = boto3.client(
                "logs",
                region_name=self.region_name
                or os.environ.get("AWS_DEFAULT_REGION", "us-east-1"),
            )
            self._create_log_group()
            self._create_log_stream()
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
        "☁️ CloudWatch logging enabled: %s/%s",
        cloudwatch_log_group,
        cloudwatch_log_stream,
    )

    # Prevent propagation to root logger
    logger.propagate = False

    logger.info(f"🚀 Logging initialized. Log file: {log_filename}")
    return logger


# Initialize a basic logger for early messages
early_logger = logging.getLogger(__name__)
early_logger.setLevel(logging.INFO)
early_console_handler = logging.StreamHandler(sys.stdout)
early_console_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
)
early_logger.addHandler(early_console_handler)
early_logger.propagate = False

early_logger.info("Logger setup completed!")
early_logger.info("✅ Logger is working correctly!")


class ExpiredSubmissionsDeleter:
    """Class to handle deletion of submission files from expired challenges."""

    def __init__(
        self,
        dry_run: bool = True,
        past_challenges_only: bool = False,
        past_challenges_min_days: int = None,
        not_approved_by_admin: bool = False,
    ):
        self.dry_run = dry_run
        self.past_challenges_only = past_challenges_only
        self.past_challenges_min_days = past_challenges_min_days
        self.not_approved_by_admin = not_approved_by_admin
        self.deletion_cutoff_date = (
            None  # Will be set by main() based on --days argument
        )
        # Track space that would be freed (in dry run) or actually freed (in execute)
        self.total_space_freed = 0
        self.logger = logging.getLogger(__name__)

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

    def get_challenges_by_category(self) -> Dict[str, List[Challenge]]:
        """Get challenges categorized by status."""
        now = timezone.now()

        # Ongoing challenges (started but not ended)
        ongoing_challenges = Challenge.objects.filter(
            is_docker_based=False,
            start_date__lt=now,
            end_date__gt=now,
            is_disabled=False,
        ).order_by("title")

        # Past challenges (ended)
        past_challenges = Challenge.objects.filter(
            is_docker_based=False,
            end_date__lt=now,
            is_disabled=False,
        ).order_by("-end_date")

        # Upcoming challenges (not started yet)
        upcoming_challenges = Challenge.objects.filter(
            is_docker_based=False,
            start_date__gt=now,
            is_disabled=False,
        ).order_by("start_date")

        # Not approved by admin and older than 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        not_approved_challenges = Challenge.objects.filter(
            approved_by_admin=False,
            created_at__lt=thirty_days_ago,
        ).order_by("id")

        return {
            "ongoing": list(ongoing_challenges),
            "past": list(past_challenges),
            "upcoming": list(upcoming_challenges),
            "not_approved": list(not_approved_challenges),
        }

    def calculate_challenge_space(self, challenge: Challenge) -> int:
        """Calculate the total S3 space used by all submissions in a challenge."""
        try:
            # Get all phases for this challenge
            phases = ChallengePhase.objects.filter(challenge=challenge)

            # Get all submissions for all phases
            submissions = Submission.objects.filter(challenge_phase__in=phases)

            total_space = 0
            for submission in submissions:
                total_space += self.calculate_submission_space(submission)

            return total_space
        except Exception as e:
            self.logger.warning(
                "⚠️ Could not calculate space for challenge %s: %s",
                challenge.id,
                str(e),
            )
            return 0

    def format_challenge_info(
        self, challenge: Challenge, include_space: bool = True
    ) -> str:
        """Format challenge information for display."""
        info = []
        info.append(f"  ID: {challenge.id}")
        info.append(f"  Title: {challenge.title}")
        info.append(f"  Creator: {challenge.creator.team_name}")
        info.append(f"  Published: {'Yes' if challenge.published else 'No'}")
        info.append(
            f"  Approved: {'Yes' if challenge.approved_by_admin else 'No'}"
        )

        if challenge.start_date:
            info.append(f"  Start Date: {challenge.start_date}")
        if challenge.end_date:
            info.append(f"  End Date: {challenge.end_date}")

        # Calculate days since/until start/end
        now = timezone.now()
        if challenge.start_date and challenge.end_date:
            if challenge.start_date > now:
                days_until_start = (challenge.start_date - now).days
                info.append(f"  Days until start: {days_until_start}")
            elif challenge.end_date > now:
                days_until_end = (challenge.end_date - now).days
                info.append(f"  Days until end: {days_until_end}")
            else:
                days_since_end = (now - challenge.end_date).days
                info.append(f"  Days since end: {days_since_end}")

        # Count submissions
        phases = ChallengePhase.objects.filter(challenge=challenge)
        submission_count = Submission.objects.filter(
            challenge_phase__in=phases
        ).count()
        info.append(f"  Total Submissions: {submission_count}")

        # Calculate and display S3 space usage
        if include_space:
            total_space = self.calculate_challenge_space(challenge)
            info.append(f"  S3 Space Used: {self.format_bytes(total_space)}")

        return "\n".join(info)

    def list_challenges(self) -> None:
        """List challenges by category, sorted by S3 space usage."""
        self.logger.info(
            "📋 Listing challenges by category (sorted by S3 space usage)..."
        )

        categories = self.get_challenges_by_category()
        total_space_all_categories = 0

        for category_name, challenges in categories.items():
            self.logger.info(f"\n{'='*60}")
            self.logger.info(
                f"📊 {category_name.upper().replace('_', ' ')} CHALLENGES ({len(challenges)} total)"
            )
            self.logger.info(f"{'='*60}")

            if not challenges:
                self.logger.info("  No challenges found in this category.")
                continue

            # Calculate space for each challenge and sort by space (descending)
            challenges_with_space = []
            category_total_space = 0

            for challenge in challenges:
                space = self.calculate_challenge_space(challenge)
                challenges_with_space.append((challenge, space))
                category_total_space += space

            # Sort by space usage (descending order)
            challenges_with_space.sort(key=lambda x: x[1], reverse=True)

            # Display challenges sorted by space usage
            for challenge, space in challenges_with_space:
                self.logger.info(f"\n{'-'*40}")
                self.logger.info(
                    self.format_challenge_info(challenge, include_space=True)
                )

            # Display category summary
            self.logger.info(f"\n{'='*60}")
            self.logger.info(
                f"📈 {category_name.upper().replace('_', ' ')} CATEGORY SUMMARY:"
            )
            self.logger.info(f"  Total Challenges: {len(challenges)}")
            self.logger.info(
                f"  Total S3 Space Used: {self.format_bytes(category_total_space)}"
            )
            self.logger.info(f"{'='*60}")

            total_space_all_categories += category_total_space

        # Display overall summary
        self.logger.info(f"\n{'='*80}")
        self.logger.info("🎯 OVERALL SUMMARY:")
        self.logger.info(
            f"  Total S3 Space Used by All Challenges: {self.format_bytes(total_space_all_categories)}"
        )
        self.logger.info(f"{'='*80}")

    def get_expired_challenges(self) -> List[Challenge]:
        """Get challenges that ended before the cutoff date or all past challenges."""
        if self.not_approved_by_admin:
            # Get challenges that are not approved by admin and are more than 30 days old
            thirty_days_ago = timezone.now() - timedelta(days=30)
            expired_challenges = Challenge.objects.filter(
                approved_by_admin=False,
                created_at__lt=thirty_days_ago,
            ).order_by("id")

            self.logger.info(
                "🔍 Found %s challenges not approved by admin and older than 30 days "
                "(approved_by_admin=False, created_at < %s)",
                expired_challenges.count(),
                thirty_days_ago,
            )
        elif self.past_challenges_min_days is not None:
            # Get challenges that ended at least N days ago
            min_days_cutoff = timezone.now() - timedelta(
                days=self.past_challenges_min_days
            )
            expired_challenges = Challenge.objects.filter(
                is_docker_based=False,
                end_date__lt=min_days_cutoff,
            ).order_by("end_date")

            self.logger.info(
                "🔍 Found %s past challenges that ended at least %s days ago (end_date < %s)",
                expired_challenges.count(),
                self.past_challenges_min_days,
                min_days_cutoff,
            )
        elif self.past_challenges_only:
            # Get all challenges that have ended (end_date < current_time)
            expired_challenges = Challenge.objects.filter(
                is_docker_based=False,
                end_date__lt=timezone.now(),
            ).order_by("end_date")

            self.logger.info(
                "🔍 Found %s past challenges (end_date < %s)",
                expired_challenges.count(),
                timezone.now(),
            )
        else:
            # Get challenges that ended before the cutoff date
            expired_challenges = Challenge.objects.filter(
                is_docker_based=False,
                end_date__lt=self.deletion_cutoff_date,
            ).order_by("end_date")

            self.logger.info(
                "🔍 Found %s challenges that expired before %s",
                expired_challenges.count(),
                self.deletion_cutoff_date,
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
                    self.logger.info(
                        "🤔 No S3 objects found for submission %s with prefix %s",
                        submission.id,
                        prefix,
                    )
                return 0

            if self.dry_run:
                self.logger.info(
                    "🔍 DRY RUN: Would delete %s files from submission %s folder",
                    len(objects_to_delete),
                    submission.id,
                )
                return len(objects_to_delete)

            self.logger.info(
                "🗑️ Deleting %s files from submission %s folder",
                len(objects_to_delete),
                submission.id,
            )

            # Delete the objects
            s3_client.delete_objects(
                Bucket=bucket_name, Delete={"Objects": objects_to_delete}
            )

            self.logger.info(
                "✅ Successfully deleted folder for submission %s",
                submission.id,
            )
            return len(objects_to_delete)

        except Exception as e:
            self.logger.error(
                "❌ Error processing folder for submission %s: %s",
                submission.id,
                str(e),
            )
            return 0

    def delete_submission_files(self, submission: Submission) -> int:
        """Delete all files associated with a submission from S3 by deleting the folder."""
        submission_space = self.calculate_submission_space(submission)
        if self.dry_run:
            self.logger.info(
                "🔍 DRY RUN: Processing submission %s", submission.id
            )
            if submission_space > 0:
                self.logger.info(
                    "  🔍 Would free %s", self.format_bytes(submission_space)
                )

        # Delete submission folder within the main bucket
        deleted_object_count = self.delete_submission_folder(submission)

        if not self.dry_run and deleted_object_count > 0:
            self.total_space_freed += submission_space

        return deleted_object_count

    def delete_submissions_files(self, submissions: List[Submission]) -> tuple:
        """Delete files from S3 for multiple submissions.
        Returns (submission_count, file_count, aws_error_count, no_files_count).
        """
        if not submissions:
            return (0, 0, 0, 0)

        if self.dry_run:
            # In dry run, we need to count the actual files that would be deleted
            total_files_to_delete = 0
            aws_error_count = 0
            no_files_count = 0
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
                        self.logger.debug(
                            "🔍 No files found for submission %s with prefix: %s",
                            submission.id,
                            prefix,
                        )
                    else:
                        self.logger.debug(
                            "🔍 Found %s files for submission %s",
                            len(objects_to_count),
                            submission.id,
                        )
                        submission_folders_to_delete.append(
                            f"media/submission_files/submission_{submission.id}/"
                        )

                    total_files_to_delete += len(objects_to_count)
                except Exception as e:
                    aws_error_count += 1
                    self.logger.warning(
                        "⚠️ Could not count files for submission %s: %s",
                        submission.id,
                        str(e),
                    )
                    continue

            # Log the folders that will be deleted
            if submission_folders_to_delete:
                self.logger.info(
                    "📁 DRY RUN: Submission folders that would be deleted:"
                )
                for folder in submission_folders_to_delete:
                    self.logger.info("   📁 %s", folder)
            else:
                self.logger.info(
                    "📁 DRY RUN: No submission folders found to delete"
                )

            self.logger.info(
                "🔍 DRY RUN: Would delete %s files from %s submissions",
                total_files_to_delete,
                len(submissions),
            )
            if aws_error_count > 0:
                self.logger.warning(
                    "⚠️ DRY RUN: %s submissions failed due to AWS errors (bucket/credential issues)",
                    aws_error_count,
                )
            if no_files_count > 0:
                self.logger.info(
                    "ℹ️ DRY RUN: %s submissions had no files to delete",
                    no_files_count,
                )
            return (
                len(submissions),
                total_files_to_delete,
                aws_error_count,
                no_files_count,
            )

        deleted_count = 0
        total_objects_deleted = 0
        aws_error_count = 0
        no_files_count = 0
        deleted_folders = []  # Track folders that are actually deleted

        for submission in submissions:
            try:
                # Calculate space before deletion for logging
                submission_space = self.calculate_submission_space(submission)

                # Log before deletion
                if not self.dry_run:
                    self.logger.info(
                        "🗑️ Deleting files from submission %s "
                        "(Challenge: %s, Phase: %s, Status: %s, "
                        "Submitted: %s, Space: %s)",
                        submission.id,
                        submission.challenge_phase.challenge.title,
                        submission.challenge_phase.name,
                        submission.status,
                        submission.submitted_at,
                        self.format_bytes(submission_space),
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
                    self.logger.info(
                        "✅ Processed submission %s, deleted %s objects.",
                        submission.id,
                        deleted_objects,
                    )

            except Exception as e:
                aws_error_count += 1
                self.logger.error(
                    "❌ Error processing submission %s: %s",
                    submission.id,
                    str(e),
                )
                continue

        # Log the folders that were actually deleted
        if not self.dry_run and deleted_folders:
            self.logger.info(
                "📁 EXECUTE: Submission folders that were deleted:"
            )
            for folder in deleted_folders:
                self.logger.info("   📁 %s", folder)
        elif not self.dry_run:
            self.logger.info("📁 EXECUTE: No submission folders were deleted")

        if self.dry_run:
            self.logger.info(
                "🔍 DRY RUN: Would delete %s objects from %s submissions.",
                total_objects_deleted,
                deleted_count,
            )

        if aws_error_count > 0:
            self.logger.warning(
                "⚠️ %s submissions failed due to AWS errors (bucket/credential issues)",
                aws_error_count,
            )
        if no_files_count > 0:
            self.logger.info(
                "ℹ️ %s submissions had no files to delete", no_files_count
            )

        return (
            deleted_count,
            total_objects_deleted,
            aws_error_count,
            no_files_count,
        )

    def run(self) -> Dict[str, Any]:
        """Main method to run the deletion process."""
        self.logger.info(
            "🚀 Starting expired submission files deletion process"
        )
        if self.not_approved_by_admin:
            self.logger.info(
                "📅 Mode: Challenges not approved by admin and older than 30 days "
                "(approved_by_admin=False, created_at < 30 days ago)"
            )
        elif self.past_challenges_min_days is not None:
            self.logger.info(
                "📅 Mode: Past challenges with minimum %s days",
                self.past_challenges_min_days,
            )
        elif self.past_challenges_only:
            self.logger.info(
                "📅 Mode: Past challenges only " "(all ended challenges)"
            )
        else:
            self.logger.info(
                "📅 Deletion cutoff date: %s", self.deletion_cutoff_date
            )
        self.logger.info("🔍 Dry run: %s", self.dry_run)

        # Get expired challenges
        expired_challenges = self.get_expired_challenges()

        if not expired_challenges:
            self.logger.info("❌ No expired challenges found")
            return {
                "deleted_count": 0,  # No submissions to delete
                "challenges_processed": 0,
                "challenges_skipped": 0,
                "submissions_with_aws_errors": 0,
                "submissions_with_no_files": 0,
                "total_challenges_found": 0,
                "space_freed": 0,  # No space to free
                "files_deleted": 0,  # No files to delete
                "cutoff_date": (
                    self.deletion_cutoff_date
                    if (
                        not self.past_challenges_only
                        and not self.past_challenges_min_days
                        and not self.not_approved_by_admin
                    )
                    else (
                        "ALL_PAST_CHALLENGES"
                        if not self.not_approved_by_admin
                        else "NOT_APPROVED_BY_ADMIN"
                    )
                ),
            }

        total_deleted = 0  # Count of submissions that would be deleted (dry run) or were deleted (execute)
        challenges_processed = 0
        challenges_skipped = 0  # Count of challenges with no submissions
        submissions_with_aws_errors = (
            0  # Count of submissions that failed due to AWS issues
        )
        submissions_with_no_files = (
            0  # Count of submissions that had no files to delete
        )
        total_space_freed = (
            0  # Space that would be freed (dry run) or was freed (execute)
        )
        total_files_deleted = 0  # Count of individual files that would be deleted (dry run) or were deleted (execute)
        total_challenges_found = len(
            expired_challenges
        )  # Total challenges matching criteria

        for challenge in expired_challenges:
            self.logger.info(
                "📊 Processing challenge: %s (ID: %s)",
                challenge.title,
                challenge.id,
            )
            self.logger.info("📅 Challenge ended: %s", challenge.end_date)
            self.logger.info(
                "⏰ Days since expiration: %s",
                (timezone.now() - challenge.end_date).days,
            )

            # Get submissions for this challenge
            submissions = self.get_submissions_for_challenge(challenge)

            if not submissions:
                self.logger.info("❌ No submissions found for this challenge")
                challenges_skipped += 1
                continue

            # Get and log statistics
            stats = self.get_submission_stats(submissions)
            self.logger.info("📈 Submission statistics:")
            self.logger.info("  Total submissions: %s", stats["total"])
            self.logger.info("  Oldest submission: %s", stats["oldest"])
            self.logger.info("  Newest submission: %s", stats["newest"])
            self.logger.info(
                "  Total space used: %s",
                self.format_bytes(stats["total_space"]),
            )
            self.logger.info("  By status: %s", stats["by_status"])
            self.logger.info("  By phase: %s", stats["by_phase"])

            # Log space breakdown by status
            if stats["space_by_status"]:
                self.logger.info("  💾 Space by status:")
                for status, space in stats["space_by_status"].items():
                    self.logger.info(
                        "    %s: %s", status, self.format_bytes(space)
                    )

            # Log space breakdown by phase
            if stats["space_by_phase"]:
                self.logger.info("  📁 Space by phase:")
                for phase, space in stats["space_by_phase"].items():
                    self.logger.info(
                        "    %s: %s", phase, self.format_bytes(space)
                    )

            # Delete submission files
            deleted_count, files_deleted, aws_errors, no_files = (
                self.delete_submissions_files(submissions)
            )

            total_deleted += deleted_count
            total_files_deleted += files_deleted
            submissions_with_aws_errors += aws_errors
            submissions_with_no_files += no_files
            total_space_freed += stats["total_space"]
            challenges_processed += 1

            if self.dry_run:
                self.logger.info(
                    "🔍 DRY RUN: Would delete files from %s "
                    "submissions from challenge %s",
                    deleted_count,
                    challenge.title,
                )
            else:
                self.logger.info(
                    "🗑️ Deleted files from %s submissions from challenge %s",
                    deleted_count,
                    challenge.title,
                )
            if self.dry_run:
                self.logger.info(
                    "💾 DRY RUN: Space that would be freed: %s",
                    self.format_bytes(stats["total_space"]),
                )
            else:
                self.logger.info(
                    "💾 Space freed: %s",
                    self.format_bytes(stats["total_space"]),
                )

        self.logger.info("🎉 Deletion process completed!")
        self.logger.info("📊 SUMMARY:")
        self.logger.info(
            "  Total challenges found: %s", total_challenges_found
        )
        self.logger.info("  Challenges processed: %s", challenges_processed)
        self.logger.info(
            "  Challenges skipped (no submissions): %s", challenges_skipped
        )
        self.logger.info(
            "  Verification: %s + %s = %s ✓",
            challenges_processed,
            challenges_skipped,
            challenges_processed + challenges_skipped,
        )

        if submissions_with_aws_errors > 0:
            self.logger.warning(
                "  ⚠️ Submissions with AWS errors: %s",
                submissions_with_aws_errors,
            )
        if submissions_with_no_files > 0:
            self.logger.info(
                "  ℹ️ Submissions with no files: %s", submissions_with_no_files
            )

        if self.dry_run:
            self.logger.info(
                "🔍 DRY RUN: Total submissions that would have files deleted: %s",
                total_deleted,
            )
            self.logger.info(
                "🔍 DRY RUN: Total files that would be deleted: %s",
                total_files_deleted,
            )
            self.logger.info(
                "💾 DRY RUN: Total space that would be freed: %s",
                self.format_bytes(total_space_freed),
            )
        else:
            self.logger.info(
                "🗑️ Total submissions with files deleted: %s", total_deleted
            )
            self.logger.info("🗑️ Total files deleted: %s", total_files_deleted)
            self.logger.info(
                "💾 Total space freed: %s",
                self.format_bytes(total_space_freed),
            )

        return {
            # Count of submissions that would be deleted (dry run) or were deleted (execute)
            "deleted_count": total_deleted,
            "challenges_processed": challenges_processed,
            "challenges_skipped": challenges_skipped,
            "submissions_with_aws_errors": submissions_with_aws_errors,
            "submissions_with_no_files": submissions_with_no_files,
            "total_challenges_found": total_challenges_found,
            "cutoff_date": (
                self.deletion_cutoff_date
                if (
                    not self.past_challenges_only
                    and not self.past_challenges_min_days
                    and not self.not_approved_by_admin
                )
                else (
                    "ALL_PAST_CHALLENGES"
                    if not self.not_approved_by_admin
                    else "NOT_APPROVED_BY_ADMIN"
                )
            ),
            # Space that would be freed (dry run) or was freed (execute)
            "space_freed": total_space_freed,
            # Count of individual files that would be deleted (dry run) or were deleted (execute)
            "files_deleted": total_files_deleted,
        }


def main():
    """Main function to parse arguments and run the deletion process."""
    # Test Django configuration
    try:
        early_logger.info(
            "Django Setting Module: %s", os.getenv("DJANGO_SETTINGS_MODULE")
        )
        early_logger.info(
            "Database: %s", settings.DATABASES["default"]["ENGINE"]
        )
    except Exception as e:
        early_logger.error("Django configuration error: %s", str(e))
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="Clean up expired submission files from EvalAI challenges or list challenges by category. "
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
        help="Number of days after challenge end date to consider for cleanup "
        "(e.g., 365 for 1 year, 180 for 6 months). Required unless --past-challenges-only is used.",
    )

    parser.add_argument(
        "--past-challenges-only",
        action="store_true",
        help="Delete submission folders from ALL past challenges (regardless of when they ended). "
        "This ignores the --days parameter and processes all challenges where end_date < current_time.",
    )

    parser.add_argument(
        "--past-challenges-min-days",
        type=int,
        help="Delete submission folders from past challenges that ended at least N days ago. "
        "This processes challenges where end_date < (current_time - N days). "
        "Example: --past-challenges-min-days 90 will process challenges that ended 90+ days ago.",
    )

    parser.add_argument(
        "--not-approved-by-admin",
        action="store_true",
        help="Delete submission folders from challenges where approved_by_admin=False "
        "and created more than 30 days ago. This processes challenges that have not "
        "been approved by admin and are older than 30 days.",
    )

    parser.add_argument(
        "--challenge-id", type=int, help="Only process a specific challenge ID"
    )

    parser.add_argument(
        "--list-challenges",
        action="store_true",
        help="List challenges by category (ongoing, past, upcoming, not approved) sorted by S3 space usage and exit",
    )

    args = parser.parse_args()

    # Handle list challenges command
    if args.list_challenges:
        # Set up basic logging for list command
        setup_logging(dry_run=True)

        # Create deleter instance for listing
        deleter = ExpiredSubmissionsDeleter(dry_run=True)

        try:
            deleter.list_challenges()
            early_logger.info("✅ Challenge listing completed successfully!")
        except Exception as e:
            early_logger.error("❌ Error during challenge listing: %s", str(e))
            early_logger.error("📋 Traceback: %s", traceback.format_exc())
            sys.exit(1)

        sys.exit(0)

    # Validate arguments for cleanup operations
    if not args.dry_run and not args.execute:
        early_logger.error("You must specify either --dry-run or --execute")
        sys.exit(1)

    if args.dry_run and args.execute:
        early_logger.error("You cannot specify both --dry-run and --execute")
        sys.exit(1)

    if (
        not args.past_challenges_only
        and not args.days
        and not args.past_challenges_min_days
        and not args.not_approved_by_admin
    ):
        early_logger.error(
            "You must specify either --days, --past-challenges-only, "
            "--past-challenges-min-days, or --not-approved-by-admin"
        )
        sys.exit(1)

    if args.past_challenges_only and args.days:
        early_logger.warning(
            "--past-challenges-only specified, ignoring --days parameter"
        )

    if args.past_challenges_min_days and args.days:
        early_logger.warning(
            "--past-challenges-min-days specified, ignoring --days parameter"
        )

    if args.past_challenges_only and args.past_challenges_min_days:
        early_logger.warning(
            "--past-challenges-min-days specified, ignoring --past-challenges-only parameter"
        )

    if args.not_approved_by_admin and args.days:
        early_logger.warning(
            "--not-approved-by-admin specified, ignoring --days parameter"
        )

    if args.not_approved_by_admin and args.past_challenges_only:
        early_logger.warning(
            "--not-approved-by-admin specified, ignoring --past-challenges-only parameter"
        )

    if args.not_approved_by_admin and args.past_challenges_min_days:
        early_logger.warning(
            "--not-approved-by-admin specified, ignoring "
            "--past-challenges-min-days parameter"
        )

    # Set up proper logging with CloudWatch enabled
    setup_logging(dry_run=args.dry_run)

    # Create deleter instance
    deleter = ExpiredSubmissionsDeleter(
        dry_run=args.dry_run,
        past_challenges_only=args.past_challenges_only,
        past_challenges_min_days=args.past_challenges_min_days,
        not_approved_by_admin=args.not_approved_by_admin,
    )

    # Set the cutoff date based on the required days argument
    # (only if not using past_challenges_only, past_challenges_min_days, or not_approved_by_admin)
    if (
        not args.past_challenges_only
        and not args.past_challenges_min_days
        and not args.not_approved_by_admin
    ):
        if args.days <= 0:
            early_logger.error(
                "Days argument must be positive (e.g., 365 for 1 year, "
                "180 for 6 months)"
            )
            sys.exit(1)

        deleter.deletion_cutoff_date = timezone.now() - timedelta(
            days=args.days
        )
        early_logger.info(
            "🔧 Using cutoff: %s days ago (%s)",
            args.days,
            deleter.deletion_cutoff_date,
        )
    elif args.past_challenges_min_days:
        # For past_challenges_min_days, we don't need a cutoff date
        deleter.deletion_cutoff_date = None
        early_logger.info(
            "🔧 Processing past challenges that ended at least %s days ago",
            args.past_challenges_min_days,
        )
    elif args.not_approved_by_admin:
        # For not_approved_by_admin, we don't need a cutoff date
        deleter.deletion_cutoff_date = None
        early_logger.info(
            "🔧 Processing challenges not approved by admin and older than 30 days "
            "(approved_by_admin=False, created_at < 30 days ago)"
        )
    else:
        # For past_challenges_only, we don't need a cutoff date
        deleter.deletion_cutoff_date = None
        early_logger.info(
            "🔧 Processing ALL past challenges (end_date < %s)",
            timezone.now(),
        )

    # Run the deletion process
    try:
        result = deleter.run()

        if args.dry_run:
            early_logger.info(
                "🔍 DRY RUN COMPLETED - No actual deletions were performed"
            )
        else:
            early_logger.info(
                "✅ DELETION COMPLETED - Submission files have been deleted"
            )

        early_logger.info("\n" + "=" * 50)
        early_logger.info("SUMMARY")
        early_logger.info("=" * 50)
        early_logger.info(
            "Total challenges found: %s", result["total_challenges_found"]
        )
        early_logger.info(
            "Challenges processed: %s", result["challenges_processed"]
        )
        early_logger.info(
            "Challenges skipped (no submissions): %s",
            result["challenges_skipped"],
        )
        early_logger.info(
            "Verification: %s + %s = %s ✓",
            result["challenges_processed"],
            result["challenges_skipped"],
            result["challenges_processed"] + result["challenges_skipped"],
        )

        if result["submissions_with_aws_errors"] > 0:
            early_logger.warning(
                "Submissions with AWS errors: %s",
                result["submissions_with_aws_errors"],
            )
        if result["submissions_with_no_files"] > 0:
            early_logger.info(
                "Submissions with no files: %s",
                result["submissions_with_no_files"],
            )

        if args.dry_run:
            early_logger.info(
                "Submissions that would have files deleted: %s",
                result["deleted_count"],
            )
            early_logger.info(
                "Files that would be deleted: %s", result["files_deleted"]
            )
            early_logger.info(
                "Space that would be freed: %s",
                deleter.format_bytes(result["space_freed"]),
            )
        else:
            early_logger.info(
                "Submissions with files deleted: %s", result["deleted_count"]
            )
            early_logger.info("Files deleted: %s", result["files_deleted"])
            early_logger.info(
                "Space freed: %s", deleter.format_bytes(result["space_freed"])
            )

        if (
            not args.past_challenges_only
            and not args.past_challenges_min_days
            and not args.not_approved_by_admin
        ):
            early_logger.info("Cutoff date: %s", result["cutoff_date"])
        elif args.past_challenges_min_days:
            early_logger.info(
                "Mode: Past challenges with minimum %s days",
                args.past_challenges_min_days,
            )
        elif args.not_approved_by_admin:
            early_logger.info(
                "Mode: Challenges not approved by admin and older than 30 days "
                "(approved_by_admin=False, created_at < 30 days ago)"
            )
        else:
            early_logger.info(
                "Mode: Past challenges only (all ended challenges)"
            )
        early_logger.info("=" * 50)

    except Exception as e:
        early_logger.error("❌ Error during deletion process: %s", str(e))
        early_logger.error("📋 Traceback: %s", traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
