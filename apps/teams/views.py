from django.conf import settings
from django.shortcuts import render

from rest_framework import permissions, status
from rest_framework.authentication import (TokenAuthentication,)
from rest_framework.decorators import (api_view,
                                       authentication_classes,
                                       permission_classes,)
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from challenges.models import Challenge

from .models import Team
from .serializers import TeamChallengeSerializer


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((TokenAuthentication,))
def team_list(request, challenge_pk):

    try:
        challenge = Challenge.objects.get(pk=challenge_pk)
    except Challenge.DoesNotExist:
        response_data = {'error': 'Challenge does not exist'}
        return Response(response_data, status=status.HTTP_406_NOT_ACCEPTABLE)

    teams = Team.objects.filter(challenge=challenge)
    paginator = PageNumberPagination()
    paginator.page_size = settings.REST_FRAMEWORK['PAGE_SIZE']
    result_page = paginator.paginate_queryset(teams, request)
    serializer = TeamChallengeSerializer(result_page, many=True)
    response_data = serializer.data
    return paginator.get_paginated_response(response_data)
