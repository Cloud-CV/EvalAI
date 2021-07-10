import os
import time

from datadog import DogStatsd
from django.utils.deprecation import MiddlewareMixin


statsd_host = os.environ.get("STATSD_ENDPOINT")
statsd_port = int(os.environ.get("STATSD_PORT"))
statsd = DogStatsd(host=statsd_host, port=statsd_port)

REQUEST_LATENCY_METRIC_NAME = "django_request_latency_seconds"
REQUEST_COUNT_METRIC_NAME = "django_request_count"


class StatsdMetricsMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()

    def get_view_name(self, request):
        view_name = "<unnamed view>"
        if hasattr(request, "resolver_match"):
            if request.resolver_match is not None:
                if request.resolver_match.view_name is not None:
                    view_name = request.resolver_match.view_name
        return view_name

    def process_response(self, request, response):
        statsd.increment(
            REQUEST_COUNT_METRIC_NAME,
            tags=[
                "service:django_worker",
                "method:%s" % request.method,
                "view:%s" % self.get_view_name(request),
                "status:%s" % str(response.status_code),
            ],
        )

        resp_time = (time.time() - request.start_time) * 1000

        statsd.histogram(
            REQUEST_LATENCY_METRIC_NAME,
            resp_time,
            tags=[
                "service:django_worker",
                "view:%s" % self.get_view_name(request),
            ],
        )

        return response
