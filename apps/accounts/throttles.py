from django.conf import settings
from django.core.cache import caches
from rest_framework.throttling import SimpleRateThrottle


class _ThrottlingCacheMixin:
    """Use a dedicated cache backend in dev/test for reliable throttle tests."""

    if (settings.DEBUG is True) or (settings.TEST is True):
        cache = caches["throttling"]


class ResendEmailThrottle(_ThrottlingCacheMixin, SimpleRateThrottle):
    """
    Used to limit the requests to /accounts/user/resend_email_verification/
    to 3/hour.
    """

    scope = "resend_email"

    def get_cache_key(self, request, view):

        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}


class PasswordResetEmailThrottle(_ThrottlingCacheMixin, SimpleRateThrottle):
    """
    Limit password reset requests to 3/hour per target email address.
    """

    scope = "password_reset_email"

    def get_cache_key(self, request, view):
        email = (request.data.get("email") or "").strip().lower()
        if not email:
            return None
        return self.cache_format % {"scope": self.scope, "ident": email}


class PasswordResetIPThrottle(_ThrottlingCacheMixin, SimpleRateThrottle):
    """
    Limit password reset requests to 10/hour per client IP address.
    """

    scope = "password_reset_ip"

    def get_cache_key(self, request, view):
        return self.cache_format % {
            "scope": self.scope,
            "ident": self.get_ident(request),
        }
