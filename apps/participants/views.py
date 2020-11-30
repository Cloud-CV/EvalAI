from django.contrib.auth.models import User

from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
)
from rest_framework.response import Response
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import HasVerifiedEmail
from base.utils import team_paginated_queryset
from challenges.models import Challenge, ChallengePhase
from challenges.serializers import ChallengeSerializer
from challenges.utils import (
    get_challenge_model,
    get_participant_model,
    is_user_in_allowed_email_domains,
    is_user_in_blocked_email_domains,
)
from jobs.models import Submission
from hosts.utils import is_user_a_host_of_challenge
from .filters import ParticipantTeamsFilter
from .models import Participant, ParticipantTeam
from .serializers import (
    InviteParticipantToTeamSerializer,
    ParticipantTeamSerializer,
    ChallengeParticipantTeam,
    ChallengeParticipantTeamList,
    ChallengeParticipantTeamListSerializer,
    ParticipantTeamDetailSerializer,
)
from .utils import (
    get_list_of_challenges_for_participant_team,
    get_list_of_challenges_participated_by_a_user,
    get_participant_team_of_user_for_a_challenge,
    has_user_participated_in_challenge,
    is_user_part_of_participant_team,
)


@api_view(["GET", "POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def participant_team_list(request):

    if request.method == "GET":
        participant_teams_id = Participant.objects.filter(
            user_id=request.user
        ).values_list("team_id", flat=True)
        participant_teams = ParticipantTeam.objects.filter(
            id__in=participant_teams_id
        ).order_by("-id")
        filtered_teams = ParticipantTeamsFilter(
            request.GET, queryset=participant_teams
        )
        paginator, result_page = team_paginated_queryset(
            filtered_teams.qs, request
        )
        serializer = ParticipantTeamDetailSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == "POST":
        serializer = ParticipantTeamSerializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            participant_team = serializer.instance
            participant = Participant(
                user=request.user,
                status=Participant.SELF,
                team=participant_team,
            )
            participant.save()
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_participant_team_challenge_list(request, participant_team_pk):
    """
    Returns a challenge list in which the participant team has participated.
    """
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "Participant Team does not exist"}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        challenge = Challenge.objects.filter(
            participant_teams=participant_team
        ).order_by("-id")
        paginator, result_page = team_paginated_queryset(challenge, request)
        serializer = ChallengeSerializer(
            result_page, many=True, context={"request": request}
        )
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)


