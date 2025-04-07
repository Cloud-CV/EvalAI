"""
Views for user account and authentication-related operations.
"""

from django.contrib.auth import logout
from django.contrib.auth.models import User

from allauth.account.utils import send_email_confirmation

from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken

from .models import JwtToken
from .permissions import HasVerifiedEmail
from .serializers import JwtTokenSerializer
from .throttles import ResendEmailThrottle


@api_view(["POST"])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def disable_user(request):
    """
    Deactivate the user account and log them out.
    """
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
    """
    Retrieve JWT token for the authenticated user.
    """
    try:
        user = User.objects.get(email=request.user.email)
    except User.DoesNotExist:
        return Response(
            {"error": "This User account doesn't exist."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        token = JwtToken.objects.get(user=user)
    except JwtToken.DoesNotExist:
        jwt_refresh_token = RefreshToken.for_user(user)
        token = JwtToken(user=user)
        token_serializer = JwtTokenSerializer(
            token,
            data={
                "refresh_token": str(jwt_refresh_token),
                "access_token": str(jwt_refresh_token.access_token),
            },
            partial=True,
        )
        if token_serializer.is_valid():
            token_serializer.save()
        token = token_serializer.instance

    outstanding_token = OutstandingToken.objects.filter(
        user=user
    ).order_by("-created_at")[0]

    response_data = {
        "token": f"{token.refresh_token}",
        "expires_at": outstanding_token.expires_at,
    }
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["POST"])
@throttle_classes([ResendEmailThrottle])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def resend_email_confirmation(request):
    """
    Resend the email confirmation to the authenticated user.
    """
    user = request.user
    send_email_confirmation(request, user)
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def refresh_auth_token(request):
    """
    Refresh the JWT token and blacklist the old one if applicable.
    """
    try:
        user = User.objects.get(email=request.user.email)
    except User.DoesNotExist:
        return Response(
            {"error": "This User account doesn't exist."},
            status=status.HTTP_404_NOT_FOUND,
        )

    try:
        token = JwtToken.objects.get(user=user)
        try:
            existing_token = RefreshToken(token.refresh_token)
            existing_token.blacklist()
            token.delete()
        except TokenError:
            # Token already expired, skip blacklisting
            pass
    except JwtToken.DoesNotExist:
        token = JwtToken(user=user)

    jwt_refresh_token = RefreshToken.for_user(user)
    token_serializer = JwtTokenSerializer(
        token,
        data={
            "refresh_token": str(jwt_refresh_token),
            "access_token": str(jwt_refresh_token.access_token),
        },
        partial=True,
    )

    if token_serializer.is_valid():
        token_serializer.save()
        token = token_serializer.instance
        response_data = {"token": f"{token.refresh_token}"}
        return Response(response_data, status=status.HTTP_200_OK)

    return Response(
        {"error": "Token refresh failed."},
        status=status.HTTP_400_BAD_REQUEST,
    )
    
