from rest_framework_expiring_authtoken.models import ExpiringToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from .models import JwtToken


def revoke_all_user_tokens(user):
    """
    Invalidate every active credential for a user.

    Called after password change or reset so existing browser sessions,
    API tokens, and JWT refresh tokens cannot keep working.
    """
    ExpiringToken.objects.filter(user=user).delete()
    JwtToken.objects.filter(user=user).delete()

    for outstanding_token in OutstandingToken.objects.filter(user=user):
        if BlacklistedToken.objects.filter(token=outstanding_token).exists():
            continue
        try:
            RefreshToken(outstanding_token.token).blacklist()
        except TokenError:
            BlacklistedToken.objects.get_or_create(token=outstanding_token)
