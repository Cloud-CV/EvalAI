import unittest
from unittest.mock import patch, MagicMock

import requests
from scripts.workers.worker_utils import EvalAI_Interface


class TestEvalAIInterface(unittest.TestCase):
    def setUp(self):
        self.AUTH_TOKEN = "dummy_token"
        self.EVALAI_API_SERVER = "http://dummy.api.server"
        self.QUEUE_NAME = "dummy_queue"
        self.api = EvalAI_Interface(
            self.AUTH_TOKEN, self.EVALAI_API_SERVER, self.QUEUE_NAME
        )

    @patch(
        "scripts.workers.worker_utils.requests.request"
    )  # Adjust the import path
    def test_get_request_headers(self, mock_request):
        headers = self.api.get_request_headers()
        self.assertEqual(headers, {"Authorization": "Bearer dummy_token"})

    @patch("scripts.workers.worker_utils.requests.request")
    def test_make_request_success(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response

        url = "http://example.com"
        method = "GET"
        response = self.api.make_request(url, method)

        self.assertEqual(response, {"key": "value"})
        mock_request.assert_called_once_with(
            method=method,
            url=url,
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_make_request_failure(self, mock_request):
        mock_request.side_effect = requests.exceptions.RequestException

        with self.assertRaises(requests.exceptions.RequestException):
            self.api.make_request("http://example.com", "GET")

    def test_return_url_per_environment(self):
        url = "/api/test"
        full_url = self.api.return_url_per_environment(url)
        self.assertEqual(full_url, "http://dummy.api.server/api/test")

    @patch("scripts.workers.worker_utils.requests.request")
    def test_get_message_from_sqs_queue(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": "test"}
        mock_request.return_value = mock_response

        response = self.api.get_message_from_sqs_queue()
        self.assertEqual(response, {"message": "test"})
        url = "/api/jobs/challenge/queues/dummy_queue/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_get_submission_by_pk(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"submission": "data"}
        mock_request.return_value = mock_response

        response = self.api.get_submission_by_pk(1)
        self.assertEqual(response, {"submission": "data"})
        url = "/api/jobs/submission/1"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_get_challenge_phases_by_challenge_pk(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"phases": "data"}
        mock_request.return_value = mock_response

        response = self.api.get_challenge_phases_by_challenge_pk(1)
        self.assertEqual(response, {"phases": "data"})
        url = "/api/challenges/1/phases/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_get_challenge_by_queue_name(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"challenge": "data"}
        mock_request.return_value = mock_response

        response = self.api.get_challenge_by_queue_name()
        self.assertEqual(response, {"challenge": "data"})
        url = "/api/challenges/challenge/queues/dummy_queue/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_get_challenge_phase_by_pk(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"phase": "data"}
        mock_request.return_value = mock_response

        response = self.api.get_challenge_phase_by_pk(1, 2)
        self.assertEqual(response, {"phase": "data"})
        url = "/api/challenges/challenge/1/challenge_phase/2"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_update_submission_data(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        data = {"submission": "data"}
        response = self.api.update_submission_data(data, 1, 2)
        self.assertEqual(response, {"result": "success"})
        url = "/api/jobs/challenge/1/update_submission/"
        mock_request.assert_called_once_with(
            method="PUT",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=data,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_update_submission_status(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        data = {"status": "finished"}
        response = self.api.update_submission_status(data, 1)
        self.assertEqual(response, {"result": "success"})
        url = "/api/jobs/challenge/1/update_submission/"
        mock_request.assert_called_once_with(
            method="PATCH",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=data,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_get_aws_eks_bearer_token(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"token": "token_data"}
        mock_request.return_value = mock_response

        response = self.api.get_aws_eks_bearer_token(1)
        self.assertEqual(response, {"token": "token_data"})
        url = "/api/jobs/challenge/1/eks_bearer_token/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_get_aws_eks_cluster_details(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"cluster": "details"}
        mock_request.return_value = mock_response

        response = self.api.get_aws_eks_cluster_details(1)
        self.assertEqual(response, {"cluster": "details"})
        url = "/api/challenges/1/evaluation_cluster/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.workers.worker_utils.requests.request")
    def test_delete_message_from_sqs_queue(self, mock_request):
        # Mock the response of the requests.request method
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        # Call the method to test
        receipt_handle = "handle123"
        response = self.api.delete_message_from_sqs_queue(receipt_handle)
        # Expected URL construction
        expected_url = "http://dummy.api.server/api/jobs/queues/dummy_queue/"

        # Expected data payload
        expected_data = {"receipt_handle": receipt_handle}

        # Assertions
        mock_request.assert_called_once_with(
            method="POST",
            url=expected_url,
            headers=self.api.get_request_headers(),
            data=expected_data,
        )
        self.assertEqual(response, {"result": "success"})
