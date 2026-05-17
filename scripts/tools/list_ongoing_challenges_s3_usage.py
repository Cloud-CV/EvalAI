#!/usr/bin/env python
"""
List present/ongoing challenges (approved_by_admin, started, not ended) with challenge IDs,
submission counts, and total S3 space. Sorted by S3 space (descending). Optimized for 1GB RAM and 2 CPU cores.

Memory strategy:
  - DB: Only values_list/aggregation; no full model instances.
  - Single submission_id -> challenge_id dict (only for ongoing challenges).
  - S3: list_objects_v2 pagination; parse keys and sum sizes in one pass.

Usage (from project root, inside Python Docker container with DB + AWS access):
  python scripts/tools/list_ongoing_challenges_s3_usage.py

  # Optional: limit to specific challenge IDs (still only ongoing)
  python scripts/tools/list_ongoing_challenges_s3_usage.py --challenge-ids 1 2 3

  # Optional: CSV output
  python scripts/tools/list_ongoing_challenges_s3_usage.py --csv

  # Optional: verbose (debug) logging
  python scripts/tools/list_ongoing_challenges_s3_usage.py -v

  # Example: run from host against production Django container
  # docker exec -it <django_container_name> python scripts/tools/list_ongoing_challenges_s3_usage.py
"""

import argparse
import gc
import logging
import os
import re
import sys
from collections import defaultdict
from decimal import Decimal

# Logger configured in main()
log = logging.getLogger(__name__)

# Path setup: find project root (directory containing manage.py or settings/)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = SCRIPT_DIR
for _ in range(5):
    if os.path.isfile(
        os.path.join(PROJECT_ROOT, "manage.py")
    ) or os.path.isdir(os.path.join(PROJECT_ROOT, "settings")):
        break
    parent = os.path.dirname(PROJECT_ROOT)
    if parent == PROJECT_ROOT:
        break
    PROJECT_ROOT = parent
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
    sys.path.insert(0, os.path.join(PROJECT_ROOT, "apps"))

# Django needs this when running as a standalone script (e.g. from scripts/tools/)
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.prod")

import django  # noqa: E402
from django.conf import settings  # noqa: E402
from django.db.models import Count, Q  # noqa: E402

if not settings.configured:
    django.setup()

settings.DEBUG = False

from challenges.models import Challenge  # noqa: E402
from django.core.files.storage import default_storage  # noqa: E402
from django.utils import timezone as django_tz  # noqa: E402
from jobs.models import Submission  # noqa: E402

# S3 listing batch size (list_objects_v2 MaxKeys)
S3_LIST_PAGE_SIZE = 1000
# DB iterator chunk size
DB_ITERATOR_CHUNK_SIZE = 5000

# Key pattern: legacy submission_files/submission_<id>/... or
# nested submission_files/challenge_<id>/phase_<id>/submission_<id>/...
SUBMISSION_KEY_PATTERN = re.compile(
    r"submission_files/(?:challenge_\d+/phase_\d+/)?"
    r"(?:submission_|environment_log_file_)(\d+)"
)

MEDIA_PREFIX = "media"


def get_s3_client_and_bucket():
    """Get boto3 S3 client and bucket name from django-storages/settings."""
    bucket_name = getattr(default_storage, "bucket_name", None)
    if not bucket_name:
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    try:
        import boto3

        s3_client = boto3.client("s3")
    except Exception:
        s3_client = None
    return s3_client, bucket_name


def get_media_prefix():
    """Prefix for media keys (e.g. 'media')."""
    location = getattr(default_storage, "location", "") or MEDIA_PREFIX
    return location.rstrip("/")


def format_size(size_bytes):
    """Convert bytes to human-readable string."""
    if size_bytes is None or size_bytes < 0:
        return "N/A"
    size = float(size_bytes)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


def parse_submission_id_from_s3_key(key):
    """
    Extract submission ID from S3 key.
    Key format: media/submission_files/submission_<id>/... or .../environment_log_file_<id>/...
    Returns int or None.
    """
    match = SUBMISSION_KEY_PATTERN.search(key)
    return int(match.group(1)) if match else None


