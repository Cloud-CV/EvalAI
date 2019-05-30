import mock

import scripts.workers.remote_submission_worker as remote_submission_worker

from unittest import TestCase


class BaseTestClass(TestCase):

    def setUp(self):
        self.dict = {"AUTH_TOKEN": "test_token", "DJANGO_SERVER": "testserver", "DJANGO_SERVER_PORT": "80", "QUEUE_NAME": "evalai_submission_queue"}
        self.DJANGO_SERVER = "testerver"

    @mock.patch("scripts.workers.remote_submission_worker.requests")
    def test_make_request_get(self, mock_make_request):
        url = "/test/url"
        headers = {"Authorization": "Token test_token"}
        with mock.patch.dict('scripts.workers.remote_submission_worker.os.environ', self.dict):
            remote_submission_worker.make_request(url, "GET")
            mock_make_request.get.assert_called_with(url=url, headers=headers)

    @mock.patch("scripts.workers.remote_submission_worker.requests")
    def test_make_request_put(self, mock_make_request):
        url = "/test/url"
        headers = {"Authorization": "Token test_token"}
        data = {"test": "data"}
        with mock.patch.dict('scripts.workers.remote_submission_worker.os.environ', self.dict):
            remote_submission_worker.make_request(url, "PUT", data=data)
            mock_make_request.put.assert_called_with(url=url, headers=headers, data=data)

    @mock.patch("scripts.workers.remote_submission_worker.requests")
    def test_make_request_patch(self, mock_make_request):
        url = "/test/url"
        headers = {"Authorization": "Token test_token"}
        data = {"test": "data"}
        with mock.patch.dict('scripts.workers.remote_submission_worker.os.environ', self.dict):
            remote_submission_worker.make_request(url, "PATCH", data=data)
            mock_make_request.patch.assert_called_with(url=url, headers=headers, data=data)

    @mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
    @mock.patch("scripts.workers.remote_submission_worker.make_request")
    def test_get_message_from_sqs_queue(self, mock_make_request, mock_url):
        url = "/api/jobs/challenge/queues/evalai_submission_queue/"
        with mock.patch.dict('scripts.workers.remote_submission_worker.os.environ', self.dict):
            remote_submission_worker.get_message_from_sqs_queue()
            mock_url.assert_called_with(url)
            url = mock_url(url)
            mock_make_request.assert_called_with(url, "GET")

    @mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
    @mock.patch("scripts.workers.remote_submission_worker.make_request")
    def test_delete_message_from_sqs_queue(self, mock_make_request, mock_url):
        test_receipt_handle = "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"
        with mock.patch.dict('os.environ', self.dict):
            remote_submission_worker.delete_message_from_sqs_queue(test_receipt_handle)
            url = "/api/jobs/queues/evalai_submission_queue/receipt/{}/".format(test_receipt_handle)
            mock_url.assert_called_with(url)
            url = mock_url(url)
            mock_make_request.assert_called_with(url, "GET")

    @mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
    @mock.patch("scripts.workers.remote_submission_worker.make_request")
    def test_get_submission_by_pk(self, mock_make_request, mock_url):
        submission_pk = 1
        remote_submission_worker.get_submission_by_pk(submission_pk)
        url = "/api/jobs/submission/{}".format(submission_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    @mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
    @mock.patch("scripts.workers.remote_submission_worker.make_request")
    def test_get_challenge_phases_by_challenge_pk(self, mock_make_request, mock_url):
        challenge_pk = 1
        remote_submission_worker.get_challenge_phases_by_challenge_pk(challenge_pk)
        url = "/api/challenges/{}/phases/".format(challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    @mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
    @mock.patch("scripts.workers.remote_submission_worker.make_request")
    def test_get_challenge_by_queue_name(self, mock_make_request, mock_url):
        url = "/api/challenges/challenge/queues/evalai_submission_queue/"
        with mock.patch.dict('scripts.workers.remote_submission_worker.os.environ', self.dict):
            remote_submission_worker.get_challenge_by_queue_name()
            mock_url.assert_called_with(url)
            url = mock_url(url)
            mock_make_request.assert_called_with(url, "GET")

    @mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
    @mock.patch("scripts.workers.remote_submission_worker.make_request")
    def test_get_challenge_phase_by_pk(self, mock_make_request, mock_url):
        challenge_pk = 1
        challenge_phase_pk = 1
        remote_submission_worker.get_challenge_phase_by_pk(challenge_pk, challenge_phase_pk)
        url = "/api/challenges/challenge/{}/challenge_phase/{}".format(challenge_pk, challenge_phase_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    @mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
    @mock.patch("scripts.workers.remote_submission_worker.make_request")
    def test_update_submission_data(self, mock_make_request, mock_url):
        challenge_pk = 1
        submission_pk = 1
        data = {"test": "data"}
        remote_submission_worker.update_submission_data(data, challenge_pk, submission_pk)
        url = "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PUT", data=data)

    @mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
    @mock.patch("scripts.workers.remote_submission_worker.make_request")
    def test_update_submission_status(self, mock_make_request, mock_url):
        challenge_pk = 1
        data = data = {"test": "data"}
        remote_submission_worker.update_submission_status(data, challenge_pk)
        url = "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PATCH", data=data)

    def test_return_url_per_environment(self):
        url = "/test/url"
        expected_url = "http://testserver:80{}".format(url)
        with mock.patch.dict('scripts.workers.remote_submission_worker.os.environ', self.dict):
            returned_url = remote_submission_worker.return_url_per_environment(url)
            self.assertEqual(returned_url, expected_url)
