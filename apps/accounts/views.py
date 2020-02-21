from django.contrib.auth import logout
from django.contrib.auth.models import User

from .models import Profile
from django import forms

from rest_framework.parsers import FileUploadParser
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework.decorators import (
    api_view,
    authentication_classes,
    permission_classes,
    throttle_classes,
    parser_classes,
)
from rest_framework.throttling import UserRateThrottle
from rest_framework_expiring_authtoken.authentication import (
    ExpiringTokenAuthentication,
)

from .permissions import HasVerifiedEmail


@api_view(["POST"])
@permission_classes((permissions.IsAuthenticated,))
@authentication_classes((ExpiringTokenAuthentication,))
def disable_user(request):

    user = request.user
    user.is_active = False
    user.save()
    logout(request)
    return Response(status=status.HTTP_200_OK)


@api_view(["GET"])
@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def get_auth_token(request):
    try:
        user = User.objects.get(email=request.user.email)
    except User.DoesNotExist:
        response_data = {"error": "This User account doesn't exist."}
        Response(response_data, status.HTTP_404_NOT_FOUND)

    try:
        token = Token.objects.get(user=user)
    except Token.DoesNotExist:
        token = Token.objects.create(user=user)
        token.save()

    response_data = {"token": "{}".format(token)}
    return Response(response_data, status=status.HTTP_200_OK)



'''@throttle_classes([UserRateThrottle])
@permission_classes((permissions.IsAuthenticated, HasVerifiedEmail))
@authentication_classes((ExpiringTokenAuthentication,))
def profile_picture(request): 
    try: 
        profile = Profile.objects.all().filter(user=request.user)
        # TODO: see if this works
        #user = User.objects.get(email=request.user.email)
    except User.DoesNotExist: 
        response_data = {"error": "This User account doesn't exist"}
        Response(response_data, status.HTTP_404_NOT_FOUND)

    if request.method == 'POST': 
        postForm = AvatarForm(request.POST, request.FILES)
        if postForm.is_valid(): 
            avatar = Avatar()
            avatar.name = postForm.cleaned_data["name"]
            avatar.image = postForm.cleaned_data["image"]
            avatar.save()
            profile.user_avatar = avatar; 
            profile.save() # check if this works at all

    current_picture = profile.user_avatar.image # TODO: replace with picture model
    form_class = AvatarForm
    username = "test user name"
    title = username + "'s avatar"
    
    return render(request, 'profile_picture.html', {'title': title, 'username': username, 'current_picture': current_picture})'''

