#!/usr/bin/env python
"""
Cleanup expired submission S3 artifacts for internal challenges.

Deletes S3 files for submissions older than a configurable age threshold on
challenges with challenge_usage_type=internal. DB Submission rows and FileField
paths are left unchanged.

Skips challenges that use host credentials (host-owned S3 buckets).

Usage:
    # Dry run (default) - show what would be deleted
    python scripts/tools/cleanup_data/cleanup_expired_internal_submissions.py

    # Dry run for specific internal challenges
    python scripts/tools/cleanup_data/cleanup_expired_internal_submissions.py --challenge-ids 42 99

    # Custom age threshold (default 14 days)
    python scripts/tools/cleanup_data/cleanup_expired_internal_submissions.py --days 30

    # Execute - actually delete S3 files
    python scripts/tools/cleanup_data/cleanup_expired_internal_submissions.py --execute

Output:
    Creates a log file: scripts/tools/cleanup_data/cleanup_internal_submissions_YYYYMMDD_HHMMSS.log

Run from project root in an environment with database and AWS access.
"""

import argparse
import gc
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timedelta

# Setup paths (for running outside container)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(SCRIPT_DIR)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import django  # noqa: E402
from django.conf import settings  # noqa: E402

if not settings.configured:
    django.setup()

settings.DEBUG = False
from django.db import connection, reset_queries  # noqa: E402
from django.utils import timezone  # noqa: E402

if hasattr(connection, "queries_log"):
    connection.queries_log.clear()

from challenges.models import Challenge  # noqa: E402
from jobs.models import Submission  # noqa: E402
from jobs.s3_retention import get_submission_artifact_paths  # noqa: E402
from s3 import (  # noqa: E402
    Logger,
    bulk_delete_s3_files,
    format_duration,
    format_size,
    get_file_sizes_from_s3,
)


def build_expired_submissions_queryset(challenge_ids=None, days=14):
    cutoff = timezone.now() - timedelta(days=days)
    queryset = (
        Submission.objects.filter(
            challenge_phase__challenge__challenge_usage_type=Challenge.INTERNAL,
            challenge_phase__challenge__use_host_credentials=False,
            submitted_at__lt=cutoff,
        )
        .select_related("challenge_phase", "challenge_phase__challenge")
        .order_by("pk")
    )
    if challenge_ids:
        queryset = queryset.filter(
            challenge_phase__challenge_id__in=challenge_ids
        )
    return queryset, cutoff


def collect_expired_submission_artifact_paths(
    queryset, logger, batch_size=5000
):
    """
    Stream expired submissions and collect S3 artifact paths.

    Returns:
        tuple: (list of file paths, stats dict)
    """
    stats = {
        "submissions_seen": 0,
        "submissions_with_files": 0,
        "files_found": 0,
        "challenges_seen": 0,
    }
    per_challenge = defaultdict(lambda: {"submissions": 0, "files": 0})
    all_paths = []
    seen_paths = set()
    challenges_seen = set()

    logger.log("\nDISCOVERY PHASE")
    logger.log("=" * 60)

    for submission in queryset.iterator(chunk_size=batch_size):
        stats["submissions_seen"] += 1
        challenge = submission.challenge_phase.challenge
        challenges_seen.add(challenge.pk)

        paths = get_submission_artifact_paths(submission)
        if not paths:
            continue

        stats["submissions_with_files"] += 1
        per_challenge[challenge.pk]["submissions"] += 1

        for path in paths:
            if path in seen_paths:
                continue
            seen_paths.add(path)
            all_paths.append(path)
            stats["files_found"] += 1
            per_challenge[challenge.pk]["files"] += 1

        if stats["submissions_seen"] % batch_size == 0:
            gc.collect()
            reset_queries()

    stats["challenges_seen"] = len(challenges_seen)

    if per_challenge:
        challenge_titles = dict(
            Challenge.objects.filter(pk__in=per_challenge.keys()).values_list(
                "pk", "title"
            )
        )
        logger.log("\nPer-challenge summary:")
        for challenge_id in sorted(per_challenge.keys()):
            counts = per_challenge[challenge_id]
            title = challenge_titles.get(challenge_id, "(unknown)")
            logger.log(
                f"  Challenge {challenge_id} ({title}): "
                f"{counts['submissions']} submission(s), "
                f"{counts['files']} file(s)"
            )

    return all_paths, stats


