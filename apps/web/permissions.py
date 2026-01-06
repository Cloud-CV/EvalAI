from rest_framework import permissions


class IsSuperUser(permissions.BasePermission):
    """
    Permission class to allow only superusers to access an endpoint.
    Used for admin-only operations like bulk email notifications.
    """

    message = "Only superusers are allowed to perform this operation."

    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.is_superuser
        )
