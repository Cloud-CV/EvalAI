from django.conf import settings
from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils.decorators import method_decorator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode as uid_decoder
from django.views.decorators.debug import sensitive_post_parameters

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,)
from rest_framework_expiring_authtoken.authentication import (ExpiringTokenAuthentication,)
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_auth.serializers import PasswordResetConfirmSerializer
from .serializers import PasswordResetTokenSerializer

sensitive_post_parameters_m = method_decorator(
    sensitive_post_parameters(
        'password', 'old_password', 'new_password1', 'new_password2'
    )
)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((ExpiringTokenAuthentication,))
def disable_user(request):

    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return Response(status=status.HTTP_200_OK)


class PasswordResetTokenView(GenericAPIView):
    """
    Password reset e-mail link is confirmed, therefore
    this resets the user's password.

    Accepts the following POST parameters: token, uid,
        new_password1, new_password2
    Returns the success/fail message.
    """
    serializer_class = PasswordResetTokenSerializer

    permission_classes = (AllowAny,)

    def post(self, request):
        self.get_serializer(data=request.data).is_valid(raise_exception=True)
        return Response({'data': request.data})


class PasswordResetConfirmView(GenericAPIView):
    """
    Password reset e-mail link is confirmed, therefore
    this resets the user's password.

    Accepts the following POST parameters: token, uid,
        new_password1, new_password2
    Returns the success/fail message.
    """
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = (AllowAny,)

    @sensitive_post_parameters_m
    def dispatch(self, *args, **kwargs):
        return super(PasswordResetConfirmView, self).dispatch(*args, **kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        if serializer.is_valid():
            uid = force_text(uid_decoder(request.data['uid']))
            host = request.data['host']
            send_mail('Password reset on '+host,
                      "You're receiving this mail because your password has been reset at "+host
                      + "\nThanks for using our site!\n The " + host + " team",
                      settings.DEFAULT_FROM_EMAIL,
                      [User.objects.get(pk=uid).email],
                      fail_silently=False,
                      )
        return Response({"detail": ("Password has been reset with the new password.")})
