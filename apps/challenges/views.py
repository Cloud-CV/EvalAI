from django.conf import settings
from django.shortcuts import render

from rest_framework import permissions, status
from rest_framework.authentication import (TokenAuthentication,)
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from hosts.models import ChallengeHostTeam

from .models import Challenge
from .serializers import ChallengeSerializer


@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated,))
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
