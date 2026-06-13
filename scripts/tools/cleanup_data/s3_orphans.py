#!/usr/bin/env python
"""
Cleanup orphaned S3 files - Memory Optimized for 1GB RAM.

This script keeps all files referenced in the database and deletes
any files in S3 that are not referenced by any challenge, phase,
submission, configuration, or cluster.

Memory Optimization Strategy:
    - Uses values_list() to fetch only file paths, not full objects
    - Streams S3 files and checks immediately (no list accumulation)
    - Writes orphan keys to temp file instead of memory
    - Processes deletions in streaming batches
    - Aggressive garbage collection

S3 folders scanned (under MEDIA_PREFIX):
    - logos/
    - evaluation_scripts/
    - test_annotations/
    - submission_files/
    - zip_configuration_files/
    - cluster_yaml/
    - kube_config/

Configuration:
    Edit MEDIA_PREFIX and S3_FOLDER_NAMES at the top of the script
    to adapt for different bucket structures.

Usage:
    # Dry run (default) - show what would be deleted
    python scripts/tools/cleanup_data/s3_orphans.py

    # Execute - actually delete orphaned files
    python scripts/tools/cleanup_data/s3_orphans.py --execute

Progress bar:
    If tqdm is installed, progress bars will be shown.

Run from project root in an environment with database access.
"""

import argparse
import gc
import os
import sys
import tempfile
import time
from datetime import datetime

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
    ChallengeEvaluationCluster,
    ChallengePhase,
)
from django.core.files.storage import default_storage  # noqa: E402
from jobs.models import Submission  # noqa: E402

# =============================================================================
# CONFIGURATION - Change these for different environments/buckets
# =============================================================================
# S3 prefix (typically "media/" - change if your bucket uses a different prefix)
MEDIA_PREFIX = "media/"

# Folder names to scan (relative to MEDIA_PREFIX)
S3_FOLDER_NAMES = [
    "logos",
    "evaluation_scripts",
    "test_annotations",
    "submission_files",
    "zip_configuration_files",
    "cluster_yaml",
    "kube_config",
]

# Build full paths
S3_FOLDERS = [f"{MEDIA_PREFIX}{folder}/" for folder in S3_FOLDER_NAMES]
# =============================================================================

# Batch sizes optimized for 1GB RAM
DB_BATCH_SIZE = (
    5000  # Larger batches for values_list (just strings, low memory)
)
S3_DELETE_BATCH_SIZE = 1000  # Max objects per S3 delete_objects call


class Logger:
    """Simple logger that writes to both console and file."""

    def __init__(self, log_file_path):
        self.log_file = open(log_file_path, "w", buffering=1)
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


