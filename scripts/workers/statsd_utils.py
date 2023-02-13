import logging
import sys

from monitoring.statsd.metrics import NUM_PROCESSED_SUBMISSIONS, increment_statsd_counter

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
