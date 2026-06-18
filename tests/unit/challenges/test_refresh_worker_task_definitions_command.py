from io import StringIO
from unittest.mock import MagicMock, patch

from challenges.models import Challenge
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase


class RefreshWorkerTaskDefinitionsCommandTest(TestCase):
    @patch(
        "challenges.management.commands.refresh_worker_task_definitions."
        "refresh_worker_task_definitions"
    )
    def test_dry_run_prints_failures(self, mock_refresh):
        mock_refresh.return_value = {
            "count": 0,
            "failures": [
                {
                    "challenge_pk": 1,
                    "message": "Worker task definitions cannot be refreshed",
                }
            ],
        }
        out = StringIO()
        call_command(
            "refresh_worker_task_definitions", dry_run=True, stdout=out
        )
        output = out.getvalue()
        self.assertIn("Dry run: 0 challenge(s) would be refreshed.", output)
        self.assertIn("Challenge 1:", output)

    @patch(
        "challenges.management.commands.refresh_worker_task_definitions."
        "refresh_worker_task_definitions"
    )
    def test_command_raises_when_refresh_failures_exist(self, mock_refresh):
        mock_refresh.return_value = {
            "count": 1,
            "failures": [{"challenge_pk": 2, "message": "refresh failed"}],
        }
        with self.assertRaises(CommandError):
            call_command("refresh_worker_task_definitions")

    @patch(
        "challenges.management.commands.refresh_worker_task_definitions."
        "refresh_worker_task_definitions"
    )
    @patch.object(Challenge.objects, "filter")
    def test_command_passes_commit_id_and_challenge_pk(
        self, mock_filter, mock_refresh
    ):
        mock_queryset = MagicMock()
        mock_filter.return_value = mock_queryset
        mock_queryset.exists.return_value = True
        mock_refresh.return_value = {"count": 1, "failures": []}
        call_command(
            "refresh_worker_task_definitions",
            commit_id="abc123",
            challenge_pk=42,
        )
        mock_filter.assert_called_once_with(pk=42)
        mock_refresh.assert_called_once_with(
            queryset=mock_queryset,
            commit_id="abc123",
            dry_run=False,
        )

    def test_command_errors_for_missing_challenge(self):
        with self.assertRaises(CommandError):
            call_command(
                "refresh_worker_task_definitions",
                challenge_pk=999999,
            )
