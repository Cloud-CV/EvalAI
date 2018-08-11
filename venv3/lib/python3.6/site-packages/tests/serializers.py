from __future__ import absolute_import, division, print_function

from rest_framework import serializers
from tests.models import User, Organisation, Membership


class UserRegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password',)
        extra_kwargs = {'password': {'write_only': True}}


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('email', 'full_name', 'password', 'is_active')
        extra_kwargs = {
            'password': {'write_only': True}
        }
        read_only_fields = ('is_active',)


class ResetPasswordSerializer(serializers.ModelSerializer):

    id = serializers.CharField()
    token = serializers.CharField()

    class Meta:
        model = User
        fields = ('id', 'token', 'password',)
        extra_kwargs = {'password': {'write_only': True}}


class CreateOrganisationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organisation
        fields = ('name', 'slug',)


class OrganisationMembersSerializer(serializers.ModelSerializer):
    user = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = ('joined', 'user', 'is_owner', 'role')

    def get_user(self, obj):
        serializer = UserProfileSerializer(obj.user)
        return serializer.data


class OrganisationErroredSerializer(serializers.ModelSerializer):

    class Meta:
        model = Organisation
        fields = ('name', 'slug', 'is_active')

    def __init__(self, *args, **kwargs):
        super(OrganisationErroredSerializer, self).__init__(*args, **kwargs)

        # Should raise a KeyError
        self.context["test_value"]
