from base.utils import get_model_object, is_user_a_staff
from challenges.models import Challenge

from .models import ChallengeHost, ChallengeHostTeam


def get_challenge_host_teams_for_user(user):
    """Returns challenge host team ids for a particular user"""
    return ChallengeHost.objects.filter(user=user).values_list(
        "team_name", flat=True
    )


def is_user_a_host_of_challenge(user, challenge_pk):
    """Returns boolean if the user is host of a challenge."""
    if user.is_anonymous:
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


def is_user_a_staff_or_host(user, challenge_pk):
    """
    Function to check if a user is staff or host

    Args:
        user ([User Class Object]): User model class object
        challenge_pk ([int]): Challenge primary key

    Return:
        {bool} : True/False if the user is staff or host
    """
    return is_user_a_staff(user) or is_user_a_host_of_challenge(user, challenge_pk)


get_challenge_host_team_model = get_model_object(ChallengeHostTeam)
