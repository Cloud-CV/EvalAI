from .models import ChallengeHost


def get_challenge_host_teams_for_user(user):
    """Returns challenge host team ids for a particular user"""
    return ChallengeHost.objects.filter(user=user).values_list('team_name', flat=True)
