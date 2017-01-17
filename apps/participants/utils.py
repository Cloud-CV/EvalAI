from challenges.models import Challenge

from .models import Participant


def is_user_part_of_participant_team(user, participant_team_id):
    """Returns boolean if the user belongs to the participant team or not"""
    return Participant.objects.filter(user=user, team__id=participant_team_id).exists()


def has_participant_team_participated_in_challenge(participant_team_id, challenge_id):
    """Returns boolean if the Participant Team participated in particular Challenge"""
    return Challenge.objects.filter(pk=challenge_id, participant_team__id=participant_team_id).exists()


def get_participant_teams_for_user(user):
    """Returns participant team ids for a particular user"""
    return Participant.objects.filter(user=user).values_list('team', flat=True)


def has_user_participated_in_challenge(user, challenge_id):
    """Returns boolean if the user has participated in a particular challenge"""
    participant_teams = get_participant_teams_for_user(user)
    return Challenge.objects.filter(pk=challenge_id, participant_teams__in=participant_teams).exists()


def get_participant_team_id_of_user_for_a_challenge(user, challenge_id):
    """Returns the participant team object for a particular user for a particular challenge"""
    participant_teams = get_participant_teams_for_user(user)
    for participant_team in participant_teams:
        if Challenge.objects.filter(pk=challenge_id, participant_teams=participant_team).exists():
            return participant_team
    return None
