import logging
import requests

logger = logging.getLogger(__name__)


URLS = {
    "get_message_from_sqs_queue": "/api/jobs/challenge/queues/{}/",
    "delete_message_from_sqs_queue": "/api/jobs/queues/{}/",
    "get_submission_by_pk": "/api/jobs/submission/{}",
    "get_challenge_phases_by_challenge_pk": "/api/challenges/{}/phases/",
    "get_challenge_by_queue_name": "/api/challenges/challenge/queues/{}/",
    "get_challenge_phase_by_pk": "/api/challenges/challenge/{}/challenge_phase/{}",
    "update_submission_data": "/api/jobs/challenge/{}/update_submission/",
    "get_aws_eks_bearer_token": "/api/jobs/challenge/{}/eks_bearer_token/",
    "get_aws_eks_cluster_details": "/api/challenges/{}/evaluation_cluster/",
}


class EvalAI_Interface:
    def __init__(self, AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME):
        self.AUTH_TOKEN = AUTH_TOKEN
        self.EVALAI_API_SERVER = EVALAI_API_SERVER
        self.QUEUE_NAME = QUEUE_NAME

    def get_request_headers(self):
        headers = {"Authorization": "Bearer {}".format(self.AUTH_TOKEN)}
        return headers

    def make_request(self, url, method, data=None):
        headers = self.get_request_headers()
        try:
            response = requests.request(
                method=method, url=url, headers=headers, data=data
            )
            response.raise_for_status()
        except requests.exceptions.RequestException:
            logger.info(
                "The worker is not able to establish connection with EvalAI"
            )
            raise
        return response.json()

    def return_url_per_environment(self, url):
        base_url = "{0}".format(self.EVALAI_API_SERVER)
        url = "{0}{1}".format(base_url, url)
        return url

    def get_message_from_sqs_queue(self):
        url = URLS.get("get_message_from_sqs_queue").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def delete_message_from_sqs_queue(self, receipt_handle):
        url = URLS.get("delete_message_from_sqs_queue").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        data = {"receipt_handle": receipt_handle}
        response = self.make_request(url, "POST", data)  # noqa
        return response

    def get_submission_by_pk(self, submission_pk):
        url = URLS.get("get_submission_by_pk").format(submission_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_phases_by_challenge_pk(self, challenge_pk):
        url = URLS.get("get_challenge_phases_by_challenge_pk").format(
            challenge_pk
        )
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_by_queue_name(self):
        url = URLS.get("get_challenge_by_queue_name").format(self.QUEUE_NAME)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_phase_by_pk(self, challenge_pk, challenge_phase_pk):
        url = URLS.get("get_challenge_phase_by_pk").format(
            challenge_pk, challenge_phase_pk
        )
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def update_submission_data(self, data, challenge_pk, submission_pk):
        url = URLS.get("update_submission_data").format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PUT", data=data)
        return response

    def update_submission_status(self, data, challenge_pk):
        url = URLS.get("update_submission_data").format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PATCH", data=data)
        return response

    def get_aws_eks_bearer_token(self, challenge_pk):
        url = URLS.get("get_aws_eks_bearer_token").format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_aws_eks_cluster_details(self, challenge_pk):
        url = URLS.get("get_aws_eks_cluster_details").format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response
