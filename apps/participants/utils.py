from challenges.models import Challenge

from base.utils import get_model_object
from .models import Participant, ParticipantTeam

get_participant_team_model = get_model_object(ParticipantTeam)


def is_user_part_of_participant_team(user, participant_team):
    """Returns boolean if the user belongs to the participant team or not"""
    return Participant.objects.filter(
        user=user, team=participant_team
    ).exists()


def has_participant_team_participated_in_challenge(
    participant_team_id, challenge_id
):
    """Returns boolean if the Participant Team participated in particular Challenge"""
    return Challenge.objects.filter(
        pk=challenge_id, participant_team__id=participant_team_id
    ).exists()


def get_participant_teams_for_user(user):
    """Returns participant team ids for a particular user"""
    return Participant.objects.filter(user=user).values_list("team", flat=True)


def has_user_participated_in_challenge(user, challenge_id):
    """Returns boolean if the user has participated in a particular challenge"""
    participant_teams = get_participant_teams_for_user(user)
    return Challenge.objects.filter(
        pk=challenge_id, participant_teams__in=participant_teams
    ).exists()


def get_participant_team_id_of_user_for_a_challenge(user, challenge_id):
    """Returns the participant team id for a particular user for a particular challenge"""
    participant_teams = get_participant_teams_for_user(user)
    for participant_team in participant_teams:
        if Challenge.objects.filter(
            pk=challenge_id, participant_teams=participant_team
        ).exists():
            return participant_team
    return


def get_participant_team_of_user_for_a_challenge(user, challenge_id):
    """Returns the participant team object for a particular user for a particular challenge"""
    # TODO: Remove other functions and use this function
    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        user, challenge_id
    )
    if participant_team_id:
        return ParticipantTeam.objects.get(pk=participant_team_id)
    return


def get_list_of_challenges_for_participant_team(participant_teams=[]):
    """Returns list of challenges participated by a team"""
    return Challenge.objects.filter(participant_teams__in=participant_teams)


def get_list_of_challenges_participated_by_a_user(user):
    """Returns list of challenges participated by a user"""
    participant_teams = get_participant_teams_for_user(user)
    return get_list_of_challenges_for_participant_team(participant_teams)
