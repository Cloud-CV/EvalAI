from django.contrib.auth import logout
from django.contrib.auth.models import User

from allauth.account.utils import send_email_confirmation

from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.throttling import UserRateThrottle
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from .models import JwtToken
from .permissions import HasVerifiedEmail

from .throttles import ResendEmailThrottle


@api_view(["POST"])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def disable_user(request):

    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def get_auth_token(request):
    try:
        user = User.objects.get(email=request.user.email)
    except User.DoesNotExist:
        response_data = {"error": "This User account doesn't exist."}
        Response(response_data, status.HTTP_404_NOT_FOUND)

    try:
        token = JwtToken.objects.get(user=user)
    except Exception as e:
        jwt_token = RefreshToken.for_user(user)
        token = JwtToken.objects.create(
            user=user,
            access_token=str(jwt_token.access_token),
            refresh_token=str(jwt_token)
        )
        token.save()

    response_data = {"token": "{}".format(token.access_token)}
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([ResendEmailThrottle])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def resend_email_confirmation(request):
    """
    Resends the confirmation email on user request.
    """
    user = request.user
    send_email_confirmation(request._request, user)
    return Response(status=status.HTTP_200_OK)
