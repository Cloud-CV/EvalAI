import os
import re

from .constants import (
    DEFAULT_WORKER_PYTHON_VERSION,
    SUPPORTED_WORKER_PYTHON_VERSIONS,
)

EC2_AMI_PATTERN = re.compile(r"^ami-[0-9a-f]+$", re.IGNORECASE)


def normalize_worker_python_version(python_version):
    """
    Return a supported worker Python version, defaulting to 3.9.
    """
    if python_version in SUPPORTED_WORKER_PYTHON_VERSIONS:
        return python_version
    return DEFAULT_WORKER_PYTHON_VERSION


def ensure_challenge_worker_python_version(challenge):
    """
    Persist the default worker Python version for challenges that omit it.
    """
    normalized_version = normalize_worker_python_version(
        getattr(challenge, "worker_python_version", None)
    )
    if challenge.worker_python_version != normalized_version:
        challenge.worker_python_version = normalized_version
        challenge.save(update_fields=["worker_python_version"])
    return normalized_version


def is_allowed_worker_image_url(
    image_url, aws_account_id=None, aws_region=None
):
    """
    Restrict worker_image_url to EC2 AMIs or EvalAI ECR repositories in this account.
    """
    if not image_url:
        return True
    if EC2_AMI_PATTERN.match(image_url):
        return True

    account_id = aws_account_id or os.environ.get("AWS_ACCOUNT_ID")
    region = aws_region or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
    if not account_id:
        return False

    ecr_prefix = f"{account_id}.dkr.ecr.{region}.amazonaws.com/"
    if not image_url.startswith(ecr_prefix):
        return False

    repository = image_url[len(ecr_prefix) :].split(":", 1)[0]
    return repository.startswith("evalai-")
