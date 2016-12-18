from django.conf import settings
from django.shortcuts import render
from django.utils import timezone

from rest_framework import permissions, status
from rest_framework.authentication import (TokenAuthentication,)
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from accounts.permissions import HasVerifiedEmail
from hosts.models import ChallengeHostTeam
from participants.models import ParticipantTeam

from .models import Challenge
from .permissions import IsChallengeCreator
from .serializers import ChallengeSerializer


@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((TokenAuthentication,))
def challenge_list(request, challenge_host_team_pk):
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(pk=challenge_host_team_pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {'error': 'ChallengeHostTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        challenge = Challenge.objects.filter(creator=challenge_host_team)
        paginator = PageNumberPagination()
        paginator.page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
        result_page = paginator.paginate_queryset(challenge, request)
        serializer = ChallengeSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == 'POST':
        serializer = ChallengeSerializer(data=request.data,
                                         context={'challenge_host_team': challenge_host_team})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail, IsChallengeCreator))
@authentication_classes((TokenAuthentication,))
def challenge_detail(request, challenge_host_team_pk, pk):
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(pk=challenge_host_team_pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {'error': 'ChallengeHostTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        challenge = Challenge.objects.get(pk=pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    if request.method == 'GET':
        serializer = ChallengeSerializer(challenge)
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)

    elif request.method in ['PUT', 'PATCH']:
        if request.method == 'PATCH':
            serializer = ChallengeSerializer(challenge,
                                             data=request.data,
                                             context={'challenge_host_team': challenge_host_team},
                                             partial=True)
        else:
            serializer = ChallengeSerializer(challenge,
                                             data=request.data,
                                             context={'challenge_host_team': challenge_host_team})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        challenge.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((TokenAuthentication,))
def add_participant_team_to_challenge(request, challenge_pk, participant_team_pk):

    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    try:
        participant_team = ParticipantTeam.objects.get(pk=participant_team_pk)
    except ParticipantTeam.DoesNotExist:
        response_data = {'error': 'ParticipantTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge.participant_teams.add(participant_team)
    return Response(status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((TokenAuthentication,))
def disable_challenge(request, pk):

    try:
        challenge = Challenge.objects.get(pk=pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    challenge_host_team = challenge.creator

    if challenge_host_team.created_by == request.user:
        challenge.is_disabled = True
        challenge.save()
        return Response(status=status.HTTP_204_NO_CONTENT)
    else:
        response_data = {
            'error': 'Sorry, you do not have permission to disable this challenge'}
        return Response(response_data, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['GET'])
def get_all_challenges(request, challenge_time):
    """
    Returns the list of all challenges
    """
    try:
        q_params = {'published': True}
        if challenge_time.lower() == "past":
            q_params['end_date__lt'] = timezone.now()

        elif challenge_time.lower() == "present":
            q_params['start_date__lt'] = timezone.now()
            q_params['end_date__gt'] = timezone.now()

        elif challenge_time.lower() == "future":
            q_params['start_date__gt'] = timezone.now()

        challenge = Challenge.objects.filter(**q_params)
        paginator = PageNumberPagination()
        paginator.page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
        result_page = paginator.paginate_queryset(challenge, request)
        serializer = ChallengeSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)
    except:
        response_data = {'error': 'Wrong url pattern!'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)
