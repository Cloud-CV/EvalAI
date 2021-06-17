from prometheus_client import Counter, REGISTRY, push_to_gateway


class Metrics:
    total_http_requests_sample = Counter(
        "total_http_requests_sample",
        "Total number of http requests completed",
        ["app_name", "endpoint_name", "request_type", "response_code"],
        registry=REGISTRY,
    )


def push_prometheus_metrics_to_gateway():
    push_to_gateway("pushgateway:9091", job="django", registry=REGISTRY)
