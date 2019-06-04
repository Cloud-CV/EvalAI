import mock

# import scripts.workers.remote_submission_worker as remote_submission_worker

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


@mock.patch("scripts.workers.remote_submission_worker.AUTH_TOKEN", "test_token")
@mock.patch("scripts.workers.remote_submission_worker.requests")
class MakeRequestTestClass(TestCase):

    def test_make_request_get(self, mock_make_request):
        url = "/test/url"
        headers = {"Authorization": "Token test_token"}
        make_request(url, "GET")
        mock_make_request.get.assert_called_with(url=url, headers=headers)

    def test_make_request_put(self, mock_make_request):
        url = "/test/url"
        headers = {"Authorization": "Token test_token"}
        data = {"test": "data"}
        make_request(url, "PUT", data=data)
        mock_make_request.put.assert_called_with(url=url, headers=headers, data=data)

    def test_make_request_patch(self, mock_make_request):
        url = "/test/url"
        headers = {"Authorization": "Token test_token"}
        data = {"test": "data"}
        make_request(url, "PATCH", data=data)
        mock_make_request.patch.assert_called_with(url=url, headers=headers, data=data)


@mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
@mock.patch("scripts.workers.remote_submission_worker.make_request")
class APICallsTestClass(TestCase):

    @mock.patch("scripts.workers.remote_submission_worker.QUEUE_NAME", "evalai_submission_queue")
    def test_get_message_from_sqs_queue(self, mock_make_request, mock_url):
        url = "/api/jobs/challenge/queues/evalai_submission_queue/"
        get_message_from_sqs_queue()
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    @mock.patch("scripts.workers.remote_submission_worker.QUEUE_NAME", "evalai_submission_queue")
    def test_delete_message_from_sqs_queue(self, mock_make_request, mock_url):
        test_receipt_handle = "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"
        delete_message_from_sqs_queue(test_receipt_handle)
        url = "/api/jobs/queues/evalai_submission_queue/receipt/{}/".format(test_receipt_handle)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    @mock.patch("scripts.workers.remote_submission_worker.QUEUE_NAME", "evalai_submission_queue")
    def test_get_challenge_by_queue_name(self, mock_make_request, mock_url):
        url = "/api/challenges/challenge/queues/evalai_submission_queue/"
        get_challenge_by_queue_name()
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_submission_by_pk(self, mock_make_request, mock_url):
        submission_pk = 1
        get_submission_by_pk(submission_pk)
        url = "/api/jobs/submission/{}".format(submission_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phases_by_challenge_pk(self, mock_make_request, mock_url):
        challenge_pk = 1
        get_challenge_phases_by_challenge_pk(challenge_pk)
        url = "/api/challenges/{}/phases/".format(challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phase_by_pk(self, mock_make_request, mock_url):
        challenge_pk = 1
        challenge_phase_pk = 1
        get_challenge_phase_by_pk(challenge_pk, challenge_phase_pk)
        url = "/api/challenges/challenge/{}/challenge_phase/{}".format(challenge_pk, challenge_phase_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_update_submission_data(self, mock_make_request, mock_url):
        challenge_pk = 1
        submission_pk = 1
        data = {"test": "data"}
        update_submission_data(data, challenge_pk, submission_pk)
        url = "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PUT", data=data)

    def test_update_submission_status(self, mock_make_request, mock_url):
        challenge_pk = 1
        data = data = {"test": "data"}
        update_submission_status(data, challenge_pk)
        url = "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PATCH", data=data)


class URLFormatTestCase(TestCase):

    @mock.patch("scripts.workers.remote_submission_worker.DJANGO_SERVER_PORT", "80")
    @mock.patch("scripts.workers.remote_submission_worker.DJANGO_SERVER", "testserver")
    def test_return_url_per_environment(self):
        url = "/test/url"
        expected_url = "http://testserver:80{}".format(url)
        returned_url = return_url_per_environment(url)
        self.assertEqual(returned_url, expected_url)
