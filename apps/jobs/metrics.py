import os

from prometheus_client import Counter, pushadd_to_gateway, CollectorRegistry


pushgateway_registry = CollectorRegistry()

num_submissions_in_queue = Counter(
    "num_submissions_in_queue",
    "Counter for number of submissions pushed into queue",
    ["submission_pk", "queue_name"],
    registry=pushgateway_registry,
)


def push_metrics_to_pushgateway(job_id):
    pushgateway_endpoint = os.environ.get("PUSHGATEWAY_ENDPOINT")
    pushadd_to_gateway(pushgateway_endpoint, job=job_id, registry=pushgateway_registry)
