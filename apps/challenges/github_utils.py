"""
Celery tasks and utilities for bi-directional GitHub sync.
Syncs Challenge and ChallengePhase changes from EvalAI UI to GitHub repositories.
"""

import logging
import threading

from celery import shared_task
from django.core import serializers

from .github_interface import GithubInterface
from .github_sync_config import (
    CHALLENGE_PHASE_SYNC_FIELDS,
    CHALLENGE_SYNC_FIELDS,
)

logger = logging.getLogger(__name__)

# Thread-local storage for per-request sync context
_sync_context = threading.local()


def get_sync_context():
    """Get the current request's sync context."""
    if not hasattr(_sync_context, "synced_models"):
        _sync_context.synced_models = set()
    if not hasattr(_sync_context, "payload_keys"):
        _sync_context.payload_keys = set()
    if not hasattr(_sync_context, "is_github_source"):
        _sync_context.is_github_source = False
    return _sync_context


def reset_sync_context():
    """Reset sync context for a new request."""
    _sync_context.synced_models = set()
    _sync_context.payload_keys = set()
    _sync_context.is_github_source = False


def mark_synced(model_name, pk):
    """Mark a model instance as synced in this request."""
    ctx = get_sync_context()
    ctx.synced_models.add((model_name, pk))


def is_synced(model_name, pk):
    """Check if a model instance was already synced in this request."""
    ctx = get_sync_context()
    return (model_name, pk) in ctx.synced_models


def set_payload_keys(keys):
    """Set the request payload keys for field inference."""
    ctx = get_sync_context()
    ctx.payload_keys = set(keys) if keys else set()


def get_payload_keys():
    """Get the request payload keys."""
    ctx = get_sync_context()
    return ctx.payload_keys


def set_github_source(is_github):
    """Mark request as originating from GitHub."""
    ctx = get_sync_context()
    ctx.is_github_source = is_github


def is_github_source():
    """Check if request originated from GitHub."""
    ctx = get_sync_context()
    return ctx.is_github_source


def deserialize_object(serialized_object):
    """Deserialize a Django object from JSON."""
    deserialized_object = None
    for obj in serializers.deserialize("json", serialized_object):
        deserialized_object = obj.object
    return deserialized_object


def get_changed_field_from_update_fields(update_fields, sync_fields):
    """
    Determine which syncable field was changed based on update_fields.
    Returns the field name if exactly one syncable field was updated.
    """
    if not update_fields:
        return None

    changed_sync_fields = set(update_fields) & sync_fields
    if len(changed_sync_fields) == 1:
        return changed_sync_fields.pop()
    return None


def get_changed_field_from_payload(payload_keys, sync_fields):
    """
    Determine which syncable field was changed based on request payload.
    Returns the field name if exactly one syncable field was in the payload.
    """
    if not payload_keys:
        return None

    changed_sync_fields = set(payload_keys) & sync_fields
    if len(changed_sync_fields) == 1:
        return changed_sync_fields.pop()
    return None


@shared_task
def github_challenge_sync(serialized_challenge, changed_field):
    """
    Celery task to sync a Challenge change to GitHub.

    Args:
        serialized_challenge: JSON serialized Challenge object
        changed_field: The field that was changed
    """
    try:
        challenge = deserialize_object(serialized_challenge)
        if not challenge:
            logger.error("Failed to deserialize challenge for GitHub sync")
            return False

        # Verify GitHub config is present
        if not challenge.github_repository or not challenge.github_token:
            logger.debug(
                f"Challenge {challenge.pk} missing github_repository or github_token, "
                "skipping sync"
            )
            return False

        # Create GitHub interface
        github = GithubInterface(
            challenge.github_repository,
            challenge.github_branch,
            challenge.github_token,
        )

        # Verify repository access
        if not github.is_repository():
            logger.error(
                f"Cannot access GitHub repository: {challenge.github_repository}"
            )
            return False

        # Sync the changed field
        success = github.update_challenge_config(challenge, changed_field)
        if success:
            logger.info(
                f"Successfully synced {changed_field} for challenge {challenge.pk}"
            )
        else:
            logger.error(
                f"Failed to sync {changed_field} for challenge {challenge.pk}"
            )
        return success

    except Exception as e:
        logger.error(f"Error in github_challenge_sync: {str(e)}")
        return False


@shared_task
def github_challenge_phase_sync(
    serialized_challenge_phase, serialized_challenge, changed_field
):
    """
    Celery task to sync a ChallengePhase change to GitHub.

    Args:
        serialized_challenge_phase: JSON serialized ChallengePhase object
        serialized_challenge: JSON serialized Challenge object (parent)
        changed_field: The field that was changed
    """
    try:
        challenge_phase = deserialize_object(serialized_challenge_phase)
        challenge = deserialize_object(serialized_challenge)

        if not challenge_phase or not challenge:
            logger.error(
                "Failed to deserialize challenge_phase or challenge for GitHub sync"
            )
            return False

        # Verify GitHub config is present on parent challenge
        if not challenge.github_repository or not challenge.github_token:
            logger.debug(
                f"Challenge {challenge.pk} missing github_repository or github_token, "
                "skipping phase sync"
            )
            return False

        # Create GitHub interface
        github = GithubInterface(
            challenge.github_repository,
            challenge.github_branch,
            challenge.github_token,
        )

        # Verify repository access
        if not github.is_repository():
            logger.error(
                f"Cannot access GitHub repository: {challenge.github_repository}"
            )
            return False

        # Sync the changed field
        success = github.update_challenge_phase_config(
            challenge_phase, changed_field
        )
        if success:
            logger.info(
                f"Successfully synced {changed_field} for challenge phase "
                f"{challenge_phase.pk}"
            )
        else:
            logger.error(
                f"Failed to sync {changed_field} for challenge phase "
                f"{challenge_phase.pk}"
            )
        return success

    except Exception as e:
        logger.error(f"Error in github_challenge_phase_sync: {str(e)}")
        return False


