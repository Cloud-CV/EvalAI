import mock

from rest_framework.test import APITestCase
from scripts.workers.worker_util import EvalAI_Interface, URLS


AUTH_TOKEN = "mock_auth_token123456"
EVALAI_API_SERVER = "http://testserver.com"
QUEUE_NAME = "evalai_submissions_queue"


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.evalai_interface = EvalAI_Interface(AUTH_TOKEN, EVALAI_API_SERVER, QUEUE_NAME)
        self.test_url = "/test-url"
        self.data = {"test": "data"}
        self.url_per_environment = "{0}{1}".format(EVALAI_API_SERVER, self.test_url)


class TestGetRequestHeaders(BaseAPITestClass):
    def setUp(self):
        super(TestGetRequestHeaders, self).setUp()

    def test_get_request_headers(self):
        expected = {"Authorization": "Token {}".format(AUTH_TOKEN)}
        result = self.evalai_interface.get_request_headers()
        self.assertEqual(expected, result)


@mock.patch("scripts.workers.worker_util.requests")
class TestMakeRequest(BaseAPITestClass):
    def setUp(self):
        super(TestMakeRequest, self).setUp()
        self.url = self.test_url

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
        expected = self.url_per_environment
        result = self.evalai_interface.return_url_per_environment(self.test_url)
        self.assertEqual(expected, result)

@mock.patch("scripts.workers.worker_util.return_url_per_environment")
@mock.patch("scripts.workers.worker_util.make_request")
class APICallsTestClass(BaseTestClass):

    def test_get_message_from_sqs_queue(self, mock_make_request, mock_url):
        url = URLS.get("get_message_from_sqs_queue").format(QUEUE_NAME)
        self.evalai_interface.get_message_from_sqs_queue()
        mock_url.assert_called_with(self.test_url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_delete_message_from_sqs_queue(self, mock_make_request, mock_url):
        test_receipt_handle = "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"
        url = URLS.get("delete_message_from_sqs_queue").format(QUEUE_NAME)
        delete_message_from_sqs_queue(test_receipt_handle)
        mock_url.assert_called_with(self.test_url)
        url = mock_url(self.test_url)
        expected_data = {"receipt_handle": "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"}
        mock_make_request.assert_called_with(url, "POST", data=expected_data)

    def test_get_challenge_by_queue_name(self, mock_make_request, mock_url):
        url = URLS.get("get_challenge_by_queue_name").format(QUEUE_NAME)
        self.evalai_interface.get_challenge_by_queue_name()
        mock_url.assert_called_with(self.test_url)
        url = mock_url(self.test_url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_submission_by_pk(self, mock_make_request, mock_url):
        self.evalai_interface.get_submission_by_pk(self.submission_pk)
        url = URLS.get("get_submission_by_pk").format(self.submission.pk)
        mock_url.assert_called_with(self.test_url)
        url = mock_url(self.test_url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phases_by_challenge_pk(self, mock_make_request, mock_url):
        self.evalai_interface.get_challenge_phases_by_challenge_pk(self.challenge_pk)
        url = URLS.get("get_challenge_phases_by_challenge_pk").format(self.challenge.pk)
        mock_url.assert_called_with(self.test_url)
        url = mock_url(self.test_url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phase_by_pk(self, mock_make_request, mock_url):
        self.evalai_interface.get_challenge_phase_by_pk(self.challenge_pk, self.challenge_phase_pk)
        url = self.URLS.get("get_challenge_phase_by_pk").format(self.challenge_pk, self.challenge_phase_pk)
        mock_url.assert_called_with(self.test_url)
        url = mock_url(self.test_url)
        mock_make_request.assert_called_with(url, "GET")

    def test_update_submission_data(self, mock_make_request, mock_url):
        self.evalai_interface.update_submission_data(self.data, self.challenge_pk, self.submission_pk)
        url = self.URLS.get("update_submission_data").format(self.challenge_pk)
        mock_url.assert_called_with(self.test_url)
        url = mock_url(self.test_url)
        mock_make_request.assert_called_with(url, "PUT", data=self.data)

    def test_update_submission_status(self, mock_make_request, mock_url):
        self.evalai_interface.update_submission_status(self.data, self.challenge_pk)
        url = URLS.get("update_submission_status").format(challenge_pk)
        mock_url.assert_called_with(self.test_url)
        url = mock_url(self.test_url)
        mock_make_request.assert_called_with(url, "PATCH", data=self.data)
