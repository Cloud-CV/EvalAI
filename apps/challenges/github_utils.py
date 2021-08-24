import requests
import logging
import base64
import yaml

from base.utils import deserialize_object
from .github_sync_config import (
    challenge_non_file_fields,
    challenge_file_fields,
    challenge_phase_non_file_fields,
    challenge_phase_file_fields,
)
from evalai.celery import app

logger = logging.getLogger(__name__)

URLS = {"contents": "/repos/{}/contents/{}", "repos": "/repos/{}"}


class GithubInterface:
    def __init__(self, GITHUB_AUTH_TOKEN, GITHUB_REPOSITORY):
        self.GITHUB_AUTH_TOKEN = GITHUB_AUTH_TOKEN
        self.GITHUB_REPOSITORY = GITHUB_REPOSITORY
        self.BRANCH = "challenge"
        self.COMMIT_PREFIX = "evalai_bot: Update {}"

    def get_request_headers(self):
        headers = {"Authorization": "token {}".format(self.GITHUB_AUTH_TOKEN)}
        return headers

    def make_request(self, url, method, params={}, data={}):
        url = self.get_github_url(url)
        headers = self.get_request_headers()
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=data,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "EvalAI is not able to establish connection with github {}".format(
                    response.json()
                )
            )
            return None
        return response.json()

    def get_github_url(self, url):
        base_url = "https://api.github.com"
        url = "{0}{1}".format(base_url, url)
        return url

    def get_content_from_path(self, path):
        """
        Gets the file content, information in json format in the repository at particular path
        Ref: https://docs.github.com/en/rest/reference/repos#contents
        """
        url = URLS.get("contents").format(self.GITHUB_REPOSITORY, path)
        params = {"ref": self.BRANCH}
        response = self.make_request(url, "GET", params)
        return response

    def get_data_from_path(self, path):
        """
        Gets the file data in string format in the repository at particular path
        Calls get_content_from_path and encode the base64 content
        """
        content_response = self.get_content_from_path(path)
        string_data = None
        if content_response and content_response.get("content"):
            string_data = base64.b64decode(content_response["content"]).decode(
                "utf-8"
            )
        return string_data

    def update_content_from_path(self, path, content):
        """
        Updates the file content, creates a commit in the repository at particular path
        Ref: https://docs.github.com/en/rest/reference/repos#create-or-update-file-contents
        """
        url = URLS.get("contents").format(self.GITHUB_REPOSITORY, path)
        data = {
            "message": self.COMMIT_PREFIX.format(path),
            "branch": self.BRANCH,
            "sha": self.get_content_from_path(path).get("sha"),
            "content": content,
        }
        response = self.make_request(url, "PUT", data=data)
        return response

    def update_data_from_path(self, path, data):
        """
        Updates the file data to the data(string) provided, at particular path
        Call update_content_from_path with decoded base64 content
        """
        content = base64.b64encode(bytes(data, "utf-8")).decode("utf-8")
        return self.update_content_from_path(path, content)

    def is_repository(self):
        url = URLS.get("repos").format(self.GITHUB_REPOSITORY)
        repo_response = self.make_request(url, "GET")
        return True if repo_response else False


@app.task
def github_challenge_sync(challenge):
    from .serializers import ZipChallengeSerializer

    challenge_obj = deserialize_object(challenge)
    serializer = ZipChallengeSerializer(challenge_obj)
    challenge = serializer.data
    github = GithubInterface(
        GITHUB_REPOSITORY=challenge.get("github_repository"),
        GITHUB_AUTH_TOKEN=challenge.get("github_token"),
    )
    if not github.is_repository():
        return
    try:
        # Challenge Non-file field Update
        challenge_config_str = github.get_data_from_path(
            "challenge_config.yaml"
        )
        challenge_config_yaml = yaml.safe_load(challenge_config_str)
        update_challenge_config = False
        for field in challenge_non_file_fields:
            # Ignoring commits when no update in field value
            if (
                challenge_config_yaml.get(field) is not None
                and challenge_config_yaml[field] == challenge[field]
            ):
                continue
            update_challenge_config = True
            challenge_config_yaml[field] = challenge[field]
        if update_challenge_config:
            content_str = yaml.dump(challenge_config_yaml, sort_keys=False)
            github.update_data_from_path("challenge_config.yaml", content_str)

        # Challenge File fields Update
        for field in challenge_file_fields:
            if challenge_config_yaml.get(field) is None:
                continue
            field_path = challenge_config_yaml[field]
            field_str = github.get_data_from_path(field_path)
            if field_str is None or field_str == challenge[field]:
                continue
            github.update_data_from_path(field_path, challenge[field])
    except Exception as e:
        logger.info("Github Sync unsuccessful due to {}".format(e))


@app.task
def github_challenge_phase_sync(challenge_phase):
    from .serializers import ChallengePhaseSerializer

    challenge_phase_obj = deserialize_object(challenge_phase)
    challenge = challenge_phase_obj.challenge
    serializer = ChallengePhaseSerializer(challenge_phase_obj)
    challenge_phase = serializer.data
    github = GithubInterface(
        GITHUB_REPOSITORY=challenge.github_repository,
        GITHUB_AUTH_TOKEN=challenge.github_token,
    )
    if not github.is_repository():
        return
    try:
        # Non-file field Update
        challenge_phase_unique = "codename"
        challenge_config_str = github.get_data_from_path(
            "challenge_config.yaml"
        )
        challenge_config_yaml = yaml.safe_load(challenge_config_str)
        update_challenge_config = False

        for phase in challenge_config_yaml["challenge_phases"]:
            if (
                phase.get(challenge_phase_unique)
                != challenge_phase[challenge_phase_unique]
            ):
                continue
            for field in challenge_phase_non_file_fields:
                # Ignoring commits when no update in field value
                if (
                    phase.get(field) is not None
                    and phase[field] == challenge_phase[field]
                ):
                    continue
                update_challenge_config = True
                phase[field] = challenge_phase[field]
            break

        if update_challenge_config:
            content_str = yaml.dump(challenge_config_yaml, sort_keys=False)
            github.update_data_from_path("challenge_config.yaml", content_str)

        # File fields Update
        for phase in challenge_config_yaml["challenge_phases"]:
            if (
                phase.get(challenge_phase_unique)
                != challenge_phase[challenge_phase_unique]
            ):
                continue
            for field in challenge_phase_file_fields:
                if phase.get(field) is None:
                    continue
                field_path = phase[field]
                field_str = github.get_data_from_path(field_path)
                if field_str is None or field_str == challenge_phase[field]:
                    continue
                github.update_data_from_path(
                    field_path, challenge_phase[field]
                )
            break

    except Exception as e:
        logger.info(
            "Github Sync Challenge Phase unsuccessful due to {}".format(e)
        )
