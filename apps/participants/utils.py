from base.utils import get_model_object
from challenges.models import Challenge

from .models import Participant, ParticipantTeam

get_participant_team_model = get_model_object(ParticipantTeam)


def is_user_part_of_participant_team(user, participant_team):
    """Returns boolean if the user belongs to the participant team or not.

    Parameters:
        user (User): User object
        participant_team (ParticipantTeam): ParticipantTeam object

    Returns:
        bool: True if user is part of the team, False otherwise
    """
    return Participant.objects.filter(
        user=user, team=participant_team
    ).exists()


def has_participant_team_participated_in_challenge(
    participant_team_id, challenge_id
):
    """Returns boolean if the Participant Team
    participated in particular Challenge.

    Parameters:
        participant_team_id (int): ID of the participant team
        challenge_id (int): ID of the challenge

    Returns:
        bool: True if team participated in the challenge, False otherwise
    """
    return Challenge.objects.filter(
        pk=challenge_id,
        participant_team__id=participant_team_id
    ).exists()


def get_participant_teams_for_user(user):
    """Returns participant team ids for a particular user.

    Parameters:
        user (User): User object

    Returns:
        QuerySet: List of team IDs the user belongs to
    """
    return (Participant.objects.
            filter(user=user).values_list("team", flat=True))


def is_user_creator_of_participant_team(user, participant_team):
    """Returns boolean if a user is the creator of participant team.

    Parameters:
        user (User): User object
        participant_team (ParticipantTeam): ParticipantTeam object

    Returns:
        bool: True if user is the creator of the team, False otherwise
    """
    return participant_team.created_by.pk == user.pk


def has_user_participated_in_challenge(user, challenge_id):
    """Returns boolean if the user has participated in a particular challenge.

    Parameters:
        user (User): User object
        challenge_id (int): ID of the challenge

    Returns:
        bool: True if user participated in the challenge, False otherwise
    """
    participant_teams = get_participant_teams_for_user(user)
    return Challenge.objects.filter(
        pk=challenge_id, participant_teams__in=participant_teams
    ).exists()


def get_participant_team_id_of_user_for_a_challenge(user, challenge_id):
    """Returns the participant team id for a particular
    user for a particular challenge.

    Parameters:
        user (User): User object
        challenge_id (int): ID of the challenge

    Returns:
        int or None: ID of the participant team if found, None otherwise
    """
    participant_teams = get_participant_teams_for_user(user)
    for participant_team in participant_teams:
        if Challenge.objects.filter(
            pk=challenge_id, participant_teams=participant_team
        ).exists():
            return participant_team
    return None


def get_participant_team_of_user_for_a_challenge(user, challenge_id):
    """Returns the participant team object for a particular
    user for a particular challenge.

    Parameters:
        user (User): User object
        challenge_id (int): ID of the challenge

    Returns:
        ParticipantTeam or None: Team object if found, None otherwise
    """
    participant_team_id = get_participant_team_id_of_user_for_a_challenge(
        user, challenge_id
    )
    if participant_team_id:
        return ParticipantTeam.objects.get(pk=participant_team_id)
    return None


def get_list_of_challenges_for_participant_team(participant_teams=None):
    """Returns list of challenges participated by a team.

    Parameters:
        participant_teams (list, optional): List of participant team objects

    Returns:
        QuerySet: Challenges the teams participated in
    """
    if participant_teams is None:
        participant_teams = []
    return Challenge.objects.filter(participant_teams__in=participant_teams)


def get_list_of_challenges_participated_by_a_user(user):
    """Returns list of challenges participated by a user.

    Parameters:
        user (User): User object

    Returns:
        QuerySet: Challenges the user participated in
    """
    participant_teams = get_participant_teams_for_user(user)
    return get_list_of_challenges_for_participant_team(participant_teams)
