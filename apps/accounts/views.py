from django.contrib.auth import logout

from allauth.account.utils import send_email_confirmation

from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework_expiring_authtoken.authentication import (ExpiringTokenAuthentication,)

from .throttles import ResendEmailThrottle


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((ExpiringTokenAuthentication,))
def disable_user(request):
    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return Response(status=status.HTTP_200_OK)


@throttle_classes([ResendEmailThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((ExpiringTokenAuthentication,))
def resend_email_confirmation(request):
    """
    Resends the confirmation Email by the users request.
    """
    user = request.user
    send_email_confirmation(request._request, user)
    return Response(status=status.HTTP_200_OK)
