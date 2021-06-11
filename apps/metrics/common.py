from prometheus_client import Counter, CollectorRegistry, push_to_gateway

pushgateway_registry = CollectorRegistry()


class Metrics:
    total_http_requests_sample = Counter(
        "total_http_requests_sample",
        "Total number of http requests completed",
        ["app_name", "endpoint_name", "request_type", "response_code"],
        registry=pushgateway_registry,
    )


def push_prometheus_metrics_to_gateway():
    push_to_gateway(
        "pushgateway:9091",
        job="django-prometheus",
        registry=pushgateway_registry,
    )
