import logging
import os
from urllib.parse import urlencode

import boto3
from botocore.config import Config
from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)

SUBMISSION_ARTIFACT_FIELDS = (
    "input_file",
    "submission_input_file",
    "stdout_file",
    "stderr_file",
    "environment_log_file",
    "submission_result_file",
    "submission_metadata_file",
)


def build_submission_artifact_s3_tags(submission):
    challenge_phase = submission.challenge_phase
    challenge = challenge_phase.challenge
    return {
        "evalai-object-type": "submission",
        "challenge-id": str(challenge.pk),
        "challenge-phase-id": str(challenge_phase.pk),
        "submission-id": str(submission.pk),
        "retention-tier": challenge_phase.submission_artifact_retention_policy,
    }


def encode_s3_tagging(tags):
    return urlencode(tags)


def get_submission_artifact_s3_key(path):
    location = getattr(settings, "MEDIAFILES_LOCATION", "media")
    location = location.strip("/")
    normalized_path = str(path).lstrip("/")

    if not location:
        return normalized_path
    if normalized_path.startswith(f"{location}/"):
        return normalized_path
    return f"{location}/{normalized_path}"


def get_s3_client_and_bucket(s3_client=None, bucket_name=None):
    if bucket_name is None:
        bucket_name = getattr(default_storage, "bucket_name", None)
    if bucket_name is None:
        bucket_name = getattr(settings, "AWS_STORAGE_BUCKET_NAME", None)
    if s3_client is None and bucket_name:
        s3_client = boto3.client(
            "s3",
            region_name=getattr(settings, "AWS_REGION", None)
            or os.environ.get("AWS_DEFAULT_REGION"),
            config=Config(retries={"mode": "adaptive"}),
        )
    return s3_client, bucket_name


def get_submission_artifact_paths(submission):
    paths = []
    for field in SUBMISSION_ARTIFACT_FIELDS:
        file_field = getattr(submission, field, None)
        if file_field and file_field.name:
            paths.append(file_field.name)
    return paths


def put_submission_artifact_tags(
    submission, path, s3_client=None, bucket_name=None
):
    s3_client, bucket_name = get_s3_client_and_bucket(
        s3_client=s3_client, bucket_name=bucket_name
    )
    if not s3_client or not bucket_name:
        return False

    tags = build_submission_artifact_s3_tags(submission)
    s3_client.put_object_tagging(
        Bucket=bucket_name,
        Key=get_submission_artifact_s3_key(path),
        Tagging={
            "TagSet": [
                {"Key": key, "Value": value} for key, value in tags.items()
            ]
        },
    )
    return True


def should_tag_submission_artifacts(submission):
    if getattr(settings, "DEBUG", False) or getattr(settings, "TEST", False):
        return False
    if submission.challenge_phase.challenge.use_host_credentials:
        return False
    if not getattr(default_storage, "bucket_name", None):
        return False
    return True


def enqueue_submission_artifact_retention_tagging(
    submission, artifact_paths=None
):
    artifact_paths = [
        path
        for path in (
            artifact_paths or get_submission_artifact_paths(submission)
        )
        if path
    ]
    if not artifact_paths or not should_tag_submission_artifacts(submission):
        return

    from jobs.tasks import tag_submission_artifact_retention_tags

    tag_submission_artifact_retention_tags.delay(
        submission.pk, list(artifact_paths)
    )


def tag_submission_artifacts_for_retention(submission, artifact_paths=None):
    if not should_tag_submission_artifacts(submission):
        return
    bucket_name = getattr(default_storage, "bucket_name", None)
    s3_client, bucket_name = get_s3_client_and_bucket(bucket_name=bucket_name)
    if not s3_client or not bucket_name:
        return

    artifact_paths = [
        path
        for path in (
            artifact_paths or get_submission_artifact_paths(submission)
        )
        if path
    ]
    if not artifact_paths:
        return
    for path in artifact_paths:
        try:
            put_submission_artifact_tags(
                submission,
                path,
                s3_client=s3_client,
                bucket_name=bucket_name,
            )
        except Exception:
            logger.exception(
                "Failed to tag submission artifact for retention: submission_id=%s path=%s",
                submission.pk,
                path,
            )


def backfill_submission_artifact_tags(
    challenge_phase_ids=None,
    dry_run=True,
    s3_client=None,
    bucket_name=None,
):
    from jobs.models import Submission

    queryset = Submission.objects.select_related(
        "challenge_phase", "challenge_phase__challenge"
    ).filter(challenge_phase__challenge__use_host_credentials=False)
    queryset = queryset.exclude(
        challenge_phase__submission_artifact_retention_policy="keep_forever"
    )
    if challenge_phase_ids:
        queryset = queryset.filter(challenge_phase_id__in=challenge_phase_ids)

    summary = {
        "submissions_seen": 0,
        "objects_seen": 0,
        "objects_to_tag": 0,
        "objects_tagged": 0,
        "objects_failed": 0,
    }

    for submission in queryset.iterator(chunk_size=1000):
        summary["submissions_seen"] += 1
        for path in get_submission_artifact_paths(submission):
            summary["objects_seen"] += 1
            summary["objects_to_tag"] += 1
            if dry_run:
                continue
            try:
                if put_submission_artifact_tags(
                    submission,
                    path,
                    s3_client=s3_client,
                    bucket_name=bucket_name,
                ):
                    summary["objects_tagged"] += 1
            except Exception:
                summary["objects_failed"] += 1
                logger.exception(
                    "Failed to backfill retention tags: submission_id=%s path=%s",
                    submission.pk,
                    path,
                )

    return summary
