from base.utils import get_model_object
from challenges.models import Challenge
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import six
from .serializers import InviteHostToTeamSerializer
from .models import ChallengeHost, ChallengeHostTeam


class TokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user_data, timestamp):
        """Custom Token Generator for Host Invitations"""
        user = user_data['user']
        challenge_host_team = user_data['challenge_host_team']
        return (
            six.text_type(user.pk) + six.text_type(timestamp) + six.text_type(challenge_host_team.pk)
        )


def get_challenge_host_teams_for_user(user):
    """Returns challenge host team ids for a particular user"""
    return ChallengeHost.objects.filter(user=user).values_list(
        "team_name", flat=True
    )


def is_user_a_host_of_challenge(user, challenge_pk):
    """Returns boolean if the user is host of a challenge."""
    if user.is_anonymous():
        return False
    challenge_host_teams = get_challenge_host_teams_for_user(user)
    return Challenge.objects.filter(
        pk=challenge_pk, creator_id__in=challenge_host_teams
    ).exists()


def is_user_part_of_host_team(user, host_team):
    """Returns boolean if the user belongs to the host team or not"""
    return ChallengeHost.objects.filter(
        user=user, team_name=host_team
    ).exists()


def add_user_to_host_team(request, challenge_host_team):
    serializer = InviteHostToTeamSerializer(
        data=request.data,
        context={
            "challenge_host_team": challenge_host_team,
            "request": request,
        },
    )

    if serializer.is_valid():
        serializer.save()
        response_data = {
            "message": "User has been added successfully to the host team"
        }
        return True
    return False


get_challenge_host_team_model = get_model_object(ChallengeHostTeam)
host_invitations_token_generator = TokenGenerator()