@api_view(["GET", "PUT", "PATCH", "DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def participant_team_detail(request, pk):

    try:
        participant_team = ParticipantTeam.objects.get(pk=pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "ParticipantTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == "GET":
        serializer = ParticipantTeamDetailSerializer(participant_team)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ["PUT", "PATCH"]:

        if request.method == "PATCH":
            serializer = ParticipantTeamSerializer(
                participant_team,
                data=request.data,
                context={"request": request},
                partial=True,
            )
        else:
            serializer = ParticipantTeamSerializer(
                participant_team,
                data=request.data,
                context={"request": request},
            )
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

    elif request.method == "DELETE":
        participant_team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def invite_participant_to_team(request, pk):
    try:
        participant_team = ParticipantTeam.objects.get(pk=pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "Participant Team does not exist"}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    if not is_user_part_of_participant_team(request.user, participant_team):
        response_data = {"error": "You are not a member of this team!"}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    email = request.data.get("email")
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data = {
            "error": "User does not exist with this email address!"
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    participant = Participant.objects.filter(team=participant_team, user=user)
    if participant.exists():
        response_data = {"error": "User is already part of the team!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    invited_user_participated_challenges = get_list_of_challenges_participated_by_a_user(
        user
    ).values_list(
        "id", flat=True
    )
    team_participated_challenges = get_list_of_challenges_for_participant_team(
        [participant_team]
    ).values_list("id", flat=True)

    if set(invited_user_participated_challenges) & set(
        team_participated_challenges
    ):
        """
        Check if the user has already participated in
        challenges where the inviting participant has participated.
        If this is the case, then the user cannot be invited since
        he cannot participate in a challenge via two teams.
        """
        response_data = {
            "error": "Sorry, the invited user has already participated"
            " in atleast one of the challenges which you are already a"
            " part of. Please try creating a new team and then invite."
        }
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if len(team_participated_challenges) > 0:
        for challenge_pk in team_participated_challenges:
            challenge = get_challenge_model(challenge_pk)

            if len(challenge.banned_email_ids) > 0:
                # Check if team participants emails are banned
                for (
                    participant_email
                ) in participant_team.get_all_participants_email():
                    if participant_email in challenge.banned_email_ids:
                        message = "You cannot invite as you're a part of {} team and it has been banned "
                        "from this challenge. Please contact the challenge host."
                        response_data = {
                            "error": message.format(participant_team.team_name)
                        }
                        return Response(
                            response_data,
                            status=status.HTTP_406_NOT_ACCEPTABLE,
                        )

                # Check if invited user is banned
                if email in challenge.banned_email_ids:
                    message = "You cannot invite as the invited user has been banned "
                    "from this challenge. Please contact the challenge host."
                    response_data = {"error": message}
                    return Response(
                        response_data, status=status.HTTP_406_NOT_ACCEPTABLE
                    )

            # Check if user is in allowed list.
            if len(challenge.allowed_email_domains) > 0:
                if not is_user_in_allowed_email_domains(email, challenge_pk):
                    message = "Sorry, users with {} email domain(s) are only allowed to participate in this challenge."
                    domains = ""
                    for domain in challenge.allowed_email_domains:
                        domains = "{}{}{}".format(domains, "/", domain)
                    domains = domains[1:]
                    response_data = {"error": message.format(domains)}
                    return Response(
                        response_data, status=status.HTTP_406_NOT_ACCEPTABLE
                    )

            # Check if user is in blocked list.
            if is_user_in_blocked_email_domains(email, challenge_pk):
                message = "Sorry, users with {} email domain(s) are not allowed to participate in this challenge."
                domains = ""
                for domain in challenge.blocked_email_domains:
                    domains = "{}{}{}".format(domains, "/", domain)
                domains = domains[1:]
                response_data = {"error": message.format(domains)}
                return Response(
                    response_data, status=status.HTTP_406_NOT_ACCEPTABLE
                )

    serializer = InviteParticipantToTeamSerializer(
        data=request.data,
        context={"participant_team": participant_team, "request": request},
    )

    if serializer.is_valid():
        serializer.save()
        response_data = {
            "message": "User has been successfully added to the team!"
        }
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(["DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def delete_participant_from_team(request, participant_team_pk, participant_pk):
    """
    Deletes a participant from a Participant Team
    """
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "ParticipantTeam does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant = Participant.objects.get(pk=participant_pk)
    except Participant.DoesNotExist:
        response_data = {"error": "Participant does not exist"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if participant_team.created_by == request.user:

        if (
            participant.user == request.user
        ):  # when the user tries to remove himself
            response_data = {
                "error": "You are not allowed to remove yourself since you are admin. Please delete the team if you want to do so!"
            }  # noqa: ignore=E501
            return Response(
                response_data, status=status.HTTP_406_NOT_ACCEPTABLE
            )
        else:
            participant.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        response_data = {
            "error": "Sorry, you do not have permissions to remove this participant"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_teams_and_corresponding_challenges_for_a_participant(
    request, challenge_pk
):
    """
    Returns list of teams and corresponding challenges for a participant
    """
    # first get list of all the participants and teams related to the user
    participant_objs = Participant.objects.filter(
        user=request.user
    ).prefetch_related("team")

    is_challenge_host = is_user_a_host_of_challenge(
        user=request.user, challenge_pk=challenge_pk
    )

    challenge_participated_teams = []
    for participant_obj in participant_objs:
        participant_team = participant_obj.team

        challenges = Challenge.objects.filter(
            participant_teams=participant_team
        )

        if challenges.count():
            for challenge in challenges:
                challenge_participated_teams.append(
                    ChallengeParticipantTeam(challenge, participant_team)
                )
        else:
            challenge = None
            challenge_participated_teams.append(
                ChallengeParticipantTeam(challenge, participant_team)
            )
    serializer = ChallengeParticipantTeamListSerializer(
        ChallengeParticipantTeamList(challenge_participated_teams)
    )
    response_data = serializer.data
    response_data["is_challenge_host"] = is_challenge_host
    return Response(response_data, status=status.HTTP_200_OK)


@api_view(["DELETE"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def remove_self_from_participant_team(request, participant_team_pk):
    """
    A user can remove himself from the participant team.
    """
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {"error": "ParticipantTeam does not exist!"}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant = Participant.objects.get(
            user=request.user, team=participant_team
        )
    except Participant.DoesNotExist:
        response_data = {"error": "Sorry, you do not belong to this team!"}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    if get_list_of_challenges_for_participant_team(
        [participant_team]
    ).exists():
        response_data = {
            "error": "Sorry, you cannot delete this team since it has taken part in challenge(s)!"
        }
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)
    else:
        participant.delete()
        participants = Participant.objects.filter(team=participant_team)
        if participants.count() == 0:
            participant_team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_participant_team_details_for_challenge(request, challenge_pk):
    """
    API to get the participant team detail

    Arguments:
        request {HttpRequest} -- The request object
        challenge_pk {[int]} -- Challenge primary key

    Returns:
        {dict} -- Participant team detail that has participated in the challenge
    """

    challenge = get_challenge_model(challenge_pk)
    if has_user_participated_in_challenge(request.user, challenge_pk):
        participant_team = get_participant_team_of_user_for_a_challenge(
            request.user, challenge_pk
        )
        serializer = ParticipantTeamSerializer(participant_team)
        return Response(serializer.data, status=status.HTTP_200_OK)
    else:
        response_data = {
            "error": f"The user {request.user.username} has not participanted in {challenge.title}"
        }
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def remove_participant_team_from_challenge(
    request, challenge_pk, participant_team_pk
):
    """
    API to remove the participant team from a challenge

    Arguments:
        request {HttpRequest} -- The request object
        challenge_pk {[int]} -- Challenge primary key
        participant_team_pk {[int]} -- Participant team primary key

    Returns:
        Response Object -- An object containing api response
    """
    challenge = get_challenge_model(challenge_pk)

    participant_team = get_participant_model(participant_team_pk)

    if participant_team.created_by == request.user:
        if participant_team.challenge_set.filter(id=challenge_pk).exists():
            challenge_phases = ChallengePhase.objects.filter(
                challenge=challenge
            )
            for challenge_phase in challenge_phases:
                submissions = Submission.objects.filter(
                    participant_team=participant_team_pk,
                    challenge_phase=challenge_phase,
                )
                if submissions.count() > 0:
                    response_data = {
                        "error": "Unable to remove team as you have already made submission to the challenge"
                    }
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

            challenge.participant_teams.remove(participant_team)
            return Response(status=status.HTTP_200_OK)
        else:
            response_data = {"error": "Team has not participated in the challenge"}
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
    else:
        response_data = {
            "error": "Sorry, you do not have permissions to remove this participant team"
        }
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
