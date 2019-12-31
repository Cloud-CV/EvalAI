import random
import requests
import responses
import string

from unittest import mock
from unittest import TestCase

from scripts.workers.worker_util import EvalAI_Interface


auth_token = "".join(random.choice(string.ascii_lowercase) for _ in range(40))
evalai_api_server = "https://evalapi.cloudcv.org"
queue_name = "evalai_submission_queue"
interface = EvalAI_Interface(auth_token, evalai_api_server, queue_name)


class BaseTestClass(TestCase):
    def setUp(self):
        # Keeping all values different so that it is recognized if one of them is confused with the other
        self.challenge_pk = 1
        self.challenge_phase_pk = 2
        self.submission_pk = 3

    def make_request_url(self):
        return "/test/url"

    def get_message_from_sqs_queue_url(self, queue_name):
        return "/api/jobs/challenge/queues/{}/".format(queue_name)

    def delete_message_from_sqs_queue_url(self, queue_name):
        return "/api/jobs/queues/{}/".format(queue_name)

    def get_submission_by_pk_url(self, submission_pk):
        return "/api/jobs/submission/{}".format(submission_pk)

    def get_challenge_phases_by_challenge_pk_url(self, challenge_pk):
        return "/api/challenges/{}/phases/".format(challenge_pk)

    def get_challenge_by_queue_name_url(self, queue_name):
        return "/api/challenges/challenge/queues/{}/".format(queue_name)

    def get_challenge_phase_by_pk_url(self, challenge_pk, challenge_phase_pk):
        return "/api/challenges/challenge/{}/challenge_phase/{}".format(challenge_pk, challenge_phase_pk)

    def update_submission_data_url(self, challenge_pk):
        return "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)

    def update_submission_status_url(self, challenge_pk):
        return "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)


class WorkerUtilTestClass(BaseTestClass):
    def setUp(self):
        super(WorkerUtilTestClass, self).setUp()
        self.success_response = {"message": "success", "status_code": 200}
        self.example_error = "ExampleError: Example description"

    def test_return_url_per_environment(self):
        returned_url = interface.return_url_per_environment(self.make_request_url())
        expected = "{0}{1}".format(evalai_api_server, self.make_request_url())
        self.assertEqual(returned_url, expected)

    @responses.activate
    def test_make_request_get_success(self):
        url = "{0}{1}".format(evalai_api_server, self.make_request_url())
        responses.add(responses.GET, url,
                      json=self.success_response,
                      content_type='application/json',
                      status=200)

        response = interface.make_request(url, "GET")

        self.assertEqual(response, self.success_response)

    @responses.activate
    @mock.patch("scripts.workers.worker_util.logger.info")
    def test_make_request_http_error(self, mock_logger):
        url = "{0}{1}".format(evalai_api_server, self.make_request_url())
        responses.add(responses.GET, url,
                      json={"error": "404 Not Found"},
                      status=404)

        with self.assertRaises(requests.exceptions.HTTPError):
            interface.make_request(url, "GET")

        mock_logger.assert_called_with("The worker is not able to establish connection with EvalAI")

    @responses.activate
    @mock.patch("scripts.workers.worker_util.logger.info")
    def test_make_request_connection_error(self, mock_logger):
        url = "{0}{1}".format(evalai_api_server, self.make_request_url())
        responses.add(responses.GET, url,
                      body=Exception(self.example_error))

        with self.assertRaises(requests.exceptions.RequestException):
            interface.make_request(url, "GET")

        mock_logger.assert_called_with("The worker is not able to establish connection with EvalAI")

    @mock.patch("interface.make_request")
    def test_get_message_from_sqs_queue(self, mock_make_request):
        url = "{}{}".format(evalai_api_server, self.get_message_from_sqs_queue_url(queue_name))
        mock_make_request.return_value = self.success_response

        response = interface.get_message_from_sqs_queue()

        mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    @mock.patch("interface.make_request")
    def test_get_submission_by_pk(self, mock_make_request):
        url = "{}{}".format(evalai_api_server, self.get_submission_by_pk_url(self.submission_pk))
        mock_make_request.return_value = self.success_response

        response = interface.get_submission_by_pk(self.submission_pk)

        mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    @mock.patch("interface.make_request")
    def test_get_challenge_phases_by_challenge_pk(self, mock_make_request):
        url = "{}{}".format(evalai_api_server, self.get_challenge_phases_by_challenge_pk_url(self.challenge_pk))
        mock_make_request.return_value = self.success_response

        response = interface.get_challenge_phases_by_challenge_pk(self.challenge_pk)

        mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    @mock.patch("interface.make_request")
    def test_get_challenge_by_queue_name(self, mock_make_request):
        url = "{}{}".format(evalai_api_server, self.get_challenge_by_queue_name_url(queue_name))
        mock_make_request.return_value = self.success_response

        response = interface.get_challenge_by_queue_name()

        mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    @mock.patch("interface.make_request")
    def test_get_challenge_phase_by_pk(self, mock_make_request):
        url = "{}{}".format(evalai_api_server, self.get_challenge_phase_by_pk_url(self.challenge_phase_pk))
        mock_make_request.return_value = self.success_response

        response = interface.get_challenge_phase_by_pk(self.challenge_phase_pk)

        mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    @mock.patch("interface.make_request")
    def test_update_submission_data(self, mock_make_request):
        url = "{}{}".format(evalai_api_server, self.update_submission_data_url(self.challenge_pk))
        data = {"submission_pk": self.submission_pk, "test_field": "new_value"}
        mock_make_request.return_value = self.success_response

        response = interface.update_submission_data(data, self.challenge_pk)

        mock_make_request.assert_called_with(url, "PUT", data=data)
        self.assertEqual(response, self.success_response)

    @mock.patch("interface.make_request")
    def test_update_submission_status(self, mock_make_request):
        url = "{}{}".format(evalai_api_server, self.update_submission_status_url(self.challenge_pk))
        data = {"test_field": "new_value"}
        mock_make_request.return_value = self.success_response

        response = interface.update_submission_status(data, self.challenge_pk)

        mock_make_request.assert_called_with(url, "PATCH", data=data)
        self.assertEqual(response, self.success_response)

    @mock.patch("interface.make_request")
    def test_delete_message_from_sqs_queue(self, mock_make_request):
        test_receipt_handle = "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"
        data = {"receipt_handle": test_receipt_handle}
        url = "{}{}".format(evalai_api_server, self.delete_message_from_sqs_queue_url(queue_name))
        mock_make_request.return_value = 200

        response = interface.delete_message_from_sqs_queue()

        mock_make_request.assert_called_with(url, "POST", data=data, return_status_code=True)
        self.assertEqual(response, 200)
