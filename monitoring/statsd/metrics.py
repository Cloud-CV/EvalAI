import os

from datadog import DogStatsd


statsd_host = os.environ.get("STATSD_ENDPOINT")
statsd_port = int(os.environ.get("STATSD_PORT"))
statsd = DogStatsd(host=statsd_host, port=statsd_port)

REQUEST_LATENCY_METRIC_NAME = "django_request_latency_seconds"
REQUEST_COUNT_METRIC_NAME = "django_request_count"
NUM_SUBMISSIONS_IN_QUEUE = "num_submissions_in_queue"
NUM_PROCESSED_SUBMISSIONS = "num_processed_submissions"


def increment_statsd_counter(metric_name, tags, inc_value):
    statsd.increment(metric_name, inc_value, tags=tags)
