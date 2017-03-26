from django.contrib.auth import logout
from django.urls import reverse
from django.views.generic import View
from django.shortcuts import render

from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,)
from rest_framework_expiring_authtoken.authentication import (ExpiringTokenAuthentication,)

import requests


class ConfirmEmailView(View):
    """
    View for confirming email after registration
    """

    def get(self, request, *args, **kwargs):
        post_data = {
            'key': kwargs['key'],
        }

        requests.post(request.build_absolute_uri(
            reverse("rest_verify_email")), data=post_data)
        return render(request, 'account/email-verification-done.html')


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((ExpiringTokenAuthentication,))
def disable_user(request):

    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return Response(status=status.HTTP_200_OK)
