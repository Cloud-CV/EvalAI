"""Regression tests for scripts/monitoring/auto_scale_workers.py."""

import importlib.util
import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import pytz


def _load_auto_scale_workers():
    """Load the cron script by path.

    It uses ``from evalai_interface import ...`` (script-directory imports),
    so package import ``scripts.monitoring.auto_scale_workers`` fails unless
    the monitoring dir is on sys.path — matching how the cron runner invokes it.
    """
    monitoring_dir = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "..",
            "scripts",
            "monitoring",
        )
    )
    if monitoring_dir not in sys.path:
        sys.path.insert(0, monitoring_dir)
    module_path = os.path.join(monitoring_dir, "auto_scale_workers.py")
    spec = importlib.util.spec_from_file_location(
        "auto_scale_workers_under_test", module_path
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


auto_scale_workers = _load_auto_scale_workers()


def _challenge(end_date, workers=1):
    return {
        "id": 42,
        "title": "Drain Me",
        "workers": workers,
        "end_date": end_date.isoformat(),
        "remote_evaluation": False,
    }


class TestScaleUpOrDownWorkersPendingDrain(unittest.TestCase):
    @patch.object(auto_scale_workers, "scale_up_workers")
    @patch.object(auto_scale_workers, "scale_down_workers")
    def test_ended_challenge_with_pending_submissions_leaves_workers_up(
        self, mock_scale_down, mock_scale_up
    ):
        """
        After end_date, pending work must keep draining.

        The previous ``pending == 0 or end_date < now`` condition stopped
        workers for every ended challenge, which undid the cleanup Lambda's
        pending-aware skip (#5179) and left queued/running submissions
        without consumers.
        """
        ended = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(hours=1)
        challenge = _challenge(ended, workers=1)
        metrics = {"running": 1, "submitted": 0, "queued": 2, "resuming": 0}

        auto_scale_workers.scale_up_or_down_workers(challenge, metrics)

        mock_scale_down.assert_not_called()
        mock_scale_up.assert_not_called()

    @patch.object(auto_scale_workers, "scale_up_workers")
    @patch.object(auto_scale_workers, "scale_down_workers")
    def test_ended_challenge_with_no_pending_scales_down(
        self, mock_scale_down, mock_scale_up
    ):
        ended = datetime.utcnow().replace(tzinfo=pytz.UTC) - timedelta(hours=1)
        challenge = _challenge(ended, workers=1)
        metrics = {"running": 0, "submitted": 0, "queued": 0, "resuming": 0}

        auto_scale_workers.scale_up_or_down_workers(challenge, metrics)

        mock_scale_down.assert_called_once_with(challenge, 1)
        mock_scale_up.assert_not_called()

    @patch.object(auto_scale_workers, "scale_up_workers")
    @patch.object(auto_scale_workers, "scale_down_workers")
    def test_active_challenge_with_pending_scales_up(
        self, mock_scale_down, mock_scale_up
    ):
        future = datetime.utcnow().replace(tzinfo=pytz.UTC) + timedelta(days=1)
        challenge = _challenge(future, workers=0)
        metrics = {"running": 0, "submitted": 1, "queued": 0, "resuming": 0}

        auto_scale_workers.scale_up_or_down_workers(challenge, metrics)

        mock_scale_up.assert_called_once_with(challenge, 0)
        mock_scale_down.assert_not_called()

    @patch.object(auto_scale_workers, "scale_up_workers")
    @patch.object(auto_scale_workers, "scale_down_workers")
    def test_active_challenge_with_no_pending_scales_down(
        self, mock_scale_down, mock_scale_up
    ):
        future = datetime.utcnow().replace(tzinfo=pytz.UTC) + timedelta(days=1)
        challenge = _challenge(future, workers=2)
        metrics = {"running": 0, "submitted": 0, "queued": 0, "resuming": 0}

        auto_scale_workers.scale_up_or_down_workers(challenge, metrics)

        mock_scale_down.assert_called_once_with(challenge, 2)
        mock_scale_up.assert_not_called()
