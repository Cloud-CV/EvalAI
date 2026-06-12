from base.utils import get_model_object
from challenges.models import Challenge
from hosts.models import ChallengeHost

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


def is_user_creator_of_participant_team(user, participant_team):
    """Returns boolean if a user is the creator of participant team"""
    return participant_team.created_by.pk == user.pk


def has_user_participated_in_challenge(user, challenge_id):
    """Returns boolean if the user has participated in a particular challenge"""
    participant_teams = get_participant_teams_for_user(user)
    return Challenge.objects.filter(
        pk=challenge_id, participant_teams__in=participant_teams
    ).exists()


def get_participant_team_id_of_user_for_a_challenge(user, challenge_id):
    """Returns the participant team id for a particular user for a particular challenge"""
    # Single query: find the user's participant team associated with this
    # challenge
    return (
        ParticipantTeam.objects.filter(
            participants__user=user, challenge=challenge_id
        )
        .values_list("pk", flat=True)
        .first()
    )


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


def get_participant_team_member_count(participant_team):
    """Returns the number of members in a participant team."""
    return Participant.objects.filter(team=participant_team).count()


def is_participant_team_exempt_from_max_members_for_challenge(
    participant_team, challenge
):
    """
    Returns True when every member of the participant team is a host of the
    challenge's organizing team (baseline/testing team exemption).
    """
    member_user_ids = list(
        Participant.objects.filter(team=participant_team).values_list(
            "user_id", flat=True
        )
    )
    if not member_user_ids:
        return False

    host_user_ids = set(
        ChallengeHost.objects.filter(
            team_name_id=challenge.creator_id,
            status__in=[ChallengeHost.ACCEPTED, ChallengeHost.SELF],
        ).values_list("user_id", flat=True)
    )
    return all(user_id in host_user_ids for user_id in member_user_ids)


def get_effective_max_team_members_for_team(participant_team):
    """
    Returns the strictest max_team_members limit among challenges the team
    has joined. Returns None when no limit applies.
    """
    challenges = get_list_of_challenges_for_participant_team(
        [participant_team]
    )
    limits = []
    for challenge in challenges.exclude(max_team_members__isnull=True):
        if is_participant_team_exempt_from_max_members_for_challenge(
            participant_team, challenge
        ):
            continue
        limits.append(challenge.max_team_members)
    limits = list(limits)
    if not limits:
        return None
    return min(limits)


def get_team_capacity_blocking_challenge_titles(participant_team):
    """
    Returns titles of joined challenges whose max_team_members limit the team
    has reached or exceeded.
    """
    member_count = get_participant_team_member_count(participant_team)
    return list(
        get_list_of_challenges_for_participant_team([participant_team])
        .exclude(max_team_members__isnull=True)
        .filter(max_team_members__lte=member_count)
        .values_list("title", flat=True)
    )


def team_can_add_member(participant_team):
    """Returns whether the team can invite or accept another member."""
    limit = get_effective_max_team_members_for_team(participant_team)
    if limit is None:
        return True
    return get_participant_team_member_count(participant_team) < limit


def team_exceeds_challenge_max_members(participant_team, challenge):
    """Returns whether the team exceeds a challenge's max team member limit."""
    if challenge.max_team_members is None:
        return False
    if is_participant_team_exempt_from_max_members_for_challenge(
        participant_team, challenge
    ):
        return False
    return (
        get_participant_team_member_count(participant_team)
        > challenge.max_team_members
    )


def has_participated_in_require_complete_profile_challenge(user):
    """
    Returns True if the user has participated in any active challenge that
    requires a complete profile. When True, profile fields (name, address,
    university) become read-only and cannot be edited. Once all such
    challenges have ended (end_date < now), profile fields become editable
    again.
    """
    from django.utils import timezone

    challenges = get_list_of_challenges_participated_by_a_user(user)
    return challenges.filter(
        require_complete_profile=True, end_date__gt=timezone.now()
    ).exists()
