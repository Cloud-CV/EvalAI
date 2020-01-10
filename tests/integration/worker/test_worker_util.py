import mock
import responses
import requests

from rest_framework import status
from rest_framework.test import APITestCase

from scripts.workers.worker_util import EvalAI_Interface, URLS


AUTH_TOKEN = "mock_auth_token123456"
EVALAI_API_SERVER = "http://testserver"
QUEUE_NAME = "evalai_submissions_queue"


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.evalai_interface = EvalAI_Interface(AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME)
        self.test_url = "/test-url"


class TestGetRequestHeaders(BaseAPITestClass):
    def setUp(self):
        super(TestGetRequestHeaders, self).setUp()

    def test_get_request_headers(self):
        expected = {"Authorization": "Token {}".format(AUTH_TOKEN)}
        result = self.evalai_interface.get_request_headers()
        self.assertEqual(expected, result)


class TestMakeRequest(BaseAPITestClass):
    def setUp(self):
        super(TestMakeRequest, self).setUp()

        url = "{}{}"
        responses.add(
            responses.GET,
            url.format(EVALAI_API_SERVER, self.test_url),
            status=200
        )

        @responses.activate
        @mock.patch('scripts.workers.worker_util.get_request_headers')
        def test_make_request_success(self, mock_headers):
            mock_headers.return_value = {"Authorization": "Token {}".format(AUTH_TOKEN)}
            response = self.evalai_interface.make_request(self.test_url, "GET")
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        @mock.patch('scripts.workers.worker_util.logger.info')
        @mock.patch('scripts.workers.worker_util.get_request_headers')
        def test_make_request_with_request_exception(self, mock_headers, mock_logger):
            mock_headers.return_value = {"Authorization": "Token {}".format(AUTH_TOKEN)}
            with self.assertRaises(requests.exceptions.RequestException):
                self.evalai_interface.make_request(self.test_url, "GET")
                mock_logger.assert_called_with("The worker is not able to establish connection with EvalAI")


class TestReturnUrlPerEnvironment(BaseAPITestClass):
    def setUp(self):
        super(TestReturnUrlPerEnvironment, self).setUp()

    def test_return_url_per_environment(self):
        expected = "{0}{1}".format(EVALAI_API_SERVER, self.test_url)
        result = self.evalai_interface.return_url_per_environment(self.test_url)
        self.assertEqual(expected, result)


class TestDeleteMessageFromSQS(BaseAPITestClass):
    def setUp(self):
        super(TestDeleteMessageFromSQS, self).setUp()

        url = "{}{}"
        responses.add(
            responses.POST,
            url.format(
                EVALAI_API_SERVER,
                URLS.get("delete_message_from_sqs_queue").format(QUEUE_NAME)
            ),
            status=200
        )

    def test_delete_message_from_sqs_queue(self):
        receipt_handle = "test-receipt-handle"
        response = self.evalai_interface.delete_message_from_sqs_queue(receipt_handle)
        self.assertEqual(response, status.HTTP_200_OK)
