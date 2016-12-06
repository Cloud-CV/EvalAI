from allauth.account.models import EmailAddress
from rest_framework import permissions


class HasVerifiedEmail(permissions.BasePermission):
    """
    Permission class for if the user has verified the email or not
    """

    message = "Please verify your email first!"

    def has_permission(self, request, view):

        if EmailAddress.objects.filter(user=request.user, verified=True).exists():
            return True
        else:
            return False
