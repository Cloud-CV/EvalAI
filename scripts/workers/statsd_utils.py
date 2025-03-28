import logging
import sys

import os

from datadog import DogStatsd


statsd_host = os.environ.get("STATSD_ENDPOINT", "statsd")
statsd_port = int(os.environ.get("STATSD_PORT", "9125"))
statsd = DogStatsd(host=statsd_host, port=statsd_port)

REQUEST_LATENCY_METRIC_NAME = "django_request_latency_seconds"
REQUEST_COUNT_METRIC_NAME = "django_request_count"
NUM_SUBMISSIONS_IN_QUEUE = "num_submissions_in_queue"
NUM_PROCESSED_SUBMISSIONS = "num_processed_submissions"


def increment_statsd_counter(metric_name, tags, inc_value):
    statsd.increment(metric_name, inc_value, tags=tags)
    return


formatter = logging.Formatter(
    "[%(asctime)s] %(levelname)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

SUBMISSION_LOGS_PREFIX = "SUBMISSION_LOG"


def increment_and_push_metrics_to_statsd(queue_name, is_remote):
    try:
        submission_metric_tags = [
            "queue_name:%s" % queue_name,
            "is_remote:%d" % is_remote,
        ]
        increment_statsd_counter(NUM_PROCESSED_SUBMISSIONS, submission_metric_tags, 1)
    except Exception as e:
        logger.exception(
            "{} Exception when pushing metrics to statsd: {}".format(
                SUBMISSION_LOGS_PREFIX, e
            )
        )
