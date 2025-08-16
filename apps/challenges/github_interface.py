import requests
import base64
import logging

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