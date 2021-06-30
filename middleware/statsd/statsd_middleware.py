import time
import os
from datadog import DogStatsd
from django.utils.deprecation import MiddlewareMixin

statsd_host = os.environ.get("STATSD_ENDPOINT")
statsd_port = int(os.environ.get("STATSD_PORT"))
statsd = DogStatsd(host=statsd_host, port=statsd_port)

REQUEST_LATENCY_METRIC_NAME = 'django_request_latency_seconds'
REQUEST_COUNT_METRIC_NAME = 'django_request_count'


class StatsdMetricsMiddleware(MiddlewareMixin):

    def process_request(self, request):
        request.start_time = time.time()
        

    def process_response(self, request, response):
        statsd.increment(REQUEST_COUNT_METRIC_NAME,
            tags=[
                'service:django_worker', 
                'method:%s' % request.method, 
                'endpoint:%s' % request.path,
                'status:%s' % str(response.status_code)
                ]
        )

        resp_time = (time.time() - request.start_time)*1000

        statsd.histogram(REQUEST_LATENCY_METRIC_NAME,
                resp_time,
                tags=[
                    'service:django_worker',
                    'endpoint:%s' % request.path,
                    ]
        )

        return response

