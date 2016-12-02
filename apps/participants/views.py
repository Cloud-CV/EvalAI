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

from challenges.models import Challenge

from .models import ParticipantTeam
from .serializers import ParticipantTeamSerializer


@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def participant_team_list(request, challenge_pk):

    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        participant_teams = ParticipantTeam.objects.filter(challenge=challenge)
        paginator = PageNumberPagination()
        paginator.page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
        result_page = paginator.paginate_queryset(participant_teams, request)
        serializer = ParticipantTeamSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == 'POST':
        serializer = ParticipantTeamSerializer(data=request.data,
                                               context={'challenge': challenge})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def participant_team_detail(request, challenge_pk, pk):
    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

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
                                                   context={'challenge': challenge}, partial=True)
        else:
            serializer = ParticipantTeamSerializer(participant_team, data=request.data,
                                                   context={'challenge': challenge})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        participant_team.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
