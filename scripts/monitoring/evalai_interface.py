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
    "get_challenge_by_pk": "/api/challenges/challenge/{}/",
    "get_challenges": "/api/challenges/challenge/all/all/all",
    "get_submissions_for_challenge": "/api/jobs/challenge/{}/submission/",
    "get_challenges_submission_metrics": "/api/challenges/challenge/get_submission_metrics",
    "get_challenge_submission_metrics_by_pk": "/api/challenges/challenge/get_submission_metrics_by_pk/{}/",
    "manage_ec2_instance": "/api/challenges/{}/manage_ec2_instance/{}",
    "get_ec2_instance_details": "/api/challenges/{}/get_ec2_instance_details/",
}


class EvalAI_Interface:
    def __init__(self, AUTH_TOKEN, EVALAI_API_SERVER):
        self.AUTH_TOKEN = AUTH_TOKEN
        self.EVALAI_API_SERVER = EVALAI_API_SERVER

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

    def get_message_from_sqs_queue(self, queue_name):
        url = URLS.get("get_message_from_sqs_queue").format(queue_name)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def delete_message_from_sqs_queue(self, receipt_handle, queue_name):
        url = URLS.get("delete_message_from_sqs_queue").format(queue_name)
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

    def get_challenge_by_queue_name(self, queue_name):
        url = URLS.get("get_challenge_by_queue_name").format(queue_name)
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

    def update_submission_data(self, data, challenge_pk):
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

    def get_challenge_by_pk(self, challenge_pk):
        url = URLS.get("get_challenge_by_pk").format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenges(self):
        url = URLS.get("get_challenges")
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_submissions_for_challenge(self, submission_pk, status=None):
        url_template = URLS.get("get_submissions_for_challenge")
        url = url_template.format(submission_pk)
        url = self.return_url_per_environment(url)
        if status:
            url += f"?status={status}"
        response = self.make_request(url, "GET")
        return response

    def get_challenges_submission_metrics(self):
        url = URLS.get("get_challenges_submission_metrics")
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_challenge_submission_metrics_by_pk(self, challenge_pk):
        url_template = URLS.get("get_challenge_submission_metrics_by_pk")
        url = url_template.format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def get_ec2_instance_details(self, challenge_pk):
        url_template = URLS.get("get_ec2_instance_details")
        url = url_template.format(challenge_pk)
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "GET")
        return response

    def start_challenge_ec2_instance(self, challenge_pk):
        url_template = URLS.get("manage_ec2_instance")
        url = url_template.format(challenge_pk, "start")
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PUT")
        return response

    def stop_challenge_ec2_instance(self, challenge_pk):
        url_template = URLS.get("manage_ec2_instance")
        url = url_template.format(challenge_pk, "stop")
        url = self.return_url_per_environment(url)
        response = self.make_request(url, "PUT")
        return response
