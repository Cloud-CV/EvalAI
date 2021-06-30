from prometheus_client import Counter, pushadd_to_gateway, CollectorRegistry
import os

pushgateway_registry = CollectorRegistry()

submissions_loaded_in_queue = Counter(
    "submissions_loaded_in_queue",
    "Counter for total number of submissions pushed into the queue when a submission is made",
    ["submission_pk", "queue_name"],
    registry=pushgateway_registry,
)


def push_metrics_to_pushgateway(job_id):
    pushgateway_endpoint = os.environ.get("PUSHGATEWAY_ENDPOINT")
    pushadd_to_gateway(pushgateway_endpoint, job=job_id, registry=pushgateway_registry)
