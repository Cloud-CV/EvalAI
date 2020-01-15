import random
import requests
import responses
import string

from unittest import mock
from unittest import TestCase

from scripts.workers.worker_util import EvalAI_Interface


AUTH_TOKEN = "".join(random.choice(string.ascii_lowercase) for _ in range(40))
EVALAI_API_SERVER = "https://evalapi.cloudcv.org"
EVALAI_QUEUE_NAME = "evalai_submission_queue"


class BaseTestClass(TestCase):
    def setUp(self):
        # Keeping all values different so that it is recognized if one of them is confused with the other
        self.challenge_pk = 1
        self.challenge_phase_pk = 2
        self.submission_pk = 3

        self.interface = EvalAI_Interface(AUTH_TOKEN, EVALAI_API_SERVER, EVALAI_QUEUE_NAME)
        self.success_response = {"success": "success_message", "status_code": 200}
        self.example_error_description = "Example description"

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


class MakeRequestTestClass(BaseTestClass):

    @responses.activate
    def test_make_request_get_success(self):
        url = "{0}{1}".format(EVALAI_API_SERVER, self.make_request_url())
        responses.add(responses.GET, url,
                      json=self.success_response,
                      content_type='application/json',
                      status=200)

        response = self.interface.make_request(url, "GET")

        self.assertEqual(response, self.success_response)

    @responses.activate
    @mock.patch("scripts.workers.worker_util.logger.info")
    def test_make_request_http_error(self, mock_logger):
        url = "{0}{1}".format(EVALAI_API_SERVER, self.make_request_url())
        responses.add(responses.GET, url,
                      json={"error": "404 Not Found"},
                      status=404)

        with self.assertRaises(requests.exceptions.HTTPError):
            self.interface.make_request(url, "GET")

        mock_logger.assert_called_with("The worker is not able to establish connection with EvalAI")

    @responses.activate
    @mock.patch("scripts.workers.worker_util.logger.info")
    def test_make_request_connection_error(self, mock_logger):
        url = "{0}{1}".format(EVALAI_API_SERVER, self.make_request_url())
        responses.add(responses.GET, url,
                      body=requests.exceptions.RequestException(self.example_error_description))

        with self.assertRaises(requests.exceptions.RequestException):
            self.interface.make_request(url, "GET")

        mock_logger.assert_called_with("The worker is not able to establish connection with EvalAI")


class WorkerUtilTestClass(BaseTestClass):

    def setUp(self):
        super(WorkerUtilTestClass, self).setUp()

        self.patcher = mock.patch(
            "scripts.workers.worker_util.EvalAI_Interface.make_request", return_value=self.success_response,
        )
        self.mock_make_request = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_return_url_per_environment(self):
        returned_url = self.interface.return_url_per_environment(self.make_request_url())
        expected = "{0}{1}".format(EVALAI_API_SERVER, self.make_request_url())
        self.assertEqual(returned_url, expected)

    def test_get_message_from_sqs_queue(self):
        url = "{}{}".format(EVALAI_API_SERVER, self.get_message_from_sqs_queue_url(EVALAI_QUEUE_NAME))
        response = self.interface.get_message_from_sqs_queue()

        self.mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    def test_get_submission_by_pk(self):
        url = "{}{}".format(EVALAI_API_SERVER, self.get_submission_by_pk_url(self.submission_pk))
        response = self.interface.get_submission_by_pk(self.submission_pk)

        self.mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    def test_get_challenge_phases_by_challenge_pk(self):
        url = "{}{}".format(EVALAI_API_SERVER, self.get_challenge_phases_by_challenge_pk_url(self.challenge_pk))
        response = self.interface.get_challenge_phases_by_challenge_pk(self.challenge_pk)

        self.mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    def test_get_challenge_by_queue_name(self):
        url = "{}{}".format(EVALAI_API_SERVER, self.get_challenge_by_queue_name_url(EVALAI_QUEUE_NAME))
        response = self.interface.get_challenge_by_queue_name()

        self.mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    def test_get_challenge_phase_by_pk(self):
        url = "{}{}".format(EVALAI_API_SERVER, self.get_challenge_phase_by_pk_url(self.challenge_pk, self.challenge_phase_pk))
        response = self.interface.get_challenge_phase_by_pk(self.challenge_pk, self.challenge_phase_pk)

        self.mock_make_request.assert_called_with(url, "GET")
        self.assertEqual(response, self.success_response)

    def test_update_submission_data(self):
        url = "{}{}".format(EVALAI_API_SERVER, self.update_submission_data_url(self.challenge_pk))
        data = {"submission_pk": self.submission_pk, "test_field": "new_value"}
        response = self.interface.update_submission_data(data, self.challenge_pk, self.submission_pk)

        self.mock_make_request.assert_called_with(url, "PUT", data=data)
        self.assertEqual(response, self.success_response)

    def test_update_submission_data_partially(self):
        url = "{}{}".format(EVALAI_API_SERVER, self.update_submission_status_url(self.challenge_pk))
        data = {"test_field": "new_value"}
        response = self.interface.update_submission_status(data, self.challenge_pk)

        self.mock_make_request.assert_called_with(url, "PATCH", data=data)
        self.assertEqual(response, self.success_response)

    def test_delete_message_from_sqs_queue(self):
        test_receipt_handle = "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"
        data = {"receipt_handle": test_receipt_handle}
        url = "{}{}".format(EVALAI_API_SERVER, self.delete_message_from_sqs_queue_url(EVALAI_QUEUE_NAME))
        response = self.interface.delete_message_from_sqs_queue(test_receipt_handle)

        self.mock_make_request.assert_called_with(url, "POST", data)
        self.assertEqual(response, self.success_response)
