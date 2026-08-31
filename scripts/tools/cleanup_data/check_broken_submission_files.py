"""
Cross-reference S3 keys that have no completed object against submission
artifact fields in the database.

s3_multipart_verify.sh splits in-progress multipart upload keys into those
that also have a completed object and those that do not. The second group
represents uploads that never finished, so nothing was ever stored at that
key. This script answers the question that follows: does the database still
point participants at any of them?

A row found here is already broken -- head-object 404s today, independently
of any lifecycle rule. The value is in knowing how many submissions silently
lost their file, and which challenges they belong to.

Read-only. Nothing is modified or deleted.

Usage:
    python manage.py shell < scripts/tools/cleanup_data/check_broken_submission_files.py

Set KEYS_FILE to the keys-with-no-object.txt produced by the verify script;
it defaults to the newest one under /tmp.
"""

import glob
import os
from collections import Counter

from django.conf import settings
from jobs.models import Submission

# Mirrors SUBMISSION_ARTIFACT_FIELDS in apps/jobs/s3_retention.py.
ARTIFACT_FIELDS = (
    "input_file",
    "submission_input_file",
    "stdout_file",
    "stderr_file",
    "environment_log_file",
    "submission_result_file",
    "submission_metadata_file",
)


def resolve_keys_file():
    explicit = os.environ.get("KEYS_FILE")
    if explicit:
        return explicit
    candidates = sorted(glob.glob("/tmp/s3-verify-*/keys-with-no-object.txt"))
    return candidates[-1] if candidates else None


def strip_media_prefix(key):
    """S3 keys carry the bucket-level 'media/' prefix that MediaStorage adds;
    FileField values are stored relative to it, so compare without it."""
    prefix = "{}/".format(getattr(settings, "MEDIAFILES_LOCATION", "media"))
    return key[len(prefix) :] if key.startswith(prefix) else key


def main():
    keys_file = resolve_keys_file()
    if not keys_file or not os.path.exists(keys_file):
        print("No keys file found. Set KEYS_FILE to keys-with-no-object.txt")
        return

    with open(keys_file) as handle:
        missing_keys = {
            strip_media_prefix(line.strip()) for line in handle if line.strip()
        }

    print("keys with no object: {}".format(len(missing_keys)))
    print("scanning submission artifact fields...\n")

    hits_by_field = Counter()
    challenges = Counter()
    affected = set()

    # values_list keeps this cheap on a large submissions table.
    queryset = Submission.objects.values_list(
        "id", "challenge_phase__challenge_id", *ARTIFACT_FIELDS
    ).iterator()

    for row in queryset:
        submission_id, challenge_id = row[0], row[1]
        for field_name, value in zip(ARTIFACT_FIELDS, row[2:]):
            if value and value in missing_keys:
                hits_by_field[field_name] += 1
                challenges[challenge_id] += 1
                affected.add(submission_id)

    print(
        "submissions referencing a key with no object: {}".format(
            len(affected)
        )
    )
    if not affected:
        print("\nNothing in the database points at these keys -- the failed")
        print("uploads left no rows behind, or cleanup already removed them.")
        return

    print("\nby field:")
    for field_name, count in hits_by_field.most_common():
        print("  {:<28} {}".format(field_name, count))

    print("\ntop affected challenges:")
    for challenge_id, count in challenges.most_common(15):
        print("  challenge {:<8} {} references".format(challenge_id, count))

    print(
        "\nThese rows are already broken; the files 404 today. Deciding what"
    )
    print("to do with them -- re-request, mark failed, or leave -- is a")
    print("product call, not a storage one.")


main()
