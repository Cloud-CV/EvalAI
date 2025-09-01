from unittest.mock import MagicMock, patch

from challenges.admin import ChallengeAdmin
from challenges.models import Challenge
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage
from django.test import RequestFactory, TestCase


class TestChallengeAdminActions(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.site = AdminSite()
        self.admin = ChallengeAdmin(Challenge, self.site)
        self.request = self.factory.get("/")

        self.request.session = self.client.session

        self.request._messages = FallbackStorage(self.request)

        self.queryset = MagicMock()
        self.queryset.count.return_value = 2

    @patch("challenges.admin.start_workers")
    def test_start_selected_workers_all_success(self, mock_start_workers):
        mock_start_workers.return_value = {"count": 2, "failures": []}
        self.admin.start_selected_workers(self.request, self.queryset)

        messages = list(self.request._messages)
        assert any("successfully started" in str(m) for m in messages)

    @patch("challenges.admin.start_workers")
    def test_start_selected_workers_partial_failure(self, mock_start_workers):
        mock_start_workers.return_value = {
            "count": 1,
            "failures": [{"challenge_pk": 1, "message": "Failed to start"}],
        }
        self.admin.start_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)
        assert any("succesfully started" in str(m) for m in messages)
        assert any("Challenge 1: Failed to start" in str(m) for m in messages)

    @patch("challenges.admin.stop_workers")
    def test_stop_selected_workers(self, mock_stop_workers):
        mock_stop_workers.return_value = {"count": 2, "failures": []}
        self.admin.stop_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)
        assert any("successfully stopped" in str(m) for m in messages)

    @patch("challenges.admin.scale_workers")
    def test_scale_selected_workers_valid(self, mock_scale_workers):
        mock_scale_workers.return_value = {"count": 2, "failures": []}
        self.request.POST = {"num_of_tasks": "2"}
        self.admin.scale_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)
        assert any("successfully scaled" in str(m) for m in messages)

    @patch("challenges.admin.scale_workers")
    def test_scale_selected_workers_invalid(self, mock_scale_workers):
        self.request.POST = {"num_of_tasks": "-1"}
        self.admin.scale_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)
        assert any(
            "Please enter a valid whole number" in str(m) for m in messages
        )

    @patch("challenges.admin.restart_workers")
    def test_restart_selected_workers(self, mock_restart_workers):
        mock_restart_workers.return_value = {"count": 2, "failures": []}
        self.admin.restart_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)
        assert any("successfully restarted" in str(m) for m in messages)

    @patch("challenges.admin.delete_workers")
    def test_delete_selected_workers(self, mock_delete_workers):
        mock_delete_workers.return_value = {"count": 2, "failures": []}
        self.admin.delete_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)
        assert any("successfully deleted" in str(m) for m in messages)

    @patch("challenges.admin.stop_workers")
    def test_stop_selected_workers_partial_failure(self, mock_stop_workers):
        mock_stop_workers.return_value = {
            "count": 1,
            "failures": [{"challenge_pk": 42, "message": "Failed to stop"}],
        }
        self.admin.stop_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)

        assert any("succesfully stopped" in str(m) for m in messages)

        assert any("Challenge 42: Failed to stop" in str(m) for m in messages)

    @patch("challenges.admin.scale_workers")
    def test_scale_selected_workers_partial_failure(self, mock_scale_workers):
        mock_scale_workers.return_value = {
            "count": 1,
            "failures": [{"challenge_pk": 99, "message": "Failed to scale"}],
        }
        self.request.POST = {"num_of_tasks": "2"}
        self.admin.scale_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)

        assert any("succesfully scaled" in str(m) for m in messages)

        assert any("Challenge 99: Failed to scale" in str(m) for m in messages)

    @patch("challenges.admin.restart_workers")
    def test_restart_selected_workers_partial_failure(
        self, mock_restart_workers
    ):
        mock_restart_workers.return_value = {
            "count": 1,
            "failures": [{"challenge_pk": 77, "message": "Failed to restart"}],
        }
        self.admin.restart_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)

        assert any("succesfully restarted" in str(m) for m in messages)

        assert any(
            "Challenge 77: Failed to restart" in str(m) for m in messages
        )

    @patch("challenges.admin.delete_workers")
    def test_delete_selected_workers_partial_failure(
        self, mock_delete_workers
    ):
        mock_delete_workers.return_value = {
            "count": 1,
            "failures": [{"challenge_pk": 55, "message": "Failed to delete"}],
        }
        self.admin.delete_selected_workers(self.request, self.queryset)
        messages = list(self.request._messages)

        assert any("succesfully deleted" in str(m) for m in messages)

        assert any(
            "Challenge 55: Failed to delete" in str(m) for m in messages
        )
