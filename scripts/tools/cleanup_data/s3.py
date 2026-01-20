#!/usr/bin/env python
"""
Cleanup S3 files for challenges - Memory Optimized for 1GB RAM.

Cleans up files from S3 folders (see constants section for folder names):
    - LOGOS_FOLDER/ (Challenge.image) - NOTE: Logos are NOT deleted by this script
    - EVALUATION_SCRIPTS_FOLDER/ (Challenge.evaluation_script) - NOTE: NOT deleted by this script
    - TEST_ANNOTATIONS_FOLDER/ (ChallengePhase.test_annotation) - NOTE: NOT deleted by this script
    - SUBMISSION_FILES_FOLDER/ (Submission files)
    - ZIP_CONFIGURATION_FILES_FOLDER/ (ChallengeConfiguration files)
    - CLUSTER_YAML_FOLDER/ (ChallengeEvaluationCluster.cluster_yaml) - NOTE: NOT deleted by this script
    - KUBE_CONFIG_FOLDER/ (ChallengeEvaluationCluster.kube_config) - NOTE: NOT deleted by this script

Memory Optimization Strategy:
    - Uses values_list() to fetch only file paths, not full objects
    - Skips S3 existence checks (we're deleting anyway)
    - Processes submissions in streaming batches
    - Minimal logging per file (summary only)
    - Aggressive garbage collection

Usage:
    # Dry run (default) - show what would be deleted
    python scripts/tools/cleanup_data/s3.py --challenge-ids 1 2 3

    # Execute - actually delete files
    python scripts/tools/cleanup_data/s3.py --challenge-ids 1 2 3 --execute

Output:
    Creates a log file: scripts/tools/cleanup_data/cleanup_YYYYMMDD_HHMMSS.log

Progress bar:
    If tqdm is installed, progress bars will be shown for challenges,
    submissions, and S3 delete batches.

Run from project root in an environment with database access.
"""

import argparse
import gc
import os
import sys
import time
from datetime import datetime

# =============================================================================
# CONFIGURATION - Edit these constants as needed
# =============================================================================
# S3 prefix - set this if default_storage.location is not configured
# Leave empty to auto-detect from Django settings
MEDIA_PREFIX = "media"

# S3 folder names (relative to MEDIA_PREFIX)
# These correspond to the FileField upload_to paths in the models
LOGOS_FOLDER = "logos"  # Challenge.image (NOT deleted by this script)
EVALUATION_SCRIPTS_FOLDER = "evaluation_scripts"  # Challenge.evaluation_script
TEST_ANNOTATIONS_FOLDER = "test_annotations"  # ChallengePhase.test_annotation
SUBMISSION_FILES_FOLDER = "submission_files"  # Submission files
ZIP_CONFIGURATION_FILES_FOLDER = (
    "zip_configuration_files"  # ChallengeConfiguration files
)
CLUSTER_YAML_FOLDER = "cluster_yaml"  # ChallengeEvaluationCluster.cluster_yaml
KUBE_CONFIG_FOLDER = "kube_config"  # ChallengeEvaluationCluster.kube_config

# Batch sizes optimized for 1GB RAM
SUBMISSION_BATCH_SIZE = 5000  # For DB queries (just path strings, low memory)
S3_DELETE_BATCH_SIZE = 1000  # Max objects per S3 delete_objects call
# =============================================================================

try:
    from tqdm import tqdm

    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Setup paths (for running outside container)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))

# Setup Django - skip if already configured (running inside Django container)
import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    django.setup()

# Disable query logging to save memory (critical in containers)
settings.DEBUG = False
from django.db import connection, reset_queries  # noqa: E402

if hasattr(connection, "queries_log"):
    connection.queries_log.clear()

import boto3  # noqa: E402
from challenges.models import (  # noqa: E402
    Challenge,
    ChallengeConfiguration,
    ChallengePhase,
)
from django.core.files.storage import default_storage  # noqa: E402
from jobs.models import Submission  # noqa: E402


class Logger:
    """Simple logger that writes to both console and file."""

    def __init__(self, log_file_path):
        self.log_file = open(log_file_path, "w", buffering=1)  # Line buffered
        self.log_file_path = log_file_path

    def log(self, message=""):
        print(message)
        self.log_file.write(message + "\n")

    def close(self):
        self.log_file.close()


