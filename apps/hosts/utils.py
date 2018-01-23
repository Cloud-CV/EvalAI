from base.utils import get_model_object
from challenges.models import Challenge

from .models import ChallengeHost, ChallengeHostTeam


def get_challenge_host_teams_for_user(user):
    """Returns challenge host team ids for a particular user"""
    return ChallengeHost.objects.filter(user=user).values_list('team_name', flat=True)


def is_user_a_host_of_challenge(user, challenge_pk):
    """Returns boolean if the user is host of a challenge."""
    challenge_host_teams = get_challenge_host_teams_for_user(user)
    return Challenge.objects.filter(pk=challenge_pk, creator_id__in=challenge_host_teams).exists()


def get_list_of_challenges_for_challenge_host_team(challenge_host_teams=[]):
    """Returns list of challenges by a host team"""
    return Challenge.objects.filter(creator__in=challenge_host_teams)


def get_list_of_challenges_participated_by_a_user(user):
    """Returns list of challenges participated by a user"""
    challenge_host_teams = get_challenge_host_teams_for_user(user)
    return get_list_of_challenges_for_challenge_host_team(challenge_host_teams)


get_challenge_host_team_model = get_model_object(ChallengeHostTeam)
