from base.utils import get_model_object

from .models import ChallengeHost, ChallengeHostTeam


def get_challenge_host_teams_for_user(user):
    """Returns challenge host team ids for a particular user"""
    return ChallengeHost.objects.filter(user=user).values_list('team_name', flat=True)

get_challenge_host_team_model = get_model_object(ChallengeHostTeam)
