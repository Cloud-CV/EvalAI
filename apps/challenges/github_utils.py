import requests
import logging
import base64
import yaml

from django.core import serializers

from evalai.celery import app

logger = logging.getLogger(__name__)

URLS = {"contents": "/repos/{}/contents/{}", "repos": "/repos/{}"}


class Github_Interface:
    def __init__(self, GITHUB_AUTH_TOKEN, GITHUB_REPOSITORY):
        self.GITHUB_AUTH_TOKEN = GITHUB_AUTH_TOKEN
        self.GITHUB_REPOSITORY = GITHUB_REPOSITORY
        self.BRANCH = "challenge"
        self.COMMIT_PREFIX = "evalai_bot: Update {}"

    def get_request_headers(self):
        headers = {"Authorization": "token {}".format(self.GITHUB_AUTH_TOKEN)}
        return headers

    def make_request(self, url, method, params={}, data={}):
        url = self.return_github_url(url)
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

    def return_github_url(self, url):
        base_url = "https://api.github.com"
        url = "{0}{1}".format(base_url, url)
        return url

    def get_content_from_path(self, path):
        url = URLS.get("contents").format(self.GITHUB_REPOSITORY, path)
        params = {"ref": self.BRANCH}
        response = self.make_request(url, "GET", params)
        return response

    def get_data_from_path(self, path):
        content_response = self.get_content_from_path(path)
        string_data = None
        if content_response and content_response.get("content"):
            string_data = base64.b64decode(content_response["content"])
        return string_data

    def update_content_from_path(self, path, content):
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
        content = base64.b64encode(bytes(data, "utf-8")).decode("utf-8")
        return self.update_content_from_path(path, content)

    def is_repo(self):
        url = URLS.get("repos").format(self.GITHUB_REPOSITORY)
        repo_response = self.make_request(url, "GET")
        return True if repo_response else False


@app.task
def github_challenge_sync(challenge):
    from .serializers import ZipChallengeSerializer

    for obj in serializers.deserialize("json", challenge):
        challenge_obj = obj.object
    serializer = ZipChallengeSerializer(challenge_obj)
    challenge = serializer.data
    github = Github_Interface(
        GITHUB_REPOSITORY=challenge.get("github_repository"),
        GITHUB_AUTH_TOKEN=challenge.get("github_token"),
    )
    if not github.is_repo():
        return
    try:
        non_file_fields = [
            "title",
            "short_description",
            "leaderboard_description",
            "remote_evaluation",
            "is_docker_based",
            "is_static_dataset_code_upload",
            "start_date",
            "end_date",
            "published",
        ]
        challenge_config_str = github.get_data_from_path(
            "challenge_config.yaml"
        )
        challenge_config_yaml = yaml.safe_load(challenge_config_str)
        update_challenge_config = False
        for field in non_file_fields:
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
    except Exception as e:
        logger.info("Github Sync unsuccessful due to {}".format(e))
