from django.contrib.auth import get_user_model
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_text
from django.utils.http import urlsafe_base64_decode as uid_decoder

from rest_framework import serializers
from rest_framework.exceptions import ValidationError


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Make username as a read_only field.
    """
    class Meta:
        model = get_user_model()
        fields = ('pk', 'email', 'username', 'first_name', 'last_name')
        read_only_fields = ('email', 'username')


class ProfileSerializer(UserDetailsSerializer):
    """
    Serializer to update the user profile.
    """

    affiliation = serializers.CharField(source="profile.affiliation")

    class Meta(UserDetailsSerializer.Meta):
        fields = UserDetailsSerializer.Meta.fields + ('affiliation',)

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', {})
        affiliation = profile_data.get('affiliation')

        instance = super(ProfileSerializer, self).update(instance, validated_data)

        profile = instance.profile
        if profile_data and affiliation:
            profile.affiliation = affiliation
            profile.save()
        return instance


class PasswordResetTokenSerializer(serializers.Serializer):
    """
    Serializer for requesting a password reset e-mail.
    """

    user_id = serializers.CharField()
    token = serializers.CharField()

    def validate(self, attrs):

        uid = force_text(uid_decoder(attrs['user_id']))

        if not default_token_generator.check_token(User.objects.get(pk=uid), attrs['token']):
            raise ValidationError({'token': ['Token Expired or invalid']})
        return attrs
