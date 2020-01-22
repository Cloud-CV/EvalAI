import mock
import requests
import responses

from scripts.workers.worker_utils import EvalAI_Interface, URLS
from unittest import TestCase


class BaseTestClass(TestCase):
    def setUp(self):
        self.AUTH_TOKEN = "test_token"
        self.EVALAI_API_SERVER = "http://testserver.com"
        self.QUEUE_NAME = "evalai_submission_queue"
        self.evalai_interface = EvalAI_Interface(self.AUTH_TOKEN, self.EVALAI_API_SERVER, self.QUEUE_NAME)

    def make_request_url(self):
        return "/test/url"

    def get_message_from_sqs_queue_url(self, queue_name):
        return URLS.get("get_message_from_sqs_queue").format(queue_name)

    def delete_message_from_sqs_queue_url(self, queue_name):
        return URLS.get("delete_message_from_sqs_queue").format(queue_name)

    def get_submission_by_pk_url(self, submission_pk):
        return URLS.get("get_submission_by_pk").format(submission_pk)

    def get_challenge_phases_by_challenge_pk_url(self, challenge_pk):
        return URLS.get("get_challenge_phases_by_challenge_pk").format(challenge_pk)

    def get_challenge_by_queue_name_url(self, queue_name):
        return URLS.get("get_challenge_by_queue_name").format(queue_name)

    def get_challenge_phase_by_pk_url(self, challenge_pk, challenge_phase_pk):
        return URLS.get("get_challenge_phase_by_pk").format(challenge_pk, challenge_phase_pk)

    def update_submission_data_url(self, challenge_pk):
        return URLS.get("update_submission_data").format(challenge_pk)

    def update_submission_status_url(self, challenge_pk):
        return "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)


class GetRequestHeadersTestClass(BaseTestClass):
    def setUp(self):
        super(GetRequestHeadersTestClass, self).setUp()
        self.headers = {"Authorization": "Token {}".format(self.AUTH_TOKEN)}

    def test_get_request_headers(self):
        expected = self.headers
        result = self.evalai_interface.get_request_headers()
        self.assertEqual(expected, result)


class ReturnURLPerEnvironment(BaseTestClass):
    def test_return_url_per_environment(self):
        expected = "{}{}".format(self.EVALAI_API_SERVER, self.make_request_url())
        result = self.evalai_interface.return_url_per_environment(self.make_request_url())
        self.assertEqual(expected, result)


class MakeRequestTestClass(BaseTestClass):
    def setUp(self):
        super(MakeRequestTestClass, self).setUp()
        self.url = self.evalai_interface.return_url_per_environment(self.make_request_url())

    @responses.activate
    def test_make_request_success(self):
        expected = {"message": "test"}
        responses.add(
            responses.GET,
            self.url,
            json=expected,
            status=200,
        )

        response = self.evalai_interface.make_request(self.url, "GET")
        self.assertEqual(expected, response)

    @responses.activate
    @mock.patch("scripts.workers.worker_utils.logger.info")
    def test_make_request_when_url_is_invalid(self, mock_logger):
        invalid_url = "invalid-url"
        responses.add(
            responses.GET,
            invalid_url,
        )

        with self.assertRaises(requests.exceptions.MissingSchema):
            self.evalai_interface.make_request(invalid_url, "GET")

        mock_logger.assert_called_with("The worker is not able to establish connection with EvalAI")


@mock.patch("scripts.workers.worker_utils.EvalAI_Interface.make_request")
class APICallsTestClass(BaseTestClass):
    def setUp(self):
        super(APICallsTestClass, self).setUp()
        self.challenge_pk = 1
        self.challenge_phase_pk = 1
        self.submission_pk = 1

    def test_get_message_from_sqs_queue(self, mock_make_request):
        expected_url = self.evalai_interface.return_url_per_environment(
            self.get_message_from_sqs_queue_url(self.QUEUE_NAME)
        )

        self.evalai_interface.get_message_from_sqs_queue()
        mock_make_request.assert_called_with(expected_url, "GET")

    def test_delete_message_from_sqs_queue(self, mock_make_request):
        expected_url = self.evalai_interface.return_url_per_environment(
            self.delete_message_from_sqs_queue_url(self.QUEUE_NAME)
        )
        expected_receipt_handle = "test"
        expected_data = {"receipt_handle": expected_receipt_handle}

        self.evalai_interface.delete_message_from_sqs_queue(expected_receipt_handle)
        mock_make_request.assert_called_with(expected_url, "POST", expected_data)

    def test_get_submission_by_pk(self, mock_make_request):
        expected_url = self.evalai_interface.return_url_per_environment(
            self.get_submission_by_pk_url(self.submission_pk)
        )

        self.evalai_interface.get_submission_by_pk(self.submission_pk)
        mock_make_request.assert_called_with(expected_url, "GET")

    def test_get_challenge_phases_by_challenge_pk(self, mock_make_request):
        expected_url = self.evalai_interface.return_url_per_environment(
            self.get_challenge_phases_by_challenge_pk_url(self.challenge_pk)
        )

        self.evalai_interface.get_challenge_phases_by_challenge_pk(self.challenge_pk)
        mock_make_request.assert_called_with(expected_url, "GET")

    def test_get_challenge_by_queue_name(self, mock_make_request):
        expected_url = self.evalai_interface.return_url_per_environment(
            self.get_challenge_by_queue_name_url(self.QUEUE_NAME)
        )

        self.evalai_interface.get_challenge_by_queue_name()
        mock_make_request.assert_called_with(expected_url, "GET")

    def test_get_challenge_phase_by_pk(self, mock_make_request):
        expected_url = self.evalai_interface.return_url_per_environment(
            self.get_challenge_phase_by_pk_url(self.challenge_pk, self.challenge_phase_pk)
        )

        self.evalai_interface.get_challenge_phase_by_pk(self.challenge_pk, self.challenge_phase_pk)
        mock_make_request.assert_called_with(expected_url, "GET")

    def test_update_submission_data(self, mock_make_request):
        expected_url = self.evalai_interface.return_url_per_environment(
            self.update_submission_data_url(self.challenge_pk)
        )
        expected_data = {"test": "test"}

        self.evalai_interface.update_submission_data(expected_data, self.challenge_pk, self.submission_pk)
        mock_make_request.assert_called_with(expected_url, "PUT", data=expected_data)

    def test_update_submission_status(self, mock_make_request):
        expected_url = self.evalai_interface.return_url_per_environment(
            self.update_submission_status_url(self.challenge_pk)
        )
        expected_data = {"test": "test"}

        self.evalai_interface.update_submission_status(expected_data, self.challenge_pk)
        mock_make_request.assert_called_with(expected_url, "PATCH", data=expected_data)