def collect_db_file_paths_optimized(logger):
    """
    Collect all file paths referenced in the database.

    Memory optimized: Uses values_list() to fetch only path strings,
    and normalizes paths in a single set with both prefix forms.
    """
    referenced_paths = set()
    prefix_len = len(MEDIA_PREFIX)

    def add_path_normalized(path):
        """Add path in both forms (with and without MEDIA_PREFIX) for fast lookup."""
        if not path:
            return
        referenced_paths.add(path)
        # Also add alternate form for matching
        if path.startswith(MEDIA_PREFIX):
            referenced_paths.add(path[prefix_len:])
        else:
            referenced_paths.add(f"{MEDIA_PREFIX}{path}")

    # 1. Challenge files - use values_list for memory efficiency
    logger.log("\n  Collecting Challenge file paths...")
    challenge_count = Challenge.objects.count()
    logger.log(f"    Found {challenge_count} challenges")

    for field in ["image", "evaluation_script"]:
        # Exclude both NULL and empty string values
        paths = (
            Challenge.objects.exclude(**{f"{field}__isnull": True})
            .exclude(**{field: ""})
            .values_list(field, flat=True)
        )
        for path in paths.iterator(chunk_size=DB_BATCH_SIZE):
            add_path_normalized(path)

    gc.collect()
    reset_queries()

    # 2. ChallengePhase files
    logger.log("\n  Collecting ChallengePhase file paths...")
    phase_count = ChallengePhase.objects.count()
    logger.log(f"    Found {phase_count} phases")

    paths = (
        ChallengePhase.objects.exclude(test_annotation__isnull=True)
        .exclude(test_annotation="")
        .values_list("test_annotation", flat=True)
    )
    for path in paths.iterator(chunk_size=DB_BATCH_SIZE):
        add_path_normalized(path)

    gc.collect()
    reset_queries()

    # 3. Submission files - largest table, process field by field
    logger.log("\n  Collecting Submission file paths...")
    submission_count = Submission.objects.count()
    logger.log(f"    Found {submission_count} submissions")

    submission_fields = [
        "input_file",
        "submission_input_file",
        "stdout_file",
        "stderr_file",
        "environment_log_file",
        "submission_result_file",
        "submission_metadata_file",
    ]

    for field in submission_fields:
        # Exclude both NULL and empty string values
        paths = (
            Submission.objects.exclude(**{f"{field}__isnull": True})
            .exclude(**{field: ""})
            .values_list(field, flat=True)
        )
        count = 0
        for path in paths.iterator(chunk_size=DB_BATCH_SIZE):
            add_path_normalized(path)
            count += 1
            if count % 50000 == 0:
                gc.collect()
                reset_queries()
        gc.collect()
        reset_queries()

    # 4. ChallengeConfiguration files
    logger.log("\n  Collecting ChallengeConfiguration file paths...")
    config_count = ChallengeConfiguration.objects.count()
    logger.log(f"    Found {config_count} configurations")

    for field in ["zip_configuration", "stdout_file", "stderr_file"]:
        # Exclude both NULL and empty string values
        paths = (
            ChallengeConfiguration.objects.exclude(
                **{f"{field}__isnull": True}
            )
            .exclude(**{field: ""})
            .values_list(field, flat=True)
        )
        field_count = 0
        for path in paths.iterator(chunk_size=DB_BATCH_SIZE):
            add_path_normalized(path)
            field_count += 1
        logger.log(f"    {field}: {field_count} files")

    gc.collect()
    reset_queries()

    # 5. ChallengeEvaluationCluster files
    logger.log("\n  Collecting ChallengeEvaluationCluster file paths...")
    cluster_count = ChallengeEvaluationCluster.objects.count()
    logger.log(f"    Found {cluster_count} clusters")

    for field in ["cluster_yaml", "kube_config"]:
        # Exclude both NULL and empty string values
        paths = (
            ChallengeEvaluationCluster.objects.exclude(
                **{f"{field}__isnull": True}
            )
            .exclude(**{field: ""})
            .values_list(field, flat=True)
        )
        for path in paths.iterator(chunk_size=DB_BATCH_SIZE):
            add_path_normalized(path)

    gc.collect()
    reset_queries()
    connection.close()

    logger.log(
        f"\n  Total normalized reference paths: {len(referenced_paths)}"
    )
    return referenced_paths


def get_s3_client_and_bucket():
    """Get boto3 S3 client and bucket name from django-storages settings."""
    bucket_name = getattr(default_storage, "bucket_name", None)
    if not bucket_name:
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)

    s3_client = boto3.client("s3")
    return s3_client, bucket_name


def stream_s3_and_find_orphans(referenced_paths, orphan_file, logger):
    """
    Stream S3 files and write orphan keys to temp file.

    Memory optimized: Never holds full S3 file list in memory.
    Checks each file immediately and writes orphans to disk.

    Returns: (total_s3_count, orphan_count, total_orphan_size, kept_count)
    """
    s3_client, bucket_name = get_s3_client_and_bucket()
    if not bucket_name:
        logger.log(
            "  [ERROR] Could not determine S3 bucket name from settings"
        )
        return 0, 0, 0, 0

    logger.log(f"  Using bucket: {bucket_name}")

    total_s3_count = 0
    orphan_count = 0
    total_orphan_size = 0
    kept_count = 0
    prefix_len = len(MEDIA_PREFIX)

    folder_iter = S3_FOLDERS
    if TQDM_AVAILABLE:
        folder_iter = tqdm(S3_FOLDERS, desc="    S3 folders", unit="folder")

    for folder in folder_iter:
        folder_count = 0
        folder_orphans = 0

        try:
            paginator = s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(
                Bucket=bucket_name, Prefix=folder
            )

            for page in page_iterator:
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    # Skip "folder" entries
                    if key.endswith("/"):
                        continue

                    total_s3_count += 1
                    folder_count += 1

                    # Check if referenced (check both with and without prefix)
                    key_without_prefix = (
                        key[prefix_len:]
                        if key.startswith(MEDIA_PREFIX)
                        else key
                    )

                    if (
                        key in referenced_paths
                        or key_without_prefix in referenced_paths
                    ):
                        kept_count += 1
                    else:
                        # Write orphan to temp file: key\tsize\n
                        orphan_file.write(f"{key}\t{obj['Size']}\n")
                        orphan_count += 1
                        folder_orphans += 1
                        total_orphan_size += obj["Size"]

                # Periodic cleanup within large folders
                if folder_count % 100000 == 0:
                    gc.collect()

        except Exception as e:
            logger.log(f"  [ERROR] Failed to list {folder}: {e}")

        logger.log(
            f"    {folder}: {folder_count} files ({folder_orphans} orphans)"
        )

    logger.log(f"\n  Total files in S3: {total_s3_count}")
    logger.log(
        f"  Orphaned files found: {orphan_count} ({format_size(total_orphan_size)})"
    )
    logger.log(f"  Referenced files (kept): {kept_count}")

    return total_s3_count, orphan_count, total_orphan_size, kept_count


