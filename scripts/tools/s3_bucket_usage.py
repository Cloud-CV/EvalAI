#!/usr/bin/env python
"""
Audit S3 storage usage across buckets with a per-folder breakdown.

No Django dependency -- requires only boto3. Can run from any machine
with valid AWS credentials (environment variables, ~/.aws/credentials,
or an IAM role).

Memory strategy:
  - Streams list_objects_v2 pages; never holds full object lists.
  - Aggregates sizes into a dict of folder prefixes (bounded by the
    number of unique prefixes at the configured depth).

Usage:
  # Audit all known EvalAI buckets (default depth=2)
  python scripts/tools/s3_bucket_usage.py

  # Audit specific buckets
  python scripts/tools/s3_bucket_usage.py --buckets evalai staging-evalai

  # Deeper breakdown (3 folder levels)
  python scripts/tools/s3_bucket_usage.py --depth 3

  # CSV output
  python scripts/tools/s3_bucket_usage.py --csv

  # Verbose logging
  python scripts/tools/s3_bucket_usage.py -v
"""

import argparse
import gc
import logging
import sys
from collections import defaultdict

log = logging.getLogger(__name__)

DEFAULT_BUCKETS = [
    "cid-937891341272-data-local",
    "cloudcv-secrets",
    "cvmlp",
    "elasticbeanstalk-us-east-1-937891341272",
    "elasticbeanstalk-us-west-2-937891341272",
    "evalai",
    "staging-evalai",
]

S3_LIST_PAGE_SIZE = 1000
S3_LOG_PAGE_INTERVAL = 100


def format_size(size_bytes):
    """Convert bytes to human-readable string."""
    if size_bytes is None or size_bytes < 0:
        return "N/A"
    size = float(size_bytes)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def prefix_at_depth(key, depth):
    """
    Return the *directory* prefix of *key* truncated to *depth* levels.

    Always returns a folder path (ending with "/") -- never an individual
    filename.  Files whose directory depth is shallower than the requested
    depth are grouped under their parent directory.

    Examples (depth=2):
      "media/submission_files/abc.zip"  -> "media/submission_files/"
      "media/logos/img.png"             -> "media/logos/"
      "media/test_annotations/x.json"  -> "media/test_annotations/"
      "top_level_file.txt"              -> "(root)"

    Examples (depth=3):
      "media/submission_files/sub_1/f.txt"  -> "media/submission_files/sub_1/"
      "media/test_annotations/x.json"       -> "media/test_annotations/"
    """
    # Strip the filename to get directory components only.
    if key.endswith("/"):
        dir_parts = key.rstrip("/").split("/")
    else:
        dir_parts = key.rsplit("/", 1)[0].split("/") if "/" in key else []

    if not dir_parts:
        return "(root)"

    if len(dir_parts) <= depth:
        return "/".join(dir_parts) + "/"
    return "/".join(dir_parts[:depth]) + "/"


def audit_bucket(s3_client, bucket_name, depth):
    """
    Stream all objects in *bucket_name* and return aggregated stats.

    Returns:
      (total_size, total_count, folder_sizes, folder_counts)
      where folder_* are dicts keyed by the prefix at *depth*.
    """
    log.info("Auditing bucket '%s' (depth=%d) ...", bucket_name, depth)

    folder_sizes = defaultdict(int)
    folder_counts = defaultdict(int)
    total_size = 0
    total_count = 0

    paginator = s3_client.get_paginator("list_objects_v2")
    page_iter = paginator.paginate(
        Bucket=bucket_name,
        PaginationConfig={"PageSize": S3_LIST_PAGE_SIZE},
    )

    page_num = 0
    for page in page_iter:
        page_num += 1
        for obj in page.get("Contents", []):
            key = obj["Key"]
            size = obj.get("Size", 0)
            total_size += size
            total_count += 1

            pfx = prefix_at_depth(key, depth)
            folder_sizes[pfx] += size
            folder_counts[pfx] += 1

        if page_num % S3_LOG_PAGE_INTERVAL == 0:
            log.info(
                "  ... %s: %d pages, %d objects so far",
                bucket_name,
                page_num,
                total_count,
            )
            gc.collect()

    log.info(
        "  %s done: %d pages, %d objects, %s total",
        bucket_name,
        page_num,
        total_count,
        format_size(total_size),
    )
    return total_size, total_count, dict(folder_sizes), dict(folder_counts)