def format_size(size_bytes):
    """Convert bytes to human readable format."""
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def format_duration(seconds):
    """Convert seconds to human readable duration format."""
    if seconds < 60:
        return f"{seconds:.1f} seconds"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f} minutes"
    else:
        hours = seconds / 3600
        return f"{hours:.2f} hours"


def get_s3_client_and_bucket():
    """Get boto3 S3 client and bucket name from django-storages settings."""
    bucket_name = getattr(default_storage, "bucket_name", None)
    if not bucket_name:
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    s3_client = boto3.client("s3")
    return s3_client, bucket_name


def get_s3_key(path):
    """Convert database path to full S3 key (add media/ prefix if needed)."""
    location = getattr(default_storage, "location", "") or MEDIA_PREFIX

    if not location:
        return path

    location_normalized = location.rstrip("/")

    if path.startswith(f"{location_normalized}/"):
        return path

    return f"{location_normalized}/{path}"


def get_file_sizes_from_s3(file_paths, logger, dry_run=True):
    """
    Get file sizes from S3 using HEAD requests.

    Memory optimized: Processes in batches to avoid memory spikes.
    Returns: list of tuples (path, size) or (path, None) if not found

    Note: Sizes are calculated in both dry run and execute modes.
    """
    if not file_paths:
        return []

    s3_client, bucket_name = get_s3_client_and_bucket()
    if not bucket_name:
        logger.log(
            "  [WARNING] Could not determine S3 bucket name - skipping size calculation"
        )
        return [(path, None) for path in file_paths]

    file_sizes = []
    total = len(file_paths)

    logger.log(f"  Getting file sizes from S3 for {total} files...")

    # Process in batches to avoid too many concurrent requests
    batch_size = (
        100  # HEAD requests are lightweight, so smaller batches are fine
    )
    batch_range = range(0, total, batch_size)

    if TQDM_AVAILABLE:
        batch_range = tqdm(
            batch_range,
            desc="Getting sizes",
            unit="batch",
            total=(total + batch_size - 1) // batch_size,
        )

    for i in batch_range:
        batch = file_paths[i : i + batch_size]  # noqa: E203

        for path in batch:
            key = get_s3_key(path)
            try:
                response = s3_client.head_object(Bucket=bucket_name, Key=key)
                size = response.get("ContentLength", 0)
                file_sizes.append((path, size))
            except Exception:
                # If HEAD fails, just continue (file might not exist or be inaccessible)
                # Don't log every failure to avoid log spam - just mark as None
                file_sizes.append((path, None))

        gc.collect()

    return file_sizes


def bulk_delete_s3_files(file_paths, logger, dry_run=True):
    """
    Delete files in bulk using S3 delete_objects API.

    Memory optimized: Processes paths in batches, clears after each batch.
    """
    if not file_paths:
        return 0, 0

    total_files = len(file_paths)

    if dry_run:
        logger.log(f"\n  [DRY RUN] Would delete {total_files} files in bulk")
        return total_files, 0

    s3_client, bucket_name = get_s3_client_and_bucket()
    if not bucket_name:
        logger.log("  [ERROR] Could not determine S3 bucket name")
        return 0, total_files

    location = getattr(default_storage, "location", "") or MEDIA_PREFIX
    logger.log(f"  Using bucket: {bucket_name}, prefix: '{location}'")

    if file_paths:
        sample_path = file_paths[0]
        sample_key = get_s3_key(sample_path)
        logger.log(
            f"  Sample path conversion: '{sample_path}' -> '{sample_key}'"
        )

    deleted = 0
    failed = 0
    total_batches = (
        total_files + S3_DELETE_BATCH_SIZE - 1
    ) // S3_DELETE_BATCH_SIZE

    batch_range = range(0, total_files, S3_DELETE_BATCH_SIZE)
    if TQDM_AVAILABLE:
        batch_range = tqdm(
            batch_range,
            desc="Deleting S3 files",
            unit="batch",
            total=total_batches,
        )

    for i in batch_range:
        batch = file_paths[i : i + S3_DELETE_BATCH_SIZE]  # noqa: E203
        objects_to_delete = [{"Key": get_s3_key(path)} for path in batch]

        try:
            response = s3_client.delete_objects(
                Bucket=bucket_name, Delete={"Objects": objects_to_delete}
            )
            deleted_count = len(response.get("Deleted", []))
            error_count = len(response.get("Errors", []))
            deleted += deleted_count
            failed += error_count

            if error_count > 0:
                for error in response.get("Errors", [])[
                    :3
                ]:  # Log first 3 errors only
                    logger.log(
                        f"  [ERROR] Failed to delete {error['Key']}: {error['Message']}"
                    )

            logger.log(
                f"  [BULK DELETE] Batch {i//S3_DELETE_BATCH_SIZE + 1}: {deleted_count} deleted, {error_count} failed"
            )
        except Exception as e:
            logger.log(f"  [ERROR] Bulk delete failed: {e}")
            failed += len(batch)

        gc.collect()

    return deleted, failed


