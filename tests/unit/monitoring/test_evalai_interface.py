import unittest
from unittest.mock import MagicMock, patch

import requests

from scripts.monitoring.evalai_interface import URLS, EvalAI_Interface


class TestEvalAIInterface(unittest.TestCase):
    def setUp(self):
        self.AUTH_TOKEN = "dummy_token"
        self.EVALAI_API_SERVER = "http://dummy.api.server"
        self.api = EvalAI_Interface(self.AUTH_TOKEN, self.EVALAI_API_SERVER)

    def test_get_request_headers_default(self):
        headers = self.api.get_request_headers()
        self.assertEqual(headers, {"Authorization": "Bearer dummy_token"})

    def test_get_request_headers_with_json_content(self):
        headers = self.api.get_request_headers(include_json_content=True)
        self.assertEqual(
            headers,
            {
                "Authorization": "Bearer dummy_token",
                "Content-Type": "application/json",
            },
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_make_request_success(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response

        url = "http://example.com"
        response = self.api.make_request(url, "GET")

        self.assertEqual(response, {"key": "value"})
        mock_request.assert_called_once_with(
            method="GET",
            url=url,
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_make_request_with_json_content_header(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "value"}
        mock_request.return_value = mock_response

        url = "http://example.com"
        data = '{"foo": "bar"}'
        response = self.api.make_request(
            url, "POST", data=data, include_json_content=True
        )

        self.assertEqual(response, {"key": "value"})
        mock_request.assert_called_once_with(
            method="POST",
            url=url,
            headers=self.api.get_request_headers(include_json_content=True),
            data=data,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_make_request_failure(self, mock_request):
        mock_request.side_effect = requests.exceptions.RequestException

        with self.assertRaises(requests.exceptions.RequestException):
            self.api.make_request("http://example.com", "GET")

    def test_return_url_per_environment(self):
        url = "/api/test"
        full_url = self.api.return_url_per_environment(url)
        self.assertEqual(full_url, "http://dummy.api.server/api/test")

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_get_message_from_sqs_queue(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"message": "test"}
        mock_request.return_value = mock_response

        response = self.api.get_message_from_sqs_queue("test_queue")
        self.assertEqual(response, {"message": "test"})
        url = "/api/jobs/challenge/queues/test_queue/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_delete_message_from_sqs_queue(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        receipt_handle = "handle123"
        response = self.api.delete_message_from_sqs_queue(
            receipt_handle, "test_queue"
        )
        self.assertEqual(response, {"result": "success"})
        url = "/api/jobs/queues/test_queue/"
        mock_request.assert_called_once_with(
            method="POST",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data={"receipt_handle": receipt_handle},
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
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

    @patch("scripts.monitoring.evalai_interface.requests.request")
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

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_get_challenge_by_queue_name(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"challenge": "data"}
        mock_request.return_value = mock_response

        response = self.api.get_challenge_by_queue_name("test_queue")
        self.assertEqual(response, {"challenge": "data"})
        url = "/api/challenges/challenge/queues/test_queue/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
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

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_update_submission_data(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "success"}
        mock_request.return_value = mock_response

        data = {"submission": "data"}
        response = self.api.update_submission_data(data, 1)
        self.assertEqual(response, {"result": "success"})
        url = "/api/jobs/challenge/1/update_submission/"
        mock_request.assert_called_once_with(
            method="PUT",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=data,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
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

    @patch("scripts.monitoring.evalai_interface.requests.request")
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

    @patch("scripts.monitoring.evalai_interface.requests.request")
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

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_get_challenge_by_pk(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"challenge": "details"}
        mock_request.return_value = mock_response

        response = self.api.get_challenge_by_pk(1)
        self.assertEqual(response, {"challenge": "details"})
        url = "/api/challenges/challenge/1/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_get_challenges(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"challenges": []}
        mock_request.return_value = mock_response

        response = self.api.get_challenges()
        self.assertEqual(response, {"challenges": []})
        url = "/api/challenges/challenge/all/all/all"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_get_submissions_for_challenge(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"submissions": []}
        mock_request.return_value = mock_response

        response = self.api.get_submissions_for_challenge(1)
        self.assertEqual(response, {"submissions": []})
        url = "/api/jobs/challenge/1/submission/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_get_submissions_for_challenge_with_status(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"submissions": []}
        mock_request.return_value = mock_response

        response = self.api.get_submissions_for_challenge(1, status="finished")
        self.assertEqual(response, {"submissions": []})
        url = "/api/jobs/challenge/1/submission/"
        expected_url = (
            self.api.return_url_per_environment(url) + "?status=finished"
        )
        mock_request.assert_called_once_with(
            method="GET",
            url=expected_url,
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_get_challenges_submission_metrics(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"metrics": []}
        mock_request.return_value = mock_response

        response = self.api.get_challenges_submission_metrics()
        self.assertEqual(response, {"metrics": []})
        url = "/api/challenges/challenge/get_submission_metrics"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_get_challenge_submission_metrics_by_pk(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"metrics": "data"}
        mock_request.return_value = mock_response

        response = self.api.get_challenge_submission_metrics_by_pk(1)
        self.assertEqual(response, {"metrics": "data"})
        url = "/api/challenges/challenge/get_submission_metrics_by_pk/1/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_get_ec2_instance_details(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"instance": "details"}
        mock_request.return_value = mock_response

        response = self.api.get_ec2_instance_details(1)
        self.assertEqual(response, {"instance": "details"})
        url = "/api/challenges/1/get_ec2_instance_details/"
        mock_request.assert_called_once_with(
            method="GET",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_start_challenge_ec2_instance(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "started"}
        mock_request.return_value = mock_response

        response = self.api.start_challenge_ec2_instance(1)
        self.assertEqual(response, {"status": "started"})
        url = "/api/challenges/1/manage_ec2_instance/start"
        mock_request.assert_called_once_with(
            method="PUT",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_stop_challenge_ec2_instance(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "stopped"}
        mock_request.return_value = mock_response

        response = self.api.stop_challenge_ec2_instance(1)
        self.assertEqual(response, {"status": "stopped"})
        url = "/api/challenges/1/manage_ec2_instance/stop"
        mock_request.assert_called_once_with(
            method="PUT",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(),
            data=None,
        )

    @patch("scripts.monitoring.evalai_interface.requests.request")
    def test_update_challenge_attributes(self, mock_request):
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": "updated"}
        mock_request.return_value = mock_response

        data = '{"challenge_pk": 1, "is_active": false}'
        response = self.api.update_challenge_attributes(data)
        self.assertEqual(response, {"result": "updated"})
        url = "/api/challenges/challenge/update_challenge_attributes/"
        mock_request.assert_called_once_with(
            method="POST",
            url=self.api.return_url_per_environment(url),
            headers=self.api.get_request_headers(include_json_content=True),
            data=data,
        )


class TestURLSDict(unittest.TestCase):
    def test_all_url_keys_exist(self):
        expected_keys = [
            "get_message_from_sqs_queue",
            "delete_message_from_sqs_queue",
            "get_submission_by_pk",
            "get_challenge_phases_by_challenge_pk",
            "get_challenge_by_queue_name",
            "get_challenge_phase_by_pk",
            "update_submission_data",
            "get_aws_eks_bearer_token",
            "get_aws_eks_cluster_details",
            "get_challenge_by_pk",
            "get_challenges",
            "get_submissions_for_challenge",
            "get_challenges_submission_metrics",
            "get_challenge_submission_metrics_by_pk",
            "manage_ec2_instance",
            "get_ec2_instance_details",
            "update_challenge_attributes",
        ]
        for key in expected_keys:
            self.assertIn(key, URLS)

    def test_update_challenge_attributes_url(self):
        self.assertEqual(
            URLS["update_challenge_attributes"],
            "/api/challenges/challenge/update_challenge_attributes/",
        )


if __name__ == "__main__":
    unittest.main()
