from django.contrib.auth import logout
from django.contrib.auth.models import User

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

from .permissions import HasVerifiedEmail


from allauth.socialaccount.providers.github.views import GitHubOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from rest_auth.registration.views import SocialLoginView
from django.conf import settings


class GithubLogin(SocialLoginView):
    adapter_class = GitHubOAuth2Adapter
    callback_url = settings.FRONTEND_URL + "/auth/oauth-redirect/github/"
    client_class = OAuth2Client


@api_view(["POST"])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((ExpiringTokenAuthentication,))
def disable_user(request):

    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_auth_token(request):
    try:
        user = User.objects.get(email=request.user.email)
    except User.DoesNotExist:
        response_data = {"error": "This User account doesn't exist."}
        Response(response_data, status.HTTP_404_NOT_FOUND)

    try:
        token = Token.objects.get(user=user)
    except Token.DoesNotExist:
        token = Token.objects.create(user=user)
        token.save()

    response_data = {"token": "{}".format(token)}
    return Response(response_data, status=status.HTTP_200_OK)