def collect_challenge_files_optimized(challenge_id, logger):
    """
    Collect all file paths for a challenge.

    Memory optimized: Uses values_list() to fetch only path strings,
    skips S3 existence checks (unnecessary for deletion).

    Returns: list of file paths
    """
    all_paths = []

    # Verify challenge exists
    if not Challenge.objects.filter(pk=challenge_id).exists():
        logger.log(
            f"\n[ERROR] Challenge {challenge_id} does not exist - skipping"
        )
        return None

    # Get challenge title for logging
    challenge_title = (
        Challenge.objects.filter(pk=challenge_id)
        .values_list("title", flat=True)
        .first()
    )

    logger.log(f"\n{'='*60}")
    logger.log(f"Challenge: {challenge_title} (ID: {challenge_id})")
    logger.log(f"{'='*60}")

    # 1. Challenge files - skip image/logos and evaluation_script (not deleting them)
    logger.log(
        f"\n  [Challenge] Skipping: image/{LOGOS_FOLDER} and evaluation_script (not deleted)"
    )

    # 2. ChallengePhase files - skip test_annotation (not deleting them)
    phase_count = ChallengePhase.objects.filter(
        challenge_id=challenge_id
    ).count()
    logger.log(
        f"\n  [ChallengePhase] {phase_count} phases (skipping test_annotation files)"
    )

    gc.collect()
    reset_queries()

    # 3. Submission files - largest, process field by field with streaming
    submission_count = Submission.objects.filter(
        challenge_phase__challenge_id=challenge_id
    ).count()
    logger.log(f"\n  [Submission] {submission_count} submissions")

    submission_fields = [
        "input_file",
        "submission_input_file",
        "stdout_file",
        "stderr_file",
        "environment_log_file",
        "submission_result_file",
        "submission_metadata_file",
    ]

    submission_files_count = 0
    for field in submission_fields:
        paths = (
            Submission.objects.filter(
                challenge_phase__challenge_id=challenge_id
            )
            .exclude(**{f"{field}__isnull": True})
            .exclude(**{field: ""})
            .values_list(field, flat=True)
        )

        # Stream in batches to avoid memory spike
        field_count = 0
        for path in paths.iterator(chunk_size=SUBMISSION_BATCH_SIZE):
            all_paths.append(path)
            field_count += 1
            if field_count % 10000 == 0:
                gc.collect()
                reset_queries()

        submission_files_count += field_count

        gc.collect()
        reset_queries()

    logger.log(f"    Found {submission_files_count} submission files")

    # 4. ChallengeConfiguration files
    logger.log("\n  [ChallengeConfiguration]")
    config_fields = ["zip_configuration", "stdout_file", "stderr_file"]
    config_count = 0

    for field in config_fields:
        path = (
            ChallengeConfiguration.objects.filter(challenge_id=challenge_id)
            .exclude(**{f"{field}__isnull": True})
            .exclude(**{field: ""})
            .values_list(field, flat=True)
            .first()
        )

        if path:
            all_paths.append(path)
            config_count += 1

    if config_count > 0:
        logger.log(f"    Found {config_count} configuration files")
    else:
        logger.log("    [SKIP] No ChallengeConfiguration found")

    # 5. ChallengeEvaluationCluster files - skip cluster_yaml and kube_config (not deleting them)
    logger.log(
        "\n  [ChallengeEvaluationCluster] Skipping: cluster_yaml and kube_config (not deleted)"
    )

    logger.log(f"\n  Challenge Total: {len(all_paths)} files to delete")

    gc.collect()
    reset_queries()

    return all_paths