def verify_no_overlap_streaming(
    referenced_paths, orphan_file_path, logger, sample_limit=10
):
    """
    Verify no overlap between orphans and referenced paths by streaming orphan file.

    Memory optimized: Reads orphan file line by line.
    """
    logger.log(
        "\n  Verifying no overlap between orphaned and referenced files..."
    )

    overlap_count = 0
    prefix_len = len(MEDIA_PREFIX)

    with open(orphan_file_path, "r") as f:
        for line in f:
            key = line.split("\t")[0]
            key_without_prefix = (
                key[prefix_len:] if key.startswith(MEDIA_PREFIX) else key
            )

            if (
                key in referenced_paths
                or key_without_prefix in referenced_paths
            ):
                overlap_count += 1
                if overlap_count <= sample_limit:
                    logger.log(f"    [WARNING] Overlap found: {key}")

    if overlap_count > 0:
        logger.log(f"\n  [ERROR] Found {overlap_count} overlapping files!")
        return False

    logger.log(
        "  [OK] No overlap detected - all orphaned files are safe to delete"
    )
    return True


def bulk_delete_from_file(orphan_file_path, logger, dry_run=True):
    """
    Delete orphaned files by streaming from temp file.

    Memory optimized: Reads orphan file in batches, never loads all into memory.
    """
    # Count total for progress
    total_orphans = sum(1 for _ in open(orphan_file_path, "r"))

    if total_orphans == 0:
        return 0, 0

    if dry_run:
        logger.log(
            f"\n  [DRY RUN] Would delete {total_orphans} orphaned files in bulk"
        )
        return total_orphans, 0

    s3_client, bucket_name = get_s3_client_and_bucket()
    if not bucket_name:
        logger.log("  [ERROR] Could not determine S3 bucket name")
        return 0, total_orphans

    deleted = 0
    failed = 0
    batch = []
    batch_num = 0
    total_batches = (
        total_orphans + S3_DELETE_BATCH_SIZE - 1
    ) // S3_DELETE_BATCH_SIZE

    with open(orphan_file_path, "r") as f:
        if TQDM_AVAILABLE:
            f_iter = tqdm(
                f, desc="Deleting S3 files", unit="file", total=total_orphans
            )
        else:
            f_iter = f

        for line in f_iter:
            key = line.split("\t")[0]
            batch.append({"Key": key})

            if len(batch) >= S3_DELETE_BATCH_SIZE:
                batch_num += 1
                try:
                    response = s3_client.delete_objects(
                        Bucket=bucket_name, Delete={"Objects": batch}
                    )
                    deleted_count = len(response.get("Deleted", []))
                    error_count = len(response.get("Errors", []))
                    deleted += deleted_count
                    failed += error_count

                    if error_count > 0:
                        for error in response.get("Errors", [])[
                            :3
                        ]:  # Log first 3 errors
                            logger.log(
                                f"  [ERROR] Failed to delete {error['Key']}: {error['Message']}"
                            )

                    logger.log(
                        f"  [BULK DELETE] Batch {batch_num}/{total_batches}: {deleted_count} deleted, {error_count} failed"
                    )
                except Exception as e:
                    logger.log(f"  [ERROR] Bulk delete failed: {e}")
                    failed += len(batch)

                batch = []
                gc.collect()

        # Process remaining batch
        if batch:
            batch_num += 1
            try:
                response = s3_client.delete_objects(
                    Bucket=bucket_name, Delete={"Objects": batch}
                )
                deleted_count = len(response.get("Deleted", []))
                error_count = len(response.get("Errors", []))
                deleted += deleted_count
                failed += error_count
                logger.log(
                    f"  [BULK DELETE] Batch {batch_num}/{total_batches}: {deleted_count} deleted, {error_count} failed"
                )
            except Exception as e:
                logger.log(f"  [ERROR] Bulk delete failed: {e}")
                failed += len(batch)

    return deleted, failed


