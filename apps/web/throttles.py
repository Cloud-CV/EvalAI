from django.conf import settings
from django.core.cache import caches
from rest_framework.throttling import SimpleRateThrottle


class BulkEmailThrottle(SimpleRateThrottle):
    """
    Throttle class for bulk email operations to prevent abuse.
    Limits bulk email notifications to a conservative rate.
    """

    if (settings.DEBUG is True) or (settings.TEST is True):
        cache = caches["throttling"]

    scope = "bulk_email"

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)
        return self.cache_format % {"scope": self.scope, "ident": ident}
