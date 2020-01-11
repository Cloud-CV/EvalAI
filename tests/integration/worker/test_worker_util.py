import mock
import responses
import requests

# from rest_framework import status
from rest_framework.test import APITestCase

from scripts.workers.worker_util import EvalAI_Interface


AUTH_TOKEN = "mock_auth_token123456"
EVALAI_API_SERVER = "http://testserver.com"
QUEUE_NAME = "evalai_submissions_queue"


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.evalai_interface = EvalAI_Interface(AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME)
        self.test_url = "/test-url"
        self.data = {"test": "data"}


class TestGetRequestHeaders(BaseAPITestClass):
    def setUp(self):
        super(TestGetRequestHeaders, self).setUp()

    def test_get_request_headers(self):
        expected = {"Authorization": "Token {}".format(AUTH_TOKEN)}
        result = self.evalai_interface.get_request_headers()
        self.assertEqual(expected, result)


@mock.patch("scripts.workers.remote_submission_worker.requests")
class TestMakeRequest(BaseAPITestClass):
    def setUp(self):
        super(TestMakeRequest, self).setUp()
        self.url = super(TestMakeRequest, self).test_url

    def test_make_request_get(self, mock_make_request):
        self.evalai_interface.make_request(self.url, "GET")
        mock_make_request.get.assert_called_with(url=self.url, method="GET")

    def test_make_request_put(self, mock_make_request):
        self.evalai_interface.make_request(self.url, "PUT", data=self.data)
        mock_make_request.put.assert_called_with(url=self.url, method="PUT", data=self.data)

    def test_make_request_patch(self, mock_make_request):
        self.evalai_interface.make_request(self.url, "PATCH", data=self.data)
        mock_make_request.patch.assert_called_with(url=self.url, method="PATCH", data=self.data)

    def test_make_request_post(self, mock_make_request):
        self.evalai_interface.make_request(self.url, "POST", data=self.data)
        mock_make_request.post.assert_called_with(url=self.url, method="POSTs", data=self.data)


class TestReturnUrlPerEnvironment(BaseAPITestClass):
    def setUp(self):
        super(TestReturnUrlPerEnvironment, self).setUp()

    def test_return_url_per_environment(self):
        expected = "{0}{1}".format(EVALAI_API_SERVER, self.test_url)
        result = self.evalai_interface.return_url_per_environment(self.test_url)
        self.assertEqual(expected, result)


# class TestDeleteMessageFromSQS(BaseAPITestClass):
#     def setUp(self):
#         super(TestDeleteMessageFromSQS, self).setUp()

#         url = "{}{}"
#         responses.add(
#             responses.POST,
#             url.format(
#                 EVALAI_API_SERVER,
#                 URLS.get("delete_message_from_sqs_queue").format(QUEUE_NAME)
#             ),
#             status=200
#         )

#     @responses.activate
#     def test_delete_message_from_sqs_queue(self):
#         receipt_handle = "test-receipt-handle"
#         response = self.evalai_interface.delete_message_from_sqs_queue(receipt_handle)
#         self.assertEqual(response.status_code, status.HTTP_200_OK)