def get_present_ongoing_challenge_ids():
    """
    Challenge IDs that are present/ongoing: approved_by_admin, start_date <= now,
    and (end_date >= now or end_date is null).
    """
    log.info(
        "Fetching present/ongoing challenges (approved_by_admin, start_date <= now, end_date >= now or null)..."
    )
    now = django_tz.now()
    qs = (
        Challenge.objects.filter(approved_by_admin=True)
        .filter(start_date__lte=now)
        .filter(Q(end_date__gte=now) | Q(end_date__isnull=True))
        .values_list("id", flat=True)
    )
    ids = list(qs)
    log.info(
        "Found %d present/ongoing challenge(s): %s",
        len(ids),
        ids[:20] if len(ids) > 20 else ids,
    )
    return ids


def get_submission_counts_by_challenge(challenge_ids):
    """Return dict challenge_id -> submission count (only for given challenge_ids)."""
    if not challenge_ids:
        return {}
    log.info("Computing submission counts per challenge (DB aggregation)...")
    qs = (
        Submission.objects.filter(
            challenge_phase__challenge_id__in=challenge_ids
        )
        .values("challenge_phase__challenge_id")
        .annotate(count=Count("id"))
    )
    counts = {row["challenge_phase__challenge_id"]: row["count"] for row in qs}
    total_submissions = sum(counts.values())
    log.info(
        "Total submissions across %d challenge(s): %d",
        len(counts),
        total_submissions,
    )
    return counts


def build_submission_to_challenge(challenge_ids):
    """
    Build dict submission_id -> challenge_id for submissions in given challenges.
    Uses iterator to keep memory low.
    """
    if not challenge_ids:
        return {}
    log.info(
        "Building submission_id -> challenge_id map (streaming from DB, chunk_size=%d)...",
        DB_ITERATOR_CHUNK_SIZE,
    )
    out = {}
    qs = (
        Submission.objects.filter(
            challenge_phase__challenge_id__in=challenge_ids
        )
        .values_list("id", "challenge_phase__challenge_id")
        .iterator(chunk_size=DB_ITERATOR_CHUNK_SIZE)
    )
    for sid, cid in qs:
        out[sid] = cid
        if len(out) % 50000 == 0:
            log.info("  ... %d submissions mapped so far", len(out))
            gc.collect()
    log.info(
        "Submission map complete: %d submission(s) mapped to challenges",
        len(out),
    )
    return out


def get_challenge_titles(challenge_ids):
    """Return dict challenge_id -> title."""
    if not challenge_ids:
        return {}
    log.info(
        "Fetching challenge titles for %d challenge(s)...", len(challenge_ids)
    )
    qs = Challenge.objects.filter(pk__in=challenge_ids).values_list(
        "id", "title"
    )
    return dict(qs)


# Log S3 progress every N pages
S3_LOG_PAGE_INTERVAL = 50


def sum_s3_sizes_by_challenge(
    submission_to_challenge, bucket_name, prefix, s3_client
):
    """
    List all objects under prefix, parse submission id from key, add size to challenge.
    Returns dict challenge_id -> total bytes (int).
    """
    log.info(
        "Listing S3 objects under prefix '%s' (bucket=%s, page_size=%d)...",
        prefix,
        bucket_name,
        S3_LIST_PAGE_SIZE,
    )
    total_by_challenge = defaultdict(int)
    paginator = s3_client.get_paginator("list_objects_v2")
    page_iterator = paginator.paginate(
        Bucket=bucket_name,
        Prefix=prefix,
        PaginationConfig={"PageSize": S3_LIST_PAGE_SIZE},
    )
    page_num = 0
    total_objects = 0
    total_matched = 0
    for page in page_iterator:
        page_num += 1
        contents = page.get("Contents") or []
        for obj in contents:
            key = obj.get("Key", "")
            size = obj.get("Size") or 0
            if isinstance(size, Decimal):
                size = int(size)
            total_objects += 1
            sid = parse_submission_id_from_s3_key(key)
            if sid is not None and sid in submission_to_challenge:
                cid = submission_to_challenge[sid]
                total_by_challenge[cid] += size
                total_matched += 1
        if page_num % S3_LOG_PAGE_INTERVAL == 0:
            log.info(
                "  ... S3: %d pages, %d objects listed, %d matched to ongoing challenges",
                page_num,
                total_objects,
                total_matched,
            )
        gc.collect()
    log.info(
        "S3 listing complete: %d pages, %d objects, %d matched to challenges",
        page_num,
        total_objects,
        total_matched,
    )
    return dict(total_by_challenge)


