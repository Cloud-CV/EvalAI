import base64
import json
import logging
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urljoin

import requests

logger = logging.getLogger(__name__)

URLS = {"contents": "/repos/{}/contents/{}", "repos": "/repos/{}"}


class GithubInterface:
    """
    Interface for GitHub API operations
    """

    def __init__(self, token, repo):
        self.token = token
        self.repo = repo
        self.base_url = "https://api.github.com"
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
        }

    def get_github_url(self, url):
        """Get the full GitHub API URL"""
        return urljoin(self.base_url, url)

    def get_file_contents(self, path: str) -> Optional[Dict[str, Any]]:
        """
        Get file contents from GitHub repository
        """
        url = URLS["contents"].format(self.repo, path)
        full_url = self.get_github_url(url)
        
        # No ref -> GitHub uses default branch
        response = requests.get(full_url, headers=self.headers)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            return None
        else:
            logger.error(f"Failed to get file contents: {response.status_code}")
            return None

    def _put_file(self, path: str, base64_content: str, message: str, sha: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create or update file in GitHub repository with base64 content
        """
        url = URLS["contents"].format(self.repo, path)
        full_url = self.get_github_url(url)
        
        data = {
            "message": message,
            "content": base64_content,
        }
        
        if sha:
            data["sha"] = sha
        
        response = requests.put(full_url, headers=self.headers, json=data)
        
        if response.status_code in [200, 201]:
            return response.json()
        else:
            logger.error(f"Failed to update file: {response.status_code}")
            return None

    def update_text_file(self, path: str, content: str, message: str, sha: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return self._put_file(path, base64.b64encode(content.encode()).decode(), message, sha)

    def update_binary_file(self, path: str, content_bytes: bytes, message: str, sha: Optional[str] = None) -> Optional[Dict[str, Any]]:
        return self._put_file(path, base64.b64encode(content_bytes).decode(), message, sha)

    @staticmethod
    def _decode_github_file_content(file_data: Dict[str, Any]) -> Optional[bytes]:
        try:
            encoded = file_data.get("content")
            if not encoded:
                return None
            # GitHub may include newlines in base64 content
            return base64.b64decode(encoded)
        except Exception as exc:
            logger.error(f"Failed to decode GitHub content: {exc}")
            return None

    @staticmethod
    def _diff_top_level_keys(old: Dict[str, Any], new: Dict[str, Any]) -> Tuple[bool, Tuple[str, ...]]:
        changed_keys = []
        all_keys = set(old.keys()) | set(new.keys())
        for key in sorted(all_keys):
            if old.get(key) != new.get(key):
                changed_keys.append(key)
        return (len(changed_keys) > 0, tuple(changed_keys))

    def update_json_if_changed(self, path: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create/update a JSON file only if content changed. Commit message lists changed keys.
        """
        try:
            file_data = self.get_file_contents(path)
            new_json_text = json.dumps(data, indent=2, sort_keys=True)
            if file_data:
                old_bytes = self._decode_github_file_content(file_data) or b""
                try:
                    old_json = json.loads(old_bytes.decode() or "{}")
                except Exception:
                    old_json = {}
                changed, changed_keys = self._diff_top_level_keys(old_json, data)
                if not changed:
                    logger.info(f"No changes for {path}. Skipping commit.")
                    return None
                message = f"Update {path}: keys updated: {', '.join(changed_keys)}"
                return self.update_text_file(path, new_json_text, message, file_data.get("sha"))
            else:
                message = f"Create {path} via EvalAI sync"
                return self.update_text_file(path, new_json_text, message)
        except Exception as exc:
            logger.error(f"Error updating JSON at {path}: {exc}")
            return None

    def update_binary_if_changed(self, path: str, content_bytes: bytes, create_message: str, update_message_prefix: str) -> Optional[Dict[str, Any]]:
        try:
            file_data = self.get_file_contents(path)
            if file_data:
                old_bytes = self._decode_github_file_content(file_data) or b""
                if old_bytes == content_bytes:
                    logger.info(f"No binary changes for {path}. Skipping commit.")
                    return None
                message = f"{update_message_prefix} {path}"
                return self.update_binary_file(path, content_bytes, message, file_data.get("sha"))
            else:
                return self.update_binary_file(path, content_bytes, create_message)
        except Exception as exc:
            logger.error(f"Error updating binary at {path}: {exc}")
            return None


def _fetch_auth_token_from_repo(repo: str, candidate_token: Optional[str] = None) -> Optional[str]:
    """
    Try to read AUTH_TOKEN file from the repository. This supports two modes:
    1) Unauthenticated read (works only for public repos)
    2) Authenticated read using a candidate token if provided

    Returns the token string if found, else None.
    """
    base_url = "https://api.github.com"
    path = URLS["contents"].format(repo, "AUTH_TOKEN")
    url = urljoin(base_url, path)

    def _request(headers: Optional[Dict[str, str]]) -> Optional[str]:
        try:
            # No ref -> default branch
            response = requests.get(url, headers=headers or {})
            if response.status_code == 200:
                data = response.json()
                content_b64 = data.get("content")
                if not content_b64:
                    return None
                try:
                    value = base64.b64decode(content_b64).decode().strip()
                except Exception:
                    return None
                return value or None
            return None
        except Exception:
            return None

    # Try unauthenticated first (public repo)
    token_value = _request(None)
    if token_value:
        return token_value

    # Try with candidate token if provided (for private repo)
    if candidate_token:
        headers = {
            "Authorization": f"token {candidate_token}",
            "Accept": "application/vnd.github.v3+json",
        }
        token_value = _request(headers)
        if token_value:
            return token_value

    return None


def sync_challenge_to_github(challenge):
    """
    Sync challenge data to GitHub repository
    """
    if not challenge.github_repository:
        logger.warning("GitHub repository not configured for challenge")
        return
    
    try:
        repo = challenge.github_repository

        # Enforce AUTH_TOKEN from repo if available; fallback to challenge.github_token
        repo_auth_token = _fetch_auth_token_from_repo(repo, candidate_token=challenge.github_token)
        resolved_token = repo_auth_token or challenge.github_token
        if not resolved_token:
            logger.warning("Neither repo AUTH_TOKEN nor challenge.github_token is available; skipping sync")
            return

        github = GithubInterface(resolved_token, repo)
        
        # Sync non-file fields
        challenge_data = {
            "title": challenge.title,
            "description": challenge.description,
            "short_description": challenge.short_description,
            "terms_and_conditions": challenge.terms_and_conditions,
            "submission_guidelines": challenge.submission_guidelines,
            "evaluation_details": challenge.evaluation_details,
            "start_date": challenge.start_date.isoformat() if challenge.start_date else None,
            "end_date": challenge.end_date.isoformat() if challenge.end_date else None,
            "domain": challenge.domain,
            "list_tags": challenge.list_tags,
            "has_prize": challenge.has_prize,
            "has_sponsors": challenge.has_sponsors,
            "published": challenge.published,
            "submission_time_limit": challenge.submission_time_limit,
            "is_registration_open": challenge.is_registration_open,
            "enable_forum": challenge.enable_forum,
            "forum_url": challenge.forum_url,
            "leaderboard_description": challenge.leaderboard_description,
            "anonymous_leaderboard": challenge.anonymous_leaderboard,
            "manual_participant_approval": challenge.manual_participant_approval,
            "is_disabled": challenge.is_disabled,
            "approved_by_admin": challenge.approved_by_admin,
            "uses_ec2_worker": challenge.uses_ec2_worker,
            "ec2_storage": challenge.ec2_storage,
            "ephemeral_storage": challenge.ephemeral_storage,
            "featured": challenge.featured,
            "allowed_email_domains": challenge.allowed_email_domains,
            "blocked_email_domains": challenge.blocked_email_domains,
            "banned_email_ids": challenge.banned_email_ids,
            "remote_evaluation": challenge.remote_evaluation,
            "queue": challenge.queue,
            "sqs_retention_period": challenge.sqs_retention_period,
            "is_docker_based": challenge.is_docker_based,
            "is_static_dataset_code_upload": challenge.is_static_dataset_code_upload,
            "max_docker_image_size": challenge.max_docker_image_size,
            "max_concurrent_submission_evaluation": challenge.max_concurrent_submission_evaluation,
            "use_host_credentials": challenge.use_host_credentials,
            "use_host_sqs": challenge.use_host_sqs,
            "allow_resuming_submissions": challenge.allow_resuming_submissions,
            "allow_host_cancel_submissions": challenge.allow_host_cancel_submissions,
            "allow_cancel_running_submissions": challenge.allow_cancel_running_submissions,
            "allow_participants_resubmissions": challenge.allow_participants_resubmissions,
            "cli_version": challenge.cli_version,
            "workers": challenge.workers,
            "task_def_arn": challenge.task_def_arn,
            "slack_webhook_url": challenge.slack_webhook_url,
            "worker_cpu_cores": challenge.worker_cpu_cores,
            "worker_memory": challenge.worker_memory,
            "inform_hosts": challenge.inform_hosts,
            "vpc_cidr": challenge.vpc_cidr,
            "subnet_1_cidr": challenge.subnet_1_cidr,
            "subnet_2_cidr": challenge.subnet_2_cidr,
            "worker_instance_type": challenge.worker_instance_type,
            "worker_ami_type": challenge.worker_ami_type,
            "worker_disk_size": challenge.worker_disk_size,
            "max_worker_instance": challenge.max_worker_instance,
            "min_worker_instance": challenge.min_worker_instance,
            "desired_worker_instance": challenge.desired_worker_instance,
            "cpu_only_jobs": challenge.cpu_only_jobs,
            "job_cpu_cores": challenge.job_cpu_cores,
            "job_memory": challenge.job_memory,
            "worker_image_url": challenge.worker_image_url,
            "evaluation_module_error": challenge.evaluation_module_error,
        }
        
        # Update challenge data
        github.update_json_if_changed("challenge.json", challenge_data)
        
        # Sync file fields if they exist
        if challenge.evaluation_script:
            try:
                field_file = challenge.evaluation_script
                field_file.open("rb")
                try:
                    content_bytes = field_file.read()
                finally:
                    field_file.close()
                file_name = "evaluation_script.zip"
                github.update_binary_if_changed(
                    file_name,
                    content_bytes,
                    create_message=f"Add {file_name} via EvalAI sync",
                    update_message_prefix="Update",
                )
            except Exception as exc:
                logger.error(f"Failed to sync evaluation_script for challenge {challenge.id}: {exc}")
        
        logger.info(f"Successfully synced challenge {challenge.id} to GitHub")
        
    except Exception as e:
        logger.error(f"Error syncing challenge {challenge.id} to GitHub: {str(e)}")


def sync_challenge_phase_to_github(challenge_phase):
    """
    Sync challenge phase data to GitHub repository
    """
    challenge = challenge_phase.challenge
    if not challenge.github_repository:
        logger.warning("GitHub repository not configured for challenge")
        return
    
    try:
        repo = challenge.github_repository
        repo_auth_token = _fetch_auth_token_from_repo(repo, candidate_token=challenge.github_token)
        resolved_token = repo_auth_token or challenge.github_token
        if not resolved_token:
            logger.warning("Neither repo AUTH_TOKEN nor challenge.github_token is available; skipping phase sync")
            return

        github = GithubInterface(resolved_token, repo)
        
        # Sync non-file fields
        phase_data = {
            "name": challenge_phase.name,
            "description": challenge_phase.description,
            "leaderboard_public": challenge_phase.leaderboard_public,
            "start_date": challenge_phase.start_date.isoformat() if challenge_phase.start_date else None,
            "end_date": challenge_phase.end_date.isoformat() if challenge_phase.end_date else None,
            "is_public": challenge_phase.is_public,
            "is_submission_public": challenge_phase.is_submission_public,
            "annotations_uploaded_using_cli": challenge_phase.annotations_uploaded_using_cli,
            "max_submissions_per_day": challenge_phase.max_submissions_per_day,
            "max_submissions_per_month": challenge_phase.max_submissions_per_month,
            "max_submissions": challenge_phase.max_submissions,
            "max_concurrent_submissions_allowed": challenge_phase.max_concurrent_submissions_allowed,
            "codename": challenge_phase.codename,
            "allowed_email_ids": challenge_phase.allowed_email_ids,
            "environment_image": challenge_phase.environment_image,
            "allowed_submission_file_types": challenge_phase.allowed_submission_file_types,
            "is_restricted_to_select_one_submission": challenge_phase.is_restricted_to_select_one_submission,
            "submission_meta_attributes": challenge_phase.submission_meta_attributes,
            "is_partial_submission_evaluation_enabled": challenge_phase.is_partial_submission_evaluation_enabled,
            "config_id": challenge_phase.config_id,
            "default_submission_meta_attributes": challenge_phase.default_submission_meta_attributes,
            "disable_logs": challenge_phase.disable_logs,
        }
        
        # Update phase data
        phase_path = f"phases/{challenge_phase.codename}.json"
        github.update_json_if_changed(phase_path, phase_data)
        
        # Sync file fields if they exist
        if challenge_phase.test_annotation:
            try:
                field_file = challenge_phase.test_annotation
                field_file.open("rb")
                try:
                    content_bytes = field_file.read()
                finally:
                    field_file.close()
                file_name = f"annotations/{challenge_phase.codename}.json"
                github.update_binary_if_changed(
                    file_name,
                    content_bytes,
                    create_message=f"Add {file_name} via EvalAI sync",
                    update_message_prefix="Update",
                )
            except Exception as exc:
                logger.error(f"Failed to sync test_annotation for phase {challenge_phase.id}: {exc}")
        
        logger.info(f"Successfully synced challenge phase {challenge_phase.id} to GitHub")
        
    except Exception as e:
        logger.error(f"Error syncing challenge phase {challenge_phase.id} to GitHub: {str(e)}") 