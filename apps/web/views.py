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
@api_view(['POST', ])
@permission_classes((permissions.AllowAny,))
def contact_us(request):
    try:
        user = User.objects.get(username=request.user)
        name = user.username
        email = user.email
        request_data = {"name": name, "email": email}
        request_data['message'] = request.data['message']
        serializer = ContactSerializer(data=request_data)
        if serializer.is_valid():
            serializer.save()
            response_data = {'message': 'Your message has been successfully recorded. We will contact you shortly.'}
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except:
        serializer = ContactSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            response_data = {'message': 'Your message has been successfully recorded. We will contact you shortly.'}
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@throttle_classes([AnonRateThrottle])
@api_view(['GET'])
@permission_classes((permissions.AllowAny,))
def our_team(request):
    teams = Team.objects.all()
    serializer = TeamSerializer(teams, many=True, context={'request': request})
    response_data = serializer.data
    return Response(response_data, status=status.HTTP_200_OK)
