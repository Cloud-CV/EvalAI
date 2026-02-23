"""
Custom token authentication that safely handles missing/expired tokens.

The third-party djangorestframework-expiring-authtoken can raise
AttributeError ('NoneType' object has no attribute 'DoesNotExist') when
a token is invalid and the package's except clause uses self.model, which
may be None in some environments. This subclass catches
ExpiringToken.DoesNotExist explicitly so invalid tokens always result in
AuthenticationFailed.

When authentication fails (invalid/expired token or inactive user), the user
is logged out so any server-side session is cleared.
"""

from django.contrib.auth import logout
from rest_framework import exceptions
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication as BaseExpiringTokenAuthentication,
)
from rest_framework_expiring_authtoken.models import ExpiringToken


class ExpiringTokenAuthentication(BaseExpiringTokenAuthentication):
    """
    Expiring token auth that safely raises AuthenticationFailed for invalid tokens.
    """

    def authenticate(self, request):
        """Run token auth and log out the request session when auth fails."""
        try:
            return super().authenticate(request)
        except exceptions.AuthenticationFailed:
            # DRF Request wraps Django HttpRequest as ._request (no public
            # alias)
            logout(request._request)  # pylint: disable=protected-access
            raise

    def authenticate_credentials(self, key):  # pylint: disable=no-self-use
        """Authenticate by token key; raise AuthenticationFailed if invalid/expired."""
        try:
            token = ExpiringToken.objects.get(key=key)
        except ExpiringToken.DoesNotExist as exc:
            raise exceptions.AuthenticationFailed("Invalid token") from exc
        if not token.user.is_active:
            raise exceptions.AuthenticationFailed("User inactive or deleted")
        if token.expired():
            raise exceptions.AuthenticationFailed("Token has expired")
        return (token.user, token)
