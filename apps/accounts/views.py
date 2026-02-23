from allauth.account.utils import send_email_confirmation
from django.contrib.auth import logout
from django.contrib.auth.models import User
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken

from .authentication import ExpiringTokenAuthentication
from .models import JwtToken
from .permissions import HasVerifiedEmail
from .serializers import JwtTokenSerializer
from .throttles import ResendEmailThrottle
from django.core.mail import EmailMessage

from django.shortcuts import render
from django.utils.encoding import force_bytes, force_text
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode


@api_view(['GET'])
def generate_activation_link(request, user_email):
    try:
        user = User.objects.get(email=user_email)
    except User.DoesNotExist:
        return Response({'error': 'User with this email does not exist.'}, status=status.HTTP_404_NOT_FOUND)
    if user.is_active:
        return Response({'message': 'Account is already active.'}, status=status.HTTP_400_BAD_REQUEST)

    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    activation_link = f"https://eval.ai/api/accounts/user/activate/{uid}/{token}"
    mail_subject = 'Activate your account.'
    message = f"Dear {user.email},\n\nPlease click on the following link to activate your account:\n{activation_link}\n\nIf you did not request this, please ignore this email.\n\nBest regards,\nCloud CV Team"
    email = EmailMessage(mail_subject, message, to=[user.email])
    email.send()
    return Response({'message': 'Activation link has been sent to your email.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
def activate_user(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
        if default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            # Render the account_activate_confirmed.html template
            return render(request, 'account/account_activate_confirmed.html', {'error': None})
        else:
            return render(request, 'account/account_activate_confirmed.html', {'error': 'Invalid activation link. Please Check the link again.'})
    except Exception as e:
        return render(request, 'account/account_activate_confirmed.html', {'error': str(e)})


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

    outstanding_token = OutstandingToken.objects.filter(user=user).order_by(
        "-created_at"
    )[0]
    response_data = {
        "token": "{}".format(token.refresh_token),
        "expires_at": outstanding_token.expires_at,
    }
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


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((JWTAuthentication, ExpiringTokenAuthentication))
def refresh_auth_token(request):
    try:
        user = User.objects.get(email=request.user.email)
    except User.DoesNotExist:
        response_data = {"error": "This User account doesn't exist."}
        Response(response_data, status.HTTP_404_NOT_FOUND)

    token = None
    try:
        token = JwtToken.objects.get(user=user)
        try:
            existing_token = RefreshToken(token.refresh_token)
            existing_token.blacklist()
            token.delete()
        except TokenError:
            # No need to blacklist when token is expired
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
        response_data = {"token": "{}".format(token.refresh_token)}
        return Response(response_data, status=status.HTTP_200_OK)

    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