def main():
    start_time = time.time()

    parser = argparse.ArgumentParser(
        description="Cleanup orphaned S3 files not referenced in database"
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
    log_file_path = os.path.join(
        SCRIPT_DIR, f"orphans_cleanup_{timestamp}.log"
    )
    logger = Logger(log_file_path)

    logger.log("=" * 60)
    logger.log(f"S3 Orphan Cleanup - {'DRY RUN' if dry_run else 'EXECUTE'}")
    logger.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.log(f"Log file: {log_file_path}")
    logger.log("=" * 60)
    logger.log("\n[Memory Optimized for 1GB RAM]")

    if dry_run:
        logger.log("\n*** DRY RUN - No files will be deleted ***")
        logger.log("*** Use --execute to actually delete files ***")

    # Phase 1: Collect all file paths from database (memory: ~200-300MB for refs)
    logger.log(f"\n{'='*60}")
    logger.log("PHASE 1: Collecting database references")
    logger.log("=" * 60)
    referenced_paths = collect_db_file_paths_optimized(logger)
    gc.collect()

    # Phase 2 & 3: Stream S3 files and identify orphans (write to temp file)
    logger.log(f"\n{'='*60}")
    logger.log("PHASE 2: Streaming S3 files and identifying orphans")
    logger.log("=" * 60)

    # Create temp file for orphan keys (stored on disk, not memory)
    orphan_temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        prefix="orphans_",
        dir=SCRIPT_DIR,
        delete=False,
    )
    orphan_file_path = orphan_temp_file.name

    try:
        total_s3_files, orphan_count, orphan_size, kept_count = (
            stream_s3_and_find_orphans(
                referenced_paths, orphan_temp_file, logger
            )
        )
        orphan_temp_file.close()

        if total_s3_files == 0:
            logger.log(
                "\n[WARNING] No S3 files found. Check S3 bucket access."
            )
            logger.close()
            os.unlink(orphan_file_path)
            print(f"\nLog saved to: {log_file_path}")
            return

        if orphan_count == 0:
            logger.log(
                "\n[INFO] No orphaned files found. All S3 files are referenced in database."
            )
            logger.close()
            os.unlink(orphan_file_path)
            print(f"\nLog saved to: {log_file_path}")
            return

        # Phase 3: Verify no overlap (streaming verification)
        logger.log(f"\n{'='*60}")
        logger.log("PHASE 3: Verifying no overlap")
        logger.log("=" * 60)

        if not verify_no_overlap_streaming(
            referenced_paths, orphan_file_path, logger
        ):
            logger.log(
                "  [ERROR] Aborting to prevent data loss. Please investigate."
            )
            logger.close()
            os.unlink(orphan_file_path)
            print(f"\nLog saved to: {log_file_path}")
            return

        # Free referenced_paths - no longer needed
        del referenced_paths
        gc.collect()

        # Phase 4: Delete orphaned files (streaming from temp file)
        logger.log(f"\n{'='*60}")
        logger.log("PHASE 4: Deleting orphaned files")
        logger.log("=" * 60)
        logger.log(f"Files to delete: {orphan_count}")
        logger.log(f"Space to free: {format_size(orphan_size)}")

        deleted, failed = bulk_delete_from_file(
            orphan_file_path, logger, dry_run
        )

        # Summary
        logger.log("\n" + "=" * 60)
        logger.log("FINAL SUMMARY")
        logger.log("=" * 60)
        logger.log(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
        logger.log(f"Total S3 files scanned: {total_s3_files}")
        logger.log(f"Files referenced in database (kept): {kept_count}")
        logger.log(
            f"Orphaned files {'to delete' if dry_run else 'deleted'}: {deleted}"
        )
        if not dry_run:
            logger.log(f"Files failed to delete: {failed}")
        logger.log(
            f"Space {'to free' if dry_run else 'freed'}: {format_size(orphan_size)}"
        )
        elapsed_time = time.time() - start_time
        logger.log(f"Execution time: {format_duration(elapsed_time)}")
        logger.log(f"Log file: {log_file_path}")
        logger.log("=" * 60)

    finally:
        # Cleanup temp file
        if os.path.exists(orphan_file_path):
            os.unlink(orphan_file_path)

    logger.close()
    print(f"\nLog saved to: {log_file_path}")


if __name__ == "__main__":
    main()
