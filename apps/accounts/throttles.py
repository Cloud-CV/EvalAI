from rest_framework.throttling import SimpleRateThrottle


class ResendEmailThrottle(SimpleRateThrottle):
    """
    Used to limit the requests to /accounts/user/resend-email
    to 2/minute.
    """
    scope = 'resend_email'

    def get_cache_key(self, request, view):
        if request.user.is_authenticated:
            ident = request.user.pk
        else:
            ident = self.get_ident(request)

        return self.cache_format % {
            'scope': self.scope,
            'ident': ident
        }