def print_tree(
    bucket_name, total_size, total_count, folder_sizes, folder_counts
):
    """Print a tree-style report for one bucket."""
    print(f"\n{'='*70}")
    print(f"  Bucket: {bucket_name}")
    print(f"  Total:  {format_size(total_size)}  ({total_count:,} objects)")
    print(f"{'='*70}")

    if not folder_sizes:
        print("  (empty)")
        return

    sorted_folders = sorted(
        folder_sizes.items(), key=lambda kv: kv[1], reverse=True
    )
    name_width = max(len(f) for f, _ in sorted_folders)
    name_width = max(name_width, 10)

    for folder, size in sorted_folders:
        count = folder_counts.get(folder, 0)
        pct = (size / total_size * 100) if total_size else 0
        print(
            f"  {folder:<{name_width}}  {format_size(size):>12}  {pct:5.1f}%  ({count:,} objects)"
        )


def print_csv(results):
    """Print all results as CSV."""
    print("bucket,folder,size_bytes,size_human,object_count,pct_of_bucket")
    for (
        bucket_name,
        total_size,
        _total_count,
        folder_sizes,
        folder_counts,
    ) in results:
        sorted_folders = sorted(
            folder_sizes.items(), key=lambda kv: kv[1], reverse=True
        )
        for folder, size in sorted_folders:
            count = folder_counts.get(folder, 0)
            pct = (size / total_size * 100) if total_size else 0
            safe_folder = '"' + folder.replace('"', '""') + '"'
            print(
                f"{bucket_name},{safe_folder},{size},{format_size(size)},{count},{pct:.1f}"
            )


def print_summary(results):
    """Print a one-line-per-bucket grand summary sorted by size."""
    print(f"\n{'='*70}")
    print("  GRAND SUMMARY (all buckets, sorted by size)")
    print(f"{'='*70}")

    sorted_results = sorted(results, key=lambda r: r[1], reverse=True)
    name_width = max(len(r[0]) for r in sorted_results)
    name_width = max(name_width, 10)
    grand_total = sum(r[1] for r in sorted_results)

    for bucket_name, total_size, total_count, _fs, _fc in sorted_results:
        pct = (total_size / grand_total * 100) if grand_total else 0
        print(
            f"  {bucket_name:<{name_width}}  {format_size(total_size):>12}  {pct:5.1f}%  ({total_count:,} objects)"
        )

    print(f"  {'TOTAL':<{name_width}}  {format_size(grand_total):>12}  100.0%")


def main():
    parser = argparse.ArgumentParser(
        description="Audit S3 storage usage per bucket and per folder."
    )
    parser.add_argument(
        "--buckets",
        nargs="*",
        default=None,
        help="Bucket names to audit (default: all 7 known EvalAI buckets).",
    )
    parser.add_argument(
        "--depth",
        type=int,
        default=2,
        help="Folder depth for breakdown (default: 2).",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Output CSV instead of tree report.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    args = parser.parse_args()

    log.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    if not log.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s [%(levelname)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        log.addHandler(handler)
    log.propagate = False

    buckets = args.buckets if args.buckets else DEFAULT_BUCKETS
    depth = max(1, args.depth)

    try:
        import boto3
    except ImportError:
        print(
            "ERROR: boto3 is required. Install with: pip install boto3",
            file=sys.stderr,
        )
        sys.exit(1)

    s3_client = boto3.client("s3")

    log.info("Auditing %d bucket(s) at depth %d ...", len(buckets), depth)

    results = []
    for bucket_name in buckets:
        try:
            total_size, total_count, folder_sizes, folder_counts = (
                audit_bucket(s3_client, bucket_name, depth)
            )
            results.append(
                (
                    bucket_name,
                    total_size,
                    total_count,
                    folder_sizes,
                    folder_counts,
                )
            )
        except Exception as e:
            log.error("Failed to audit bucket '%s': %s", bucket_name, e)
            print(f"\n[ERROR] Bucket '{bucket_name}': {e}", file=sys.stderr)

    if not results:
        print("No buckets could be audited.", file=sys.stderr)
        sys.exit(1)

    if args.csv:
        print_csv(results)
    else:
        for (
            bucket_name,
            total_size,
            total_count,
            folder_sizes,
            folder_counts,
        ) in results:
            print_tree(
                bucket_name,
                total_size,
                total_count,
                folder_sizes,
                folder_counts,
            )
        print_summary(results)


if __name__ == "__main__":
    main()
