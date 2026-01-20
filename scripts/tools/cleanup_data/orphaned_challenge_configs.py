#!/usr/bin/env python
"""
Cleanup orphaned ChallengeConfiguration files - Memory Optimized for 1GB RAM.

This script finds ChallengeConfiguration entries where challenge is NULL
(not mapped to any challenge) and deletes their associated S3 files.

Files cleaned up:
    - zip_configuration_files/challenge_zip/ (zip_configuration, stdout_file, stderr_file)

Memory Optimization Strategy:
    - Uses values_list() to fetch only file paths, not full objects
    - Streams configs and writes file paths to temp file (not memory)
    - Processes deletions by reading from temp file
    - Optimized queries to fetch all fields at once
    - Aggressive garbage collection
    - Option to delete DB records after file cleanup

Usage:
    # Dry run (default) - show what would be deleted
    python scripts/tools/cleanup_data/orphaned_challenge_configs.py

    # Execute - actually delete S3 files
    python scripts/tools/cleanup_data/orphaned_challenge_configs.py --execute

    # Execute - delete S3 files AND database records
    python scripts/tools/cleanup_data/orphaned_challenge_configs.py --execute --delete-db-records

Output:
    Creates a log file: scripts/tools/cleanup_data/orphaned_challenge_configs_cleanup_YYYYMMDD_HHMMSS.log

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
from challenges.models import ChallengeConfiguration  # noqa: E402
from django.core.files.storage import default_storage  # noqa: E402

# Batch sizes optimized for 1GB RAM and 1 CPU core
DB_BATCH_SIZE = 5000  # For DB queries (just path strings, low memory)
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


def get_s3_client_and_bucket():
    """Get boto3 S3 client and bucket name from django-storages settings."""
    bucket_name = getattr(default_storage, "bucket_name", None)
    if not bucket_name:
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    s3_client = boto3.client("s3")
    return s3_client, bucket_name


def get_s3_key(path):
    """Convert database path to full S3 key (add media/ prefix if needed)."""
    location = getattr(default_storage, "location", "") or "media"

    if not location:
        return path

    location_normalized = location.rstrip("/")

    if path.startswith(f"{location_normalized}/"):
        return path

    return f"{location_normalized}/{path}"


def collect_orphaned_config_files_streaming(
    logger, file_paths_file, config_ids_file
):
    """
    Stream orphaned configs and write file paths to temp file (memory optimized).

    Memory optimized: Never accumulates all paths in memory, writes directly to disk.
    Optimized query: Fetches all fields at once instead of per-config queries.

    Returns: (total_configs, total_files, files_per_config_stats)
    """
    logger.log("\n  Finding orphaned ChallengeConfiguration entries...")

    # Find all configs where challenge is NULL
    orphaned_configs = ChallengeConfiguration.objects.filter(
        challenge__isnull=True
    )
    orphaned_count = orphaned_configs.count()

    logger.log(
        f"    Found {orphaned_count} orphaned configurations (challenge is NULL)"
    )

    if orphaned_count == 0:
        return 0, 0, {}

    # Optimized: Fetch all needed fields at once instead of per-config queries
    config_fields = ["id", "zip_configuration", "stdout_file", "stderr_file"]
    config_iter = orphaned_configs.values_list(*config_fields).iterator(
        chunk_size=DB_BATCH_SIZE
    )

    if TQDM_AVAILABLE:
        config_iter = tqdm(
            config_iter,
            desc="    Collecting files",
            unit="config",
            total=orphaned_count,
        )

    total_files = 0
    total_configs_with_files = 0
    files_per_config_list = []  # Only for stats, will be cleared

    processed = 0
    for row in config_iter:
        config_id = row[0]
        files_for_this_config = []

        # Check each file field (skip id at index 0)
        for path in row[1:]:
            if path:  # path is not None and not empty string
                file_paths_file.write(f"{path}\n")
                files_for_this_config.append(path)
                total_files += 1

        if files_for_this_config:
            config_ids_file.write(f"{config_id}\n")
            total_configs_with_files += 1
            files_per_config_list.append(len(files_for_this_config))

        processed += 1
        if processed % DB_BATCH_SIZE == 0:
            gc.collect()
            reset_queries()

        # Clear stats list periodically to save memory (keep only recent for rolling stats)
        if len(files_per_config_list) > 10000:
            # Keep stats but clear old entries
            files_per_config_list = files_per_config_list[-1000:]

    # Calculate stats
    stats = {}
    if files_per_config_list:
        stats = {
            "min": min(files_per_config_list),
            "max": max(files_per_config_list),
            "avg": sum(files_per_config_list) / len(files_per_config_list),
        }

    logger.log(
        f"\n  Total configurations with files: {total_configs_with_files}"
    )
    logger.log(f"  Total files to delete: {total_files}")

    # Clear stats list
    del files_per_config_list
    gc.collect()
    reset_queries()
    connection.close()

    return total_configs_with_files, total_files, stats


def calculate_total_size_from_s3(file_paths_file_path, logger):
    """
    Calculate total size of files in S3 by querying each file.

    Memory optimized: Streams through file paths and queries S3 one by one.
    Returns total size in bytes.
    """
    s3_client, bucket_name = get_s3_client_and_bucket()
    if not bucket_name:
        logger.log("  [ERROR] Could not determine S3 bucket name")
        return 0

    total_size = 0
    file_count = 0

    # Count total files first for progress
    total_files = sum(1 for _ in open(file_paths_file_path, "r"))

    if total_files == 0:
        return 0

    logger.log(f"  Calculating total size of {total_files} files from S3...")

    with open(file_paths_file_path, "r") as f:
        if TQDM_AVAILABLE:
            f_iter = tqdm(
                f, desc="  Getting file sizes", unit="file", total=total_files
            )
        else:
            f_iter = f

        for line in f_iter:
            path = line.strip()
            if not path:
                continue

            try:
                key = get_s3_key(path)
                response = s3_client.head_object(Bucket=bucket_name, Key=key)
                size = response.get("ContentLength", 0)
                total_size += size
                file_count += 1
            except Exception as e:
                # File doesn't exist or other error, skip but log first few
                error_code = (
                    getattr(e, "response", {}).get("Error", {}).get("Code", "")
                )
                if error_code != "404" and file_count < 3:
                    logger.log(
                        f"  [WARNING] Could not get size for {path}: {e}"
                    )

    return total_size


def bulk_delete_s3_files_from_file(file_paths_file_path, logger, dry_run=True):
    """
    Delete files in bulk by streaming from temp file.

    Memory optimized: Reads file paths from temp file in batches, never loads all into memory.

    Returns: (deleted_count, failed_count, total_size_deleted)
    """
    # Count total files first
    total_files = sum(1 for _ in open(file_paths_file_path, "r"))

    if total_files == 0:
        return 0, 0, 0

    if dry_run:
        # Calculate total size for dry run
        total_size = calculate_total_size_from_s3(file_paths_file_path, logger)
        logger.log(
            f"\n  [DRY RUN] Would delete {total_files} files ({format_size(total_size)})"
        )
        return total_files, 0, total_size

    s3_client, bucket_name = get_s3_client_and_bucket()
    if not bucket_name:
        logger.log("  [ERROR] Could not determine S3 bucket name")
        return 0, total_files, 0

    location = getattr(default_storage, "location", "") or "media"
    logger.log(f"  Using bucket: {bucket_name}, prefix: '{location}'")

    # Show sample path conversion
    with open(file_paths_file_path, "r") as f:
        first_line = f.readline().strip()
        if first_line:
            sample_key = get_s3_key(first_line)
            logger.log(
                f"  Sample path conversion: '{first_line}' -> '{sample_key}'"
            )

    deleted = 0
    failed = 0
    total_size_deleted = 0
    batch = []
    batch_keys_with_sizes = []  # Store (key, size) for tracking
    batch_num = 0
    total_batches = (
        total_files + S3_DELETE_BATCH_SIZE - 1
    ) // S3_DELETE_BATCH_SIZE

    with open(file_paths_file_path, "r") as f:
        if TQDM_AVAILABLE:
            f_iter = tqdm(
                f, desc="Deleting S3 files", unit="file", total=total_files
            )
        else:
            f_iter = f

        for line in f_iter:
            path = line.strip()
            if not path:
                continue

            key = get_s3_key(path)
            batch.append({"Key": key})

            # Get file size before deletion (for tracking)
            try:
                response = s3_client.head_object(Bucket=bucket_name, Key=key)
                size = response.get("ContentLength", 0)
                batch_keys_with_sizes.append((key, size))
            except Exception:
                # If we can't get size, just track the key
                batch_keys_with_sizes.append((key, 0))

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

                    # Track size of successfully deleted files
                    deleted_keys = {
                        item.get("Key") for item in response.get("Deleted", [])
                    }
                    for key, size in batch_keys_with_sizes:
                        if key in deleted_keys:
                            total_size_deleted += size

                    if error_count > 0:
                        for error in response.get("Errors", [])[
                            :3
                        ]:  # Log first 3 errors only
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
                batch_keys_with_sizes = []
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

                # Track size of successfully deleted files
                deleted_keys = {
                    item.get("Key") for item in response.get("Deleted", [])
                }
                for key, size in batch_keys_with_sizes:
                    if key in deleted_keys:
                        total_size_deleted += size

                logger.log(
                    f"  [BULK DELETE] Batch {batch_num}/{total_batches}: {deleted_count} deleted, {error_count} failed"
                )
            except Exception as e:
                logger.log(f"  [ERROR] Bulk delete failed: {e}")
                failed += len(batch)

    return deleted, failed, total_size_deleted


def delete_db_records_from_file(config_ids_file_path, logger, dry_run=True):
    """
    Delete ChallengeConfiguration database records by streaming from temp file.

    Memory optimized: Reads config IDs from temp file in batches.

    Note: This should only be done AFTER S3 files are deleted.
    """
    # Count total configs first
    total_configs = sum(1 for _ in open(config_ids_file_path, "r"))

    if total_configs == 0:
        return 0

    if dry_run:
        logger.log(
            f"\n  [DRY RUN] Would delete {total_configs} database records"
        )
        return total_configs

    deleted_count = 0
    batch = []
    batch_num = 0
    total_batches = (total_configs + DB_BATCH_SIZE - 1) // DB_BATCH_SIZE

    logger.log(f"\n  Deleting {total_configs} database records...")

    with open(config_ids_file_path, "r") as f:
        if TQDM_AVAILABLE:
            f_iter = tqdm(
                f,
                desc="  Deleting DB records",
                unit="record",
                total=total_configs,
            )
        else:
            f_iter = f

        for line in f_iter:
            config_id = line.strip()
            if not config_id:
                continue

            try:
                batch.append(int(config_id))
            except ValueError:
                continue

            if len(batch) >= DB_BATCH_SIZE:
                batch_num += 1
                count = ChallengeConfiguration.objects.filter(
                    id__in=batch
                ).delete()[0]
                deleted_count += count
                logger.log(
                    f"    Deleted {count} records (batch {batch_num}/{total_batches})"
                )
                batch = []
                gc.collect()
                reset_queries()

        # Process remaining batch
        if batch:
            batch_num += 1
            count = ChallengeConfiguration.objects.filter(
                id__in=batch
            ).delete()[0]
            deleted_count += count
            logger.log(
                f"    Deleted {count} records (batch {batch_num}/{total_batches})"
            )
            gc.collect()
            reset_queries()

    return deleted_count


def main():
    start_time = time.time()

    parser = argparse.ArgumentParser(
        description="Cleanup orphaned ChallengeConfiguration files (where challenge is NULL)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete files (default is dry run)",
    )
    parser.add_argument(
        "--delete-db-records",
        action="store_true",
        help="Also delete database records after deleting S3 files (use with --execute)",
    )
    args = parser.parse_args()

    dry_run = not args.execute

    # Create log file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(
        SCRIPT_DIR, f"orphaned_challenge_configs_cleanup_{timestamp}.log"
    )
    logger = Logger(log_file_path)

    logger.log("=" * 60)
    logger.log(
        f"Orphaned ChallengeConfiguration Cleanup - {'DRY RUN' if dry_run else 'EXECUTE'}"
    )
    logger.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.log(f"Log file: {log_file_path}")
    logger.log("=" * 60)
    logger.log("\n[Memory Optimized for 1GB RAM]")

    if args.delete_db_records and not args.execute:
        logger.log(
            "\n[WARNING] --delete-db-records requires --execute. Ignoring --delete-db-records."
        )

    if dry_run:
        logger.log("\n*** DRY RUN - No files will be deleted ***")
        logger.log("*** Use --execute to actually delete files ***")
        if args.delete_db_records:
            logger.log(
                "*** Use --delete-db-records with --execute to also delete DB records ***"
            )

    # Create temp files for streaming (stored on disk, not memory)
    file_paths_temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        prefix="orphaned_files_",
        dir=SCRIPT_DIR,
        delete=False,
    )
    file_paths_file_path = file_paths_temp_file.name

    config_ids_temp_file = tempfile.NamedTemporaryFile(
        mode="w",
        suffix=".txt",
        prefix="orphaned_config_ids_",
        dir=SCRIPT_DIR,
        delete=False,
    )
    config_ids_file_path = config_ids_temp_file.name

    # Initialize variables for summary (in case of early exit)
    total_configs = 0
    total_files = 0
    stats = {}
    deleted = 0
    failed = 0
    total_size = 0
    db_deleted = 0

    try:
        # Phase 1: Stream orphaned configs and write to temp files
        logger.log(f"\n{'='*60}")
        logger.log("PHASE 1: Collecting orphaned configuration files")
        logger.log("=" * 60)
        total_configs, total_files, stats = (
            collect_orphaned_config_files_streaming(
                logger, file_paths_temp_file, config_ids_temp_file
            )
        )
        file_paths_temp_file.close()
        config_ids_temp_file.close()

        if total_files == 0:
            logger.log("\n[INFO] No orphaned configuration files found.")
            logger.close()
            os.unlink(file_paths_file_path)
            os.unlink(config_ids_file_path)
            print(f"\nLog saved to: {log_file_path}")
            return

        logger.log("\n  Summary:")
        logger.log(f"    Configurations: {total_configs}")
        logger.log(f"    Total files: {total_files}")
        if stats:
            logger.log(
                f"    Files per config: min={stats['min']}, max={stats['max']}, avg={stats['avg']:.1f}"
            )

        # Phase 2: Delete S3 files (streaming from temp file)
        logger.log(f"\n{'='*60}")
        logger.log("PHASE 2: Deleting S3 files")
        logger.log("=" * 60)
        deleted, failed, total_size = bulk_delete_s3_files_from_file(
            file_paths_file_path, logger, dry_run
        )

        # Phase 3: Delete DB records (if requested, streaming from temp file)
        if args.delete_db_records and args.execute and total_configs > 0:
            logger.log(f"\n{'='*60}")
            logger.log("PHASE 3: Deleting database records")
            logger.log("=" * 60)
            db_deleted = delete_db_records_from_file(
                config_ids_file_path, logger, dry_run=False
            )
    finally:
        # Cleanup temp files
        if os.path.exists(file_paths_file_path):
            os.unlink(file_paths_file_path)
        if os.path.exists(config_ids_file_path):
            os.unlink(config_ids_file_path)

    # Summary
    logger.log("\n" + "=" * 60)
    logger.log("FINAL SUMMARY")
    logger.log("=" * 60)
    logger.log(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    logger.log(f"Orphaned configurations found: {total_configs}")
    logger.log(f"Files {'to delete' if dry_run else 'deleted'}: {deleted}")
    if total_size > 0:
        logger.log(
            f"Space {'to free' if dry_run else 'freed'}: {format_size(total_size)}"
        )
    if not dry_run:
        logger.log(f"Files failed to delete: {failed}")
    if args.delete_db_records and args.execute:
        logger.log(f"Database records deleted: {db_deleted}")
    elapsed_time = time.time() - start_time
    logger.log(f"Execution time: {format_duration(elapsed_time)}")
    logger.log(f"Log file: {log_file_path}")
    logger.log("=" * 60)

    logger.close()
    print(f"\nLog saved to: {log_file_path}")


if __name__ == "__main__":
    main()
