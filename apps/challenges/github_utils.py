import logging
import yaml

from base.utils import deserialize_object
from .github_sync_config import (
    challenge_non_file_fields,
    challenge_file_fields,
    challenge_phase_non_file_fields,
    challenge_phase_file_fields,
)
from .github_interface import GithubInterface
from evalai.celery import app

logger = logging.getLogger(__name__)


@app.task
def github_challenge_sync(challenge):
    challenge = deserialize_object(challenge)
    github = GithubInterface(
        GITHUB_REPOSITORY=getattr(challenge, "github_repository"),
        GITHUB_AUTH_TOKEN=getattr(challenge, "github_token"),
    )
    if not github.is_repository():
        return
    try:
        # Challenge non-file field update
        challenge_config_str = github.get_data_from_path(
            "challenge_config.yaml"
        )
        challenge_config_yaml = yaml.safe_load(challenge_config_str)
        update_challenge_config = False
        for field in challenge_non_file_fields:
            # Ignoring commits when no update in field value
            if challenge_config_yaml.get(
                field
            ) is not None and challenge_config_yaml[field] == getattr(
                challenge, field
            ):
                continue
            update_challenge_config = True
            challenge_config_yaml[field] = getattr(challenge, field)
        if update_challenge_config:
            content_str = yaml.dump(challenge_config_yaml, sort_keys=False)
            github.update_data_from_path("challenge_config.yaml", content_str)

        # Challenge file fields update
        for field in challenge_file_fields:
            if challenge_config_yaml.get(field) is None:
                continue
            field_path = challenge_config_yaml[field]
            field_str = github.get_data_from_path(field_path)
            if field_str is None or field_str == getattr(challenge, field):
                continue
            github.update_data_from_path(field_path, getattr(challenge, field))
    except Exception as e:
        logger.error("Github Sync unsuccessful due to {}".format(e))


@app.task
def github_challenge_phase_sync(challenge_phase):
    challenge_phase = deserialize_object(challenge_phase)
    challenge = challenge_phase.challenge
    github = GithubInterface(
        GITHUB_REPOSITORY=getattr(challenge, "github_repository"),
        GITHUB_AUTH_TOKEN=getattr(challenge, "github_token"),
    )
    if not github.is_repository():
        return
    try:
        # Challenge phase non-file field update
        challenge_phase_unique = "codename"
        challenge_config_str = github.get_data_from_path(
            "challenge_config.yaml"
        )
        challenge_config_yaml = yaml.safe_load(challenge_config_str)
        update_challenge_config = False

        for phase in challenge_config_yaml["challenge_phases"]:
            if phase.get(challenge_phase_unique) != getattr(
                challenge_phase, challenge_phase_unique
            ):
                continue
            for field in challenge_phase_non_file_fields:
                # Ignoring commits when no update in field value
                if phase.get(field) is not None and phase[field] == getattr(
                    challenge_phase, field
                ):
                    continue
                update_challenge_config = True
                phase[field] = getattr(challenge_phase, field)
            break
        if update_challenge_config:
            content_str = yaml.dump(challenge_config_yaml, sort_keys=False)
            github.update_data_from_path("challenge_config.yaml", content_str)

        # Challenge phase file fields update
        for phase in challenge_config_yaml["challenge_phases"]:
            if phase.get(challenge_phase_unique) != getattr(
                challenge_phase, challenge_phase_unique
            ):
                continue
            for field in challenge_phase_file_fields:
                if phase.get(field) is None:
                    continue
                field_path = phase[field]
                field_str = github.get_data_from_path(field_path)
                if field_str is None or field_str == getattr(
                    challenge_phase, field
                ):
                    continue
                github.update_data_from_path(
                    field_path, getattr(challenge_phase, field)
                )
            break
    except Exception as e:
        logger.error(
            "Github Sync Challenge Phase unsuccessful due to {}".format(e)
        )