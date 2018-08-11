"""Authentication classes for Django Rest Framework.

Classes:
    ExpiringTokenAuthentication: Authentication using extended authtoken model.
"""

from rest_framework import exceptions
from rest_framework.authentication import TokenAuthentication

from rest_framework_expiring_authtoken.models import ExpiringToken


class ExpiringTokenAuthentication(TokenAuthentication):

    """
    Extends default token auth to have time-based expiration.

    Based on http://stackoverflow.com/questions/14567586/
    """

    model = ExpiringToken

    def authenticate_credentials(self, key):
        """Attempt token authentication using the provided key."""
        try:
            token = self.model.objects.get(key=key)
        except self.model.DoesNotExist:
            raise exceptions.AuthenticationFailed('Invalid token')

        if not token.user.is_active:
            raise exceptions.AuthenticationFailed('User inactive or deleted')

        if token.expired():
            raise exceptions.AuthenticationFailed('Token has expired')

        return (token.user, token)
