import mock

from unittest import TestCase

from scripts.workers.remote_submission_worker import (
    make_request,
    get_message_from_sqs_queue,
    delete_message_from_sqs_queue,
    get_submission_by_pk,
    get_challenge_phases_by_challenge_pk,
    get_challenge_by_queue_name,
    get_challenge_phase_by_pk,
    update_submission_data,
    update_submission_status,
    return_url_per_environment,
)


class BaseTestClass(TestCase):
    def setUp(self):
        self.url = "/test/url"
        self.submission_pk = 1
        self.challenge_pk = 1
        self.challenge_phase_pk = 1
        self.data = {"test": "data"}
        self.headers = {"Authorization": "Token test_token"}


@mock.patch("scripts.workers.remote_submission_worker.AUTH_TOKEN", "test_token")
@mock.patch("scripts.workers.remote_submission_worker.requests")
class MakeRequestTestClass(BaseTestClass):

    def test_make_request_get(self, mock_make_request):
        make_request(self.url, "GET")
        mock_make_request.get.assert_called_with(url=self.url, headers=self.headers)

    def test_make_request_put(self, mock_make_request):
        make_request(self.url, "PUT", data=self.data)
        mock_make_request.put.assert_called_with(url=self.url, headers=self.headers, data=self.data)

    def test_make_request_patch(self, mock_make_request):
        make_request(self.url, "PATCH", data=self.data)
        mock_make_request.patch.assert_called_with(url=self.url, headers=self.headers, data=self.data)


@mock.patch("scripts.workers.remote_submission_worker.QUEUE_NAME", "evalai_submission_queue")
@mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
@mock.patch("scripts.workers.remote_submission_worker.make_request")
class APICallsTestClass(BaseTestClass):

    def test_get_message_from_sqs_queue(self, mock_make_request, mock_url):
        self.url = "/api/jobs/challenge/queues/evalai_submission_queue/"
        get_message_from_sqs_queue()
        mock_url.assert_called_with(self.url)
        self.url = mock_url(self.url)
        mock_make_request.assert_called_with(self.url, "GET")

    def test_delete_message_from_sqs_queue(self, mock_make_request, mock_url):
        test_receipt_handle = "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"
        delete_message_from_sqs_queue(test_receipt_handle)
        self.url = "/api/jobs/queues/evalai_submission_queue/receipt/{}/".format(test_receipt_handle)
        mock_url.assert_called_with(self.url)
        self.url = mock_url(self.url)
        mock_make_request.assert_called_with(self.url, "GET")

    def test_get_challenge_by_queue_name(self, mock_make_request, mock_url):
        self.url = "/api/challenges/challenge/queues/evalai_submission_queue/"
        get_challenge_by_queue_name()
        mock_url.assert_called_with(self.url)
        self.url = mock_url(self.url)
        mock_make_request.assert_called_with(self.url, "GET")

    def test_get_submission_by_pk(self, mock_make_request, mock_url):
        get_submission_by_pk(self.submission_pk)
        self.url = "/api/jobs/submission/{}".format(self.submission_pk)
        mock_url.assert_called_with(self.url)
        self.url = mock_url(self.url)
        mock_make_request.assert_called_with(self.url, "GET")

    def test_get_challenge_phases_by_challenge_pk(self, mock_make_request, mock_url):
        get_challenge_phases_by_challenge_pk(self.challenge_pk)
        self.url = "/api/challenges/{}/phases/".format(self.challenge_pk)
        mock_url.assert_called_with(self.url)
        self.url = mock_url(self.url)
        mock_make_request.assert_called_with(self.url, "GET")

    def test_get_challenge_phase_by_pk(self, mock_make_request, mock_url):
        get_challenge_phase_by_pk(self.challenge_pk, self.challenge_phase_pk)
        self.url = "/api/challenges/challenge/{}/challenge_phase/{}".format(self.challenge_pk, self.challenge_phase_pk)
        mock_url.assert_called_with(self.url)
        self.url = mock_url(self.url)
        mock_make_request.assert_called_with(self.url, "GET")

    def test_update_submission_data(self, mock_make_request, mock_url):
        update_submission_data(self.data, self.challenge_pk, self.submission_pk)
        self.url = "/api/jobs/challenge/{}/update_submission/".format(self.challenge_pk)
        mock_url.assert_called_with(self.url)
        self.url = mock_url(self.url)
        mock_make_request.assert_called_with(self.url, "PUT", data=self.data)

    def test_update_submission_status(self, mock_make_request, mock_url):
        update_submission_status(self.data, self.challenge_pk)
        self.url = "/api/jobs/challenge/{}/update_submission/".format(self.challenge_pk)
        mock_url.assert_called_with(self.url)
        self.url = mock_url(self.url)
        mock_make_request.assert_called_with(self.url, "PATCH", data=self.data)


@mock.patch("scripts.workers.remote_submission_worker.DJANGO_SERVER_PORT", "80")
@mock.patch("scripts.workers.remote_submission_worker.DJANGO_SERVER", "testserver")
class URLFormatTestCase(BaseTestClass):

    def test_return_url_per_environment(self):
        expected_url = "http://testserver:80{}".format(self.url)
        returned_url = return_url_per_environment(self.url)
        self.assertEqual(returned_url, expected_url)
