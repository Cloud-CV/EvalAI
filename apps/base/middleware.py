from .views import health_check

HEALTH_CHECK_PATH = "/api/health/"


class HealthCheckMiddleware:
    """
    Answer the load balancer health check before host validation runs.

    An ALB health-checks its targets by private IP and cannot be configured to
    send a custom Host header, so the request never matches ALLOWED_HOSTS.
    Django would reject it with 400 and the load balancer would mark every
    target unhealthy, taking the whole service out of rotation.

    Matching on ``request.path`` is what makes this work: the path comes from
    PATH_INFO and needs no host, so nothing here calls ``request.get_host()``
    and validation never runs. This middleware must stay FIRST in MIDDLEWARE.
    Returning without calling ``get_response`` skips every middleware below it,
    including the ones that would perform the host check.

    The bypass is deliberately limited to one path serving a static payload
    with no database access and no user data. The attacks ALLOWED_HOSTS exists
    to prevent -- poisoned password-reset links, cache poisoning, redirects to
    attacker-controlled hosts -- all need a response that reflects the host
    back, which this one never does. Every other path keeps full validation.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path == HEALTH_CHECK_PATH:
            return health_check(request)
        return self.get_response(request)
