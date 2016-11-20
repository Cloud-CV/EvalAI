from django.conf import settings
from django.shortcuts import render

from rest_framework import permissions, status
from rest_framework.authentication import (TokenAuthentication,)
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from .models import (ChallengeHostTeam,)
from .serializers import (ChallengeHostTeamSerializer,)


@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def challenge_host_team_list(request):

    if request.method == 'GET':
        challenge_host_teams = ChallengeHostTeam.objects.filter(created_by=request.user)
        paginator = PageNumberPagination()
        paginator.page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
        result_page = paginator.paginate_queryset(challenge_host_teams, request)
        serializer = ChallengeHostTeamSerializer(result_page, many=True)
        response_data = serializer.data
        return paginator.get_paginated_response(response_data)

    elif request.method == 'POST':
        serializer = ChallengeHostTeamSerializer(data=request.data,
                                                 context={'request': request})
        if serializer.is_valid():
            serializer.save()
            response_data = serializer.data
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def challenge_host_team_detail(request, pk):
    try:
        challenge_host_team = ChallengeHostTeam.objects.get(pk=pk)
    except ChallengeHostTeam.DoesNotExist:
        response_data = {'error': 'ChallengeHostTeam does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    serializer = ChallengeHostTeamSerializer(challenge_host_team)
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)
