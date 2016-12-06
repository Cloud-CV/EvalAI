from django.conf import settings
from django.shortcuts import render

from rest_framework import permissions, status
from rest_framework.authentication import (TokenAuthentication,)
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,
                                       renderer_classes,)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework import response, schemas

from accounts.permissions import HasVerifiedEmail
from challenges.models import Challenge

from .models import (Participant, ParticipantTeam)
from .serializers import (InviteParticipantToTeamSerializer,
                          ParticipantTeamSerializer,)


@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((TokenAuthentication,))
def participant_team_list(request):

    if request.method == 'GET':
        participant_teams = ParticipantTeam.objects.filter(
            created_by=request.user)
        paginator = PageNumberPagination()
        paginator.page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
        result_page = paginator.paginate_queryset(participant_teams, request)
        serializer = ParticipantTeamSerializer(result_page, many=True)
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


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((TokenAuthentication,))
def participant_team_detail(request, pk):

    try:
        participant_team = ParticipantTeam.objects.get(pk=pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        serializer = ParticipantTeamSerializer(participant_team)
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


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((TokenAuthentication,))
def invite_participant_to_team(request, pk):

    try:
        participant_team = ParticipantTeam.objects.get(pk=pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    serializer = InviteParticipantToTeamSerializer(data=request.data,
                                                   context={'participant_team': participant_team,
                                                            'request': request})
    if serializer.is_valid():
        serializer.save()
        response_data = {
            'message': 'User has been added successfully to the team'}
        return Response(response_data, status=status.HTTP_202_ACCEPTED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((TokenAuthentication,))
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
                'error': 'You are not allowed to remove yourself since you are admin. Please delete the team if you want to do so!'} # noqa: ignore=E501
            return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
        else:
            participant.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        response_data = {
            'error': 'Sorry, you do not have permissions to remove this participant'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)
