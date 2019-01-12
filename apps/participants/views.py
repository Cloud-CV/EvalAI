from django.contrib.auth.models import User

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework.response import Response
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,)
from rest_framework.throttling import UserRateThrottle

from accounts.permissions import HasVerifiedEmail
from base.utils import paginated_queryset
from challenges.models import Challenge
from challenges.serializers import ChallengeSerializer
from hosts.utils import is_user_a_host_of_challenge

from .models import (Participant, ParticipantTeam)
from .serializers import (InviteParticipantToTeamSerializer,
                          ParticipantTeamSerializer,
                          ChallengeParticipantTeam,
                          ChallengeParticipantTeamList,
                          ChallengeParticipantTeamListSerializer,
                          ParticipantTeamDetailSerializer,)
from .utils import (get_list_of_challenges_for_participant_team,
                    get_list_of_challenges_participated_by_a_user,
                    is_user_part_of_participant_team,)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def participant_team_list(request):

    if request.method == 'GET':
        participant_teams_id = Participant.objects.filter(user_id=request.user).values_list('team_id', flat=True)
        participant_teams = ParticipantTeam.objects.filter(
            id__in=participant_teams_id).order_by('-id')
        paginator, result_page = paginated_queryset(participant_teams, request)
        serializer = ParticipantTeamDetailSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == 'POST':
        serializer = ParticipantTeamSerializer(data=request.data,
                                               context={'request': request})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            participant_team = serializer.instance
            participant = Participant(user=request.user,
                                      status=Participant.SELF,
                                      team=participant_team)
            participant.save()
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_participant_team_challenge_list(request, participant_team_pk):
    """
    Returns a challenge list in which the participant team has participated.
    """
    try:
        participant_team = ParticipantTeam.objects.get(
            pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'Participant Team does not exist'}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        challenge = Challenge.objects.filter(participant_teams=participant_team).order_by('-id')
        paginator, result_page = paginated_queryset(challenge, request)
        serializer = ChallengeSerializer(
            result_page, many=True, context={'request': request})
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)


@throttle_classes([UserRateThrottle])
@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def participant_team_detail(request, pk):

    try:
        participant_team = ParticipantTeam.objects.get(pk=pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        serializer = ParticipantTeamDetailSerializer(participant_team)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:

        if request.method == 'PATCH':
            serializer = ParticipantTeamSerializer(participant_team, data=request.data,
                                                   context={
                                                       'request': request},
                                                   partial=True)
        else:
            serializer = ParticipantTeamSerializer(participant_team, data=request.data,
                                                   context={'request': request})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        participant_team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@throttle_classes([UserRateThrottle])
@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def invite_participant_to_team(request, pk):
    try:
        participant_team = ParticipantTeam.objects.get(pk=pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'Participant Team does not exist'}
        return Response(response_data, status=status.HTTP_404_NOT_FOUND)

    if not is_user_part_of_participant_team(request.user, participant_team):
        response_data = {'error': 'You are not a member of this team!'}
        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        response_data = {
            'error': 'User does not exist with this email address!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    participant = Participant.objects.filter(team=participant_team, user=user)
    if participant.exists():
        response_data = {'error': 'User is already part of the team!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    invited_user_participated_challenges = get_list_of_challenges_participated_by_a_user(
        user).values_list("id", flat=True)
    team_participated_challenges = get_list_of_challenges_for_participant_team(
        [participant_team]).values_list("id", flat=True)

    if set(invited_user_participated_challenges) & set(team_participated_challenges):
        """
        Check if the user has already participated in
        challenges where the inviting participant has participated.
        If this is the case, then the user cannot be invited since
        he cannot participate in a challenge via two teams.
        """
        response_data = {
            'error': 'Sorry, the invited user has already participated'
            ' in atleast one of the challenges which you are already a'
            ' part of. Please try creating a new team and then invite.'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    serializer = InviteParticipantToTeamSerializer(
        data=request.data,
        context={
            'participant_team': participant_team,
            'request': request})

    if serializer.is_valid():
        serializer.save()
        response_data = {
            'message': 'User has been successfully added to the team!'}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([UserRateThrottle])
@api_view(['DELETE'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def delete_participant_from_team(request, participant_team_pk, participant_pk):
    """
    Deletes a participant from a Participant Team
    """
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant = Participant.objects.get(pk=participant_pk)
    except Participant.DoesNotExist:
        response_data = {'error': 'Participant does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if participant_team.created_by == request.user:

        if participant.user == request.user:  # when the user tries to remove himself
            response_data = {
                'error': 'You are not allowed to remove yourself since you are admin. Please delete the team if you want to do so!'}  # noqa: ignore=E501
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            participant.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        response_data = {
            'error': 'Sorry, you do not have permissions to remove this participant'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)


@throttle_classes([UserRateThrottle])
@api_view(['GET', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_teams_and_corresponding_challenges_for_a_participant(request, challenge_pk):
    """
    Returns list of teams and corresponding challenges for a participant
    """
    # first get list of all the participants and teams related to the user
    participant_objs = Participant.objects.filter(user=request.user).prefetch_related('team')

    is_challenge_host = is_user_a_host_of_challenge(user=request.user, challenge_pk=challenge_pk)

    challenge_participated_teams = []
    for participant_obj in participant_objs:
        participant_team = participant_obj.team

        challenges = Challenge.objects.filter(
            participant_teams=participant_team)

        if challenges.count():
            for challenge in challenges:
                challenge_participated_teams.append(ChallengeParticipantTeam(
                    challenge, participant_team))
        else:
            challenge = None
            challenge_participated_teams.append(ChallengeParticipantTeam(
                challenge, participant_team))
    serializer = ChallengeParticipantTeamListSerializer(ChallengeParticipantTeamList(challenge_participated_teams))
    response_data = serializer.data
    response_data['is_challenge_host'] = is_challenge_host
    return Response(response_data, status=status.HTTP_200_OK)


@throttle_classes([UserRateThrottle])
@api_view(['DELETE', ])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def remove_self_from_participant_team(request, participant_team_pk):
    """
    A user can remove himself from the participant team.
    """
    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant = Participant.objects.get(user=request.user, team=participant_team)
    except Participant.DoesNotExist:
        response_data = {'error': 'Sorry, you do not belong to this team!'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)

    if get_list_of_challenges_for_participant_team([participant_team]).exists():
        response_data = {'error': 'Sorry, you cannot delete this team since it has taken part in challenge(s)!'}
        return Response(response_data, status=status.HTTP_403_FORBIDDEN)
    else:
        participant.delete()
        participants = Participant.objects.filter(team=participant_team)
        if participants.count() == 0:
            participant_team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
