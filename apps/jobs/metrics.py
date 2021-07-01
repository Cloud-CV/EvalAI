import logging
import os

from prometheus_client import Counter, pushadd_to_gateway, CollectorRegistry
from prometheus_client.exposition import basic_auth_handler

logger = logging.getLogger(__name__)

pushgateway_registry = CollectorRegistry()

submissions_loaded_in_queue = Counter(
    "submissions_loaded_in_queue",
    "Counter for total number of submissions pushed into the queue when a submission is made",
    ["submission_pk", "queue_name"],
    registry=pushgateway_registry,
)


def pushgateway_auth_handler(url, method, timeout, headers, data):
    try:
        username = os.environ.get("HTTP_AUTH_USERNAME")
        password = os.environ.get("HTTP_AUTH_PASSWORD")
    except Exception as e:
        logger.exception(
            "Exception while fetching env variables for pushgateway authentication: {}".format(
                e
            )
        )
    return basic_auth_handler(
        url, method, timeout, headers, data, username, password
    )


def push_metrics_to_pushgateway(job_id):
    pushgateway_endpoint = os.environ.get("PUSHGATEWAY_ENDPOINT")
    pushadd_to_gateway(
        pushgateway_endpoint,
        job=job_id,
        registry=pushgateway_registry,
        handler=pushgateway_auth_handler,
    )
