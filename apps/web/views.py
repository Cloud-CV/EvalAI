from django.shortcuts import render

from rest_framework import permissions, status
from rest_framework.decorators import (api_view,
                                       permission_classes,
                                       throttle_classes,)
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from .serializers import ContactSerializer


def home(request, template_name="index.html"):
    """
    Home Page View
    """
    return render(request, template_name)


@throttle_classes([AnonRateThrottle, ])
@api_view(['POST', ])
@permission_classes((permissions.AllowAny, ))
def contact_us(request):
    serializer = ContactSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        response_data = {'message': 'Your message has been successfully recorded. We will contact you shortly.'}
        return Response(response_data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