def trigger_challenge_sync(challenge, update_fields=None):
    """
    Trigger GitHub sync for a Challenge if conditions are met.

    Args:
        challenge: Challenge model instance
        update_fields: List of fields that were updated (from model.save())
    """
    # Skip if not configured for GitHub sync
    if not challenge.github_repository or not challenge.github_token:
        return

    # Skip if already synced in this request (prevent loops)
    if is_synced("Challenge", challenge.pk):
        logger.debug(
            f"Challenge {challenge.pk} already synced in this request"
        )
        return

    # Skip if request came from GitHub (prevent loops)
    if is_github_source():
        logger.debug("Skipping sync - request originated from GitHub")
        return

    # Determine which field changed
    changed_field = get_changed_field_from_update_fields(
        update_fields, CHALLENGE_SYNC_FIELDS
    )

    # If not from update_fields, try payload keys
    if not changed_field:
        changed_field = get_changed_field_from_payload(
            get_payload_keys(), CHALLENGE_SYNC_FIELDS
        )

    # Fallback: compare original field values if available
    if not changed_field:
        for field in CHALLENGE_SYNC_FIELDS:
            original_attr = f"_original_{field}"
            if hasattr(challenge, original_attr):
                original_value = getattr(challenge, original_attr)
                current_value = getattr(challenge, field)
                if original_value != current_value:
                    changed_field = field
                    logger.debug(
                        f"Detected changed field via original value comparison: "
                        f"{field} for challenge {challenge.pk}"
                    )
                    break

    if not changed_field:
        logger.debug(
            f"Could not determine changed field for challenge {challenge.pk}"
        )
        return

    # Mark as synced to prevent re-entry
    mark_synced("Challenge", challenge.pk)

    # Serialize and queue the sync task
    serialized_challenge = serializers.serialize("json", [challenge])
    github_challenge_sync.delay(serialized_challenge, changed_field)
    logger.info(
        f"Queued GitHub sync for challenge {challenge.pk}, field: {changed_field}"
    )


def trigger_challenge_phase_sync(challenge_phase, update_fields=None):
    """
    Trigger GitHub sync for a ChallengePhase if conditions are met.

    Args:
        challenge_phase: ChallengePhase model instance
        update_fields: List of fields that were updated (from model.save())
    """
    # Get parent challenge
    challenge = challenge_phase.challenge

    # Skip if not configured for GitHub sync
    if not challenge.github_repository or not challenge.github_token:
        return

    # Skip if already synced in this request (prevent loops)
    if is_synced("ChallengePhase", challenge_phase.pk):
        logger.debug(
            f"ChallengePhase {challenge_phase.pk} already synced in this request"
        )
        return

    # Skip if request came from GitHub (prevent loops)
    if is_github_source():
        logger.debug("Skipping phase sync - request originated from GitHub")
        return

    # Determine which field changed
    changed_field = get_changed_field_from_update_fields(
        update_fields, CHALLENGE_PHASE_SYNC_FIELDS
    )

    # If not from update_fields, try payload keys
    if not changed_field:
        changed_field = get_changed_field_from_payload(
            get_payload_keys(), CHALLENGE_PHASE_SYNC_FIELDS
        )

    # Fallback: compare original field values if available
    if not changed_field:
        for field in CHALLENGE_PHASE_SYNC_FIELDS:
            original_attr = f"_original_{field}"
            if hasattr(challenge_phase, original_attr):
                original_value = getattr(challenge_phase, original_attr)
                current_value = getattr(challenge_phase, field)
                if original_value != current_value:
                    changed_field = field
                    logger.debug(
                        f"Detected changed field via original value comparison: "
                        f"{field} for challenge phase {challenge_phase.pk}"
                    )
                    break

    if not changed_field:
        logger.debug(
            f"Could not determine changed field for challenge phase "
            f"{challenge_phase.pk}"
        )
        return

    # Mark as synced to prevent re-entry
    mark_synced("ChallengePhase", challenge_phase.pk)

    # Serialize and queue the sync task
    serialized_challenge_phase = serializers.serialize(
        "json", [challenge_phase]
    )
    serialized_challenge = serializers.serialize("json", [challenge])
    github_challenge_phase_sync.delay(
        serialized_challenge_phase, serialized_challenge, changed_field
    )
    logger.info(
        f"Queued GitHub sync for challenge phase {challenge_phase.pk}, "
        f"field: {changed_field}"
    )
