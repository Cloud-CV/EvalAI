from django.contrib.auth import logout


from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,)
from rest_framework_expiring_authtoken.authentication import (ExpiringTokenAuthentication,)
from rest_framework.generics import GenericAPIView
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .serializers import PasswordResetTokenSerializer

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

    def dispatch(self, *args, **kwargs):
        return super(PasswordResetTokenView, self).dispatch(*args, **kwargs)

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'data':request.data})