def main():
    parser = argparse.ArgumentParser(
        description="List ongoing challenges with submission counts and S3 usage (sorted by S3 space)."
    )
    parser.add_argument(
        "--challenge-ids",
        type=int,
        nargs="*",
        default=None,
        help="Optional: only these challenge IDs (still filtered to present/ongoing).",
    )
    parser.add_argument(
        "--csv",
        action="store_true",
        help="Output CSV instead of table.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable debug logging.",
    )
    args = parser.parse_args()

    # Configure our logger so messages always go to stderr (Django's console handler
    # uses require_debug_true in prod, so log.info would otherwise only go to logfile)
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
    log.propagate = (
        False  # we handle it ourselves; don't rely on Django's config
    )
    log.info("Starting list_ongoing_challenges_s3_usage")

    # 1. Ongoing challenge IDs
    ongoing_ids = get_present_ongoing_challenge_ids()
    if args.challenge_ids is not None:
        before = len(ongoing_ids)
        ongoing_ids = [c for c in ongoing_ids if c in args.challenge_ids]
        log.info(
            "Filtered to --challenge-ids: %d -> %d challenge(s)",
            before,
            len(ongoing_ids),
        )
    if not ongoing_ids:
        log.warning("No present/ongoing challenges found.")
        print("No present/ongoing challenges found.")
        return

    # 2. Submission counts per challenge (DB aggregation only)
    submission_counts = get_submission_counts_by_challenge(ongoing_ids)
    # 3. submission_id -> challenge_id for S3 key mapping
    submission_to_challenge = build_submission_to_challenge(ongoing_ids)
    # 4. Challenge titles
    titles = get_challenge_titles(ongoing_ids)

    gc.collect()

    # 5. S3 sizes: list objects under media/submission_files/
    s3_client, bucket_name = get_s3_client_and_bucket()
    if not s3_client or not bucket_name:
        log.warning(
            "S3 not configured (bucket=%s); S3 space will be 0 for all.",
            bucket_name,
        )
        print("S3 not configured; S3 space will be 0 for all.")
        s3_bytes = {cid: 0 for cid in ongoing_ids}
    else:
        prefix = get_media_prefix() + "/submission_files/"
        s3_bytes = sum_s3_sizes_by_challenge(
            submission_to_challenge, bucket_name, prefix, s3_client
        )

    # 6. Build rows: challenge_id, title, submission_count, s3_bytes
    rows = []
    for cid in ongoing_ids:
        rows.append(
            (
                cid,
                titles.get(cid, ""),
                submission_counts.get(cid, 0),
                s3_bytes.get(cid, 0),
            )
        )
    # Sort by S3 space descending
    rows.sort(key=lambda r: r[3], reverse=True)

    total_s3 = sum(r[3] for r in rows)
    log.info(
        "Done. Total S3 space across %d challenge(s): %s",
        len(rows),
        format_size(total_s3),
    )

    # 7. Output
    if args.csv:
        print("challenge_id,title,submission_count,s3_bytes,s3_human")
        for cid, title, count, b in rows:
            safe_title = '"' + (title or "").replace('"', '""') + '"'
            print(f"{cid},{safe_title},{count},{b},{format_size(b)}")
    else:
        # Table with aligned columns
        col_id = max(12, len("challenge_id"))
        col_title = 30
        col_count = max(10, len("submissions"))
        col_size = max(14, len("S3 space"))
        fmt = f"{{:>{col_id}}}  {{:<{col_title}}}  {{:>{col_count}}}  {{:>{col_size}}}"
        print(fmt.format("challenge_id", "title", "submissions", "S3 space"))
        print("-" * (col_id + 2 + col_title + 2 + col_count + 2 + col_size))
        for cid, title, count, b in rows:
            title_short = (title or "")[:col_title]
            print(fmt.format(cid, title_short, count, format_size(b)))


if __name__ == "__main__":
    main()
