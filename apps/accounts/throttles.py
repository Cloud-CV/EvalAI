from rest_framework.throttling import SimpleRateThrottle

from django.core.cache import caches

from django.conf import settings


class ResendEmailThrottle(SimpleRateThrottle):
    """
    Used to limit the requests to /accounts/user/resend_email_verification/
    to 3/hour.
    """

    if (settings.DEBUG is True) or (settings.TEST is True):
        cache = caches["throttling"]

    scope = "resend_email"

    def get_cache_key(self, request, view):

        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
