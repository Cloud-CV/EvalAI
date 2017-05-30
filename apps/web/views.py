from django.contrib.auth.models import User
from django.shortcuts import render

from .models import Team

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .serializers import ContactSerializer, TeamSerializer


def home(request, template_name="index.html"):
    """
    Home Page View
    """
    return render(request, template_name)


def page_not_found(request):
    response = render(request, 'error404.html',
                      )
    response.status_code = 404
    return response


def internal_server_error(request):
    response = render(request, 'error500.html',
                      )
    response.status_code = 500
    return response


@throttle_classes([AnonRateThrottle, ])
@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def contact_us(request):
    user_does_not_exist = False
    try:
        user = User.objects.get(username=request.user)
        name = user.username
        email = user.email
        request_data = {'name': name, 'email': email}
    except:
        request_data = request.data
        user_does_not_exist = True

    if request.method == 'POST' or user_does_not_exist:
        if request.POST.get('message'):
            request_data['message'] = request.POST.get('message')
        serializer = ContactSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
            response_data = {'message': 'We have received your request and will contact you shortly.'}
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'GET':
        response_data = {"name": name, "email": email}
        return Response(response_data, status=status.HTTP_200_OK)


@throttle_classes([AnonRateThrottle])
@api_view(['GET', 'POST'])
@permission_classes((permissions.AllowAny,))
def our_team(request):
    if request.method == 'GET':
        teams = Team.objects.all()
        serializer = TeamSerializer(teams, many=True, context={'request': request})
        response_data = serializer.data
        return Response(response_data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        # team_type is set to Team.CONTRIBUTOR by default and can be overridden by the requester
        request.data['team_type'] = request.data.get('team_type', Team.CONTRIBUTOR)
        serializer = TeamSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_data = {'message', 'Successfully added the contributor.'}
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
