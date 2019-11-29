from rest_framework import permissions

from .models import Challenge

from hosts.utils import is_user_a_host_of_challenge


class IsChallengeCreator(permissions.BasePermission):
    """
    Permission class for edit/delete a challenge.
    """

    message = "Sorry, you are not allowed to perform this operation!"

    def has_permission(self, request, view):

        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.method in ["DELETE", "PATCH", "PUT", "POST"]:
            try:
                challenge = Challenge.objects.get(
                    pk=request.parser_context["kwargs"]["challenge_pk"]
                )
            except Challenge.DoesNotExist:
                return False

            if request.user.id == challenge.creator.created_by.id:
                return True
            elif is_user_a_host_of_challenge(request.user, challenge.id):
                return True
            else:
                return False
        else:
            return False
