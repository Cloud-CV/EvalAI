from __future__ import absolute_import, division, print_function

from django.shortcuts import get_object_or_404
from django.views.generic.base import TemplateView
from rest_framework import parsers, renderers, generics, status
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from tests.models import User, Organisation, Membership
from tests import serializers


class TestView(TemplateView):
    """
    This view should not be included in DRF Docs.
    """
    template_name = "a_test.html"


class LoginView(APIView):
    """
    A view that allows users to login providing their username and password.
    """

    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)
    serializer_class = AuthTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})


class UserRegistrationView(generics.CreateAPIView):

    permission_classes = (AllowAny,)
    serializer_class = serializers.UserRegistrationSerializer


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    An endpoint for users to view and update their profile information.
    """

    serializer_class = serializers.UserProfileSerializer

    def get_object(self):
        return self.request.user


class PasswordResetView(APIView):

    permission_classes = (AllowAny,)
    queryset = User.objects.all()

    def get_object(self):
        email = self.request.data.get('email')
        obj = get_object_or_404(self.queryset, email=email)
        return obj

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        user.send_reset_password_email()
        return Response({}, status=status.HTTP_200_OK)


class PasswordResetConfirmView(APIView):

    permission_classes = (AllowAny,)
    serializer_class = serializers.ResetPasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = serializers.ResetPasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"msg": "Password updated successfully."}, status=status.HTTP_200_OK)


class CreateOrganisationView(generics.CreateAPIView):

    serializer_class = serializers.CreateOrganisationSerializer


class OrganisationMembersView(generics.ListAPIView):

    serializer_class = serializers.OrganisationMembersSerializer

    def get_queryset(self):
        organisation = Organisation.objects.order_by('?').first()
        return Membership.objects.filter(organisation=organisation)


class LeaveOrganisationView(generics.DestroyAPIView):

    def get_object(self):
        return Membership.objects.order_by('?').first()

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class OrganisationErroredView(generics.ListAPIView):

    serializer_class = serializers.OrganisationErroredSerializer


class LoginWithSerilaizerClassView(APIView):
    """
    A view that allows users to login providing their username and password. Without serializer_class
    """

    throttle_classes = ()
    permission_classes = ()
    parser_classes = (parsers.FormParser, parsers.MultiPartParser, parsers.JSONParser,)
    renderer_classes = (renderers.JSONRenderer,)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        return Response({'token': token.key})

    def get_serializer_class(self):
        return AuthTokenSerializer