def main():
    start_time = time.time()

    parser = argparse.ArgumentParser(
        description=(
            "Delete S3 submission artifacts for internal challenges older "
            "than N days (DB rows are preserved)"
        )
    )
    parser.add_argument(
        "--days",
        type=int,
        default=14,
        help=(
            "Delete artifacts for submissions older than this many days "
            "(default: 14)"
        ),
    )
    parser.add_argument(
        "--challenge-ids",
        type=int,
        nargs="+",
        default=None,
        help="Limit cleanup to these internal challenge IDs",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=5000,
        help="Submission iterator chunk size (default: 5000)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Actually delete S3 files (default is dry run)",
    )
    args = parser.parse_args()

    if args.days < 1:
        parser.error("--days must be at least 1")

    dry_run = not args.execute
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file_path = os.path.join(
        SCRIPT_DIR, f"cleanup_internal_submissions_{timestamp}.log"
    )
    logger = Logger(log_file_path)

    queryset, cutoff = build_expired_submissions_queryset(
        challenge_ids=args.challenge_ids,
        days=args.days,
    )

    logger.log("=" * 60)
    logger.log(
        "Internal Submission S3 Cleanup - "
        f"{'DRY RUN' if dry_run else 'EXECUTE'}"
    )
    logger.log(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.log(f"Age threshold: {args.days} day(s)")
    logger.log(f"Cutoff (UTC): {cutoff.strftime('%Y-%m-%d %H:%M:%S')}")
    if args.challenge_ids:
        logger.log(f"Challenge IDs filter: {args.challenge_ids}")
    else:
        logger.log("Challenge IDs filter: all internal (non-host-credential)")
    logger.log(f"Log file: {log_file_path}")
    logger.log("=" * 60)
    logger.log("\nDB Submission rows will NOT be deleted or modified.")

    if dry_run:
        logger.log("\n*** DRY RUN - No files will be deleted ***")
        logger.log("*** Use --execute to actually delete files ***")

    all_paths, stats = collect_expired_submission_artifact_paths(
        queryset, logger, batch_size=args.batch_size
    )

    section_rule = "=" * 60
    logger.log(f"\n{section_rule}")
    logger.log("SIZE CALCULATION PHASE")
    logger.log(section_rule)
    logger.log(f"Total files to delete: {len(all_paths)}")

    file_sizes = get_file_sizes_from_s3(all_paths, logger, dry_run=dry_run)
    total_size = sum(size for _, size in file_sizes if size is not None)
    files_without_size = sum(1 for _, size in file_sizes if size is None)

    logger.log(
        f"Total size {'to free' if dry_run else 'freed'}: "
        f"{format_size(total_size)}"
    )
    if files_without_size > 0:
        logger.log(
            f"  Note: {files_without_size} files could not be sized "
            "(may not exist in S3)"
        )

    logger.log(f"\n{section_rule}")
    logger.log("BULK DELETE PHASE")
    logger.log(section_rule)

    deleted, failed = bulk_delete_s3_files(all_paths, logger, dry_run)

    logger.log("\n" + "=" * 60)
    logger.log("FINAL SUMMARY")
    logger.log("=" * 60)
    logger.log(f"Mode: {'DRY RUN' if dry_run else 'EXECUTE'}")
    logger.log(
        f"Challenges with expired submissions: {stats['challenges_seen']}"
    )
    logger.log(f"Expired submissions matched: {stats['submissions_seen']}")
    logger.log(
        "Expired submissions with artifact files: "
        f"{stats['submissions_with_files']}"
    )
    logger.log(f"Files found: {stats['files_found']}")
    logger.log(f"Files {'to delete' if dry_run else 'deleted'}: {deleted}")
    if not dry_run:
        logger.log(f"Files failed to delete: {failed}")
    if total_size > 0:
        logger.log(
            f"Space {'to free' if dry_run else 'freed'}: "
            f"{format_size(total_size)}"
        )
    logger.log(f"Execution time: {format_duration(time.time() - start_time)}")
    logger.log(f"Log file: {log_file_path}")
    logger.log("=" * 60)

    logger.close()
    print(f"\nLog saved to: {log_file_path}")


if __name__ == "__main__":
    main()
