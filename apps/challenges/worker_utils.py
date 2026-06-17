from .constants import (
    DEFAULT_WORKER_PYTHON_VERSION,
    SUPPORTED_WORKER_PYTHON_VERSIONS,
)


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
