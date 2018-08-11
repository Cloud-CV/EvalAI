"""Expiring Token models.

Classes:
    ExpiringToken
"""

from django.utils import timezone

from rest_framework.authtoken.models import Token

from rest_framework_expiring_authtoken.settings import token_settings


class ExpiringToken(Token):

    """Extend Token to add an expired method."""

    class Meta(object):
        proxy = True

    def expired(self):
        """Return boolean indicating token expiration."""
        now = timezone.now()
        if self.created < now - token_settings.EXPIRING_TOKEN_LIFESPAN:
            return True
        return False
