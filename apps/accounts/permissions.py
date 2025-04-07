from allauth.account.models import EmailAddress
from rest_framework import permissions


class HasVerifiedEmail(permissions.BasePermission):
    """
    Permission class to check if the user's email is verified.
    """

    message = "Please verify your email!"

    def has_permission(self, request, view):
        if request.user.is_anonymous:
            return True

        return EmailAddress.objects.filter(
            user=request.user,
            verified=True
        ).exists()
        
