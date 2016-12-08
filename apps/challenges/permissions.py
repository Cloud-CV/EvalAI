from rest_framework import permissions

from .models import Challenge
from .serializers import ChallengeSerializer


class IsChallengeCreator(permissions.BasePermission):
    """
    Permission class for edit/delete a challenge.
    """

    def has_permission(self, request, view):

        if request.method in permissions.SAFE_METHODS:
            return True
        elif request.method in ['DELETE', 'PATCH', 'PUT']:
            challenge = Challenge.objects.get(pk=request.parser_context['kwargs']['pk'])
            if request.user.id == challenge.creator.created_by.id:
                return True
            else:
                return False
        else:
            return False