def main():
    start_time = time.time()

    parser = argparse.ArgumentParser(
        description="Cleanup S3 files for challenges"
    )
    parser.add_argument(
        "--challenge-ids",
        type=int,
        nargs="+",
        required=True,
        help="Challenge IDs to process",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete files (default is dry run)",
    )
    args = parser.parse_args()

    dry_run = not args.execute

    # Create log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(SCRIPT_DIR, f"cleanup_{timestamp}.log")
    logger = Logger(log_file_path)

    logger.log("=" * 60)
    logger.log(f"S3 Cleanup - {'DRY RUN' if dry_run else 'EXECUTE'}")
    logger.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.log(
        f"Challenge IDs: {len(args.challenge_ids)} challenges ({min(args.challenge_ids)} to {max(args.challenge_ids)})"
    )
    logger.log(f"Log file: {log_file_path}")
    logger.log("=" * 60)
    logger.log("\n[Memory Optimized for 1GB RAM]")

    if dry_run:
        logger.log("\n*** DRY RUN - No files will be deleted ***")
        logger.log("*** Use --execute to actually delete files ***")

    total_stats = {
        "files_found": 0,
        "files_deleted": 0,
        "files_failed": 0,
        "size": 0,
        "processed": 0,
        "skipped": 0,
    }

    # Collect all files from all challenges
    all_files_to_delete = []

    challenge_ids = args.challenge_ids
    if TQDM_AVAILABLE:
        challenge_ids = tqdm(
            challenge_ids, desc="Collecting files", unit="challenge"
        )

    for challenge_id in challenge_ids:
        file_paths = collect_challenge_files_optimized(challenge_id, logger)

        if file_paths is None:
            total_stats["skipped"] += 1
            continue

        all_files_to_delete.extend(file_paths)
        total_stats["files_found"] += len(file_paths)
        total_stats["processed"] += 1

        # Free memory after each challenge
        gc.collect()
        reset_queries()
        connection.close()

    # Calculate total size (get sizes from S3 for both dry run and execute)
    logger.log(f"\n{'='*60}")
    logger.log("SIZE CALCULATION PHASE")
    logger.log(f"{'='*60}")
    logger.log(f"Total files to delete: {len(all_files_to_delete)}")
    logger.log("  Getting file sizes from S3...")

    file_sizes = get_file_sizes_from_s3(
        all_files_to_delete, logger, dry_run=dry_run
    )
    total_size = sum(size for _, size in file_sizes if size is not None)
    files_with_size = sum(1 for _, size in file_sizes if size is not None)
    files_without_size = len(all_files_to_delete) - files_with_size

    logger.log(
        f"Total size {'to free' if dry_run else 'freed'}: {format_size(total_size)}"
    )
    if files_without_size > 0:
        logger.log(
            f"  Note: {files_without_size} files could not be sized (may not exist in S3)"
        )

    # Bulk delete all collected files
    logger.log(f"\n{'='*60}")
    logger.log("BULK DELETE PHASE")
    logger.log(f"{'='*60}")
    logger.log(f"Total files to delete: {len(all_files_to_delete)}")

    deleted, failed = bulk_delete_s3_files(
        all_files_to_delete, logger, dry_run
    )
    total_stats["files_deleted"] = deleted
    total_stats["files_failed"] = failed
    total_stats["size"] = total_size

    # Summary
    logger.log("\n" + "=" * 60)
    logger.log("FINAL SUMMARY")
    logger.log("=" * 60)
    logger.log(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    logger.log(f"Challenges processed: {total_stats['processed']}")
    logger.log(f"Challenges skipped (not found): {total_stats['skipped']}")
    logger.log(f"Files found: {total_stats['files_found']}")
    logger.log(
        f"Files {'to delete' if dry_run else 'deleted'}: {total_stats['files_deleted']}"
    )
    if not dry_run:
        logger.log(f"Files failed to delete: {total_stats['files_failed']}")
    if total_stats.get("size", 0) > 0:
        logger.log(
            f"Space {'to free' if dry_run else 'freed'}: {format_size(total_stats['size'])}"
        )
    elapsed_time = time.time() - start_time
    logger.log(f"Execution time: {format_duration(elapsed_time)}")
    logger.log(f"Log file: {log_file_path}")
    logger.log("=" * 60)

    logger.close()
    print(f"\nLog saved to: {log_file_path}")


if __name__ == "__main__":
    main()
