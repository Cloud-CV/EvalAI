import time
import traceback

from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

from datadog import initialize
from datadog import statsd, api

options = {
    "api_key": settings.DATADOG_API_KEY,
    "app_key": settings.DATADOG_APP_KEY,
}

initialize(**options)


class DatadogMiddleware(MiddlewareMixin):
    """
    Middleware to submit some metrics to DataDog about each requests.
    """

    DATADOG_TIMING_ATTRIBUTE = "_datadog_start_time"
    app_name = settings.DATADOG_APP_NAME

    def process_request(self, request):
        setattr(request, self.DATADOG_TIMING_ATTRIBUTE, time.time())

    def process_response(self, request, response):
        if not hasattr(request, self.DATADOG_TIMING_ATTRIBUTE):
            return response

        request_time = time.time() - getattr(
            request, self.DATADOG_TIMING_ATTRIBUTE
        )

        timing_metric = "{0}.request_time".format(self.app_name)
        count_metric = "{0}.no_of_requests_metric".format(self.app_name)
        success_metric = "{0}.no_of_successful_requests_metric".format(
            self.app_name
        )
        unsuccess_metric = "{0}.no_of_unsuccessful_requests_metric".format(
            self.app_name
        )

        tags = self._get_metric_tags(request)

        if 200 <= response.status_code < 400:
            statsd.increment(success_metric, tags=tags)
        else:
            statsd.increment(unsuccess_metric, tags=tags)

        statsd.increment(count_metric, tags=tags)
        statsd.histogram(timing_metric, request_time, tags=tags)

        return response

    def process_exception(self, request, exception):
        exc = traceback.format_exc()
        title = "Exception from {0}".format(request.path)
        text = "Traceback: {0}".format(exc)

        tags = self._get_metric_tags(request)
        event_tags = [self.app_name, "unhandled_exception"]
        app_error_metric = "{0}.unhandled_errors.{1}".format(
            self.app_name, request.path
        )

        statsd.increment(app_error_metric, tags=tags)
        api.Event.create(title=title, text=text, tags=event_tags)

    def _get_metric_tags(self, request):
        return ["path:{0}".format(request.path)]
