import unittest
from unittest.mock import patch
from scripts.workers.statsd_utils import (
    increment_statsd_counter,
    increment_and_push_metrics_to_statsd,
)


class TestStatsdFunctions(unittest.TestCase):

    @patch("scripts.workers.statsd_utils.statsd.increment")
    def test_increment_statsd_counter(self, mock_increment):
        metric_name = "test_metric"
        tags = ["tag1", "tag2"]
        inc_value = 1

        increment_statsd_counter(metric_name, tags, inc_value)

        mock_increment.assert_called_once_with(
            metric_name, inc_value, tags=tags
        )

    @patch("scripts.workers.statsd_utils.statsd.increment")
    def test_increment_statsd_counter_with_exception(self, mock_increment):
        metric_name = "test_metric"
        tags = ["tag1", "tag2"]
        inc_value = 1

        mock_increment.side_effect = Exception("Mocked exception")

        with self.assertRaises(Exception):
            increment_statsd_counter(metric_name, tags, inc_value)

    @patch("scripts.workers.statsd_utils.logger.exception")
    @patch("scripts.workers.statsd_utils.statsd.increment")
    def test_increment_and_push_metrics_to_statsd_exception(
        self, mock_increment, mock_logger_exception
    ):
        queue_name = "test_queue"
        is_remote = True

        mock_increment.side_effect = Exception("Mocked exception")

        increment_and_push_metrics_to_statsd(queue_name, is_remote)

        mock_logger_exception.assert_called_once()

    @patch("scripts.workers.statsd_utils.statsd.increment")
    def test_increment_and_push_metrics_to_statsd_success(
        self, mock_increment
    ):
        queue_name = "test_queue"
        is_remote = True

        increment_and_push_metrics_to_statsd(queue_name, is_remote)

        mock_increment.assert_called_once_with(
            "num_processed_submissions",
            1,
            tags=["queue_name:test_queue", "is_remote:1"],
        )
