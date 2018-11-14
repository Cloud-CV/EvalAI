from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.db import IntegrityError

from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework.throttling import UserRateThrottle
from rest_framework_expiring_authtoken.authentication import (ExpiringTokenAuthentication,)

from .permissions import HasVerifiedEmail


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((ExpiringTokenAuthentication,))
def disable_user(request):

    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return Response(status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['GET'])
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


@throttle_classes([UserRateThrottle])
@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication, ))
def generate_auth_token(request):
    try:
        user = User.objects.get(id=request.user.pk)
    except User.DoesNotExist:
        response_data = {"error": "This User account doesn't exist."}
        return Response(response_data, status.HTTP_404_NOT_FOUND)
    try:
        old_auth_token = Token.objects.get(user_id=request.user.pk)
    except Token.DoesNotExist:
        response_data = {"error": "This Token account doesn't exist."}
        return Response(response_data, status.HTTP_404_NOT_FOUND)
    Token.delete(old_auth_token)
    try:
        new_token = Token.objects.create(user=user)
    except IntegrityError:
        response_data = {"error": "Token was not able to be created"}
        return Response(response_data, status.HTTP_404_NOT_FOUND)
    new_token.save()
    response_data = {
        "message": "The new generated auth token for {} is {}".format(request.user.username, new_token),
    }
    return Response(response_data, status=status.HTTP_200_OK)
