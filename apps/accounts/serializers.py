from django.contrib.auth import get_user_model
from rest_auth.serializers import PasswordResetSerializer
from rest_framework.exceptions import ValidationError
from .models import JwtToken, Profile
from rest_framework import serializers


class UserDetailsSerializer(serializers.ModelSerializer):
    """
    Make username as a read_only field.
    """

    class Meta:
        model = get_user_model()
        fields = (
            "pk",
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
        )
        read_only_fields = ("email", "username")


class ProfileSerializer(UserDetailsSerializer):
    """
    Serializer to update the user profile.
    """

    affiliation = serializers.CharField(source="profile.affiliation", allow_blank=True)
    github_url = serializers.URLField(
        source="profile.github_url", allow_blank=True
    )
    google_scholar_url = serializers.URLField(
        source="profile.google_scholar_url", allow_blank=True
    )
    linkedin_url = serializers.URLField(
        source="profile.linkedin_url", allow_blank=True
    )

    class Meta(UserDetailsSerializer.Meta):
        fields = (
            "pk",
            "email",
            "username",
            "first_name",
            "last_name",
            "affiliation",
            "github_url",
            "google_scholar_url",
            "linkedin_url",
        )

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        affiliation = profile_data.get("affiliation")
        github_url = profile_data.get("github_url")
        google_scholar_url = profile_data.get("google_scholar_url")
        linkedin_url = profile_data.get("linkedin_url")

        instance = super(ProfileSerializer, self).update(
            instance, validated_data
        )

        profile = instance.profile
        if profile_data:
            profile.affiliation = affiliation
            profile.github_url = github_url
            profile.google_scholar_url = google_scholar_url
            profile.linkedin_url = linkedin_url
            profile.save()
        return instance


class UserProfileSerializer(UserDetailsSerializer):
    """
    Serializer to fetch the user profile.
    """

    class Meta:
        model = Profile
        fields = (
            "affiliation",
            "github_url",
            "google_scholar_url",
            "linkedin_url",
        )


class JwtTokenSerializer(serializers.ModelSerializer):
    """
    Serializer to update JWT token.
    """

    class Meta:
        model = JwtToken
        fields = (
            "user",
            "refresh_token",
            "access_token",
        )


class CustomPasswordResetSerializer(PasswordResetSerializer):
    """
    Serializer to check Account Active Status.
    """
    def get_email_options(self):
        try:
            user = get_user_model().objects.get(email=self.data['email'])
            if not user.is_active:
                raise ValidationError({'details': "Account is not active. Please contact the administrator."})
            else:
                return super().get_email_options()
        except get_user_model().DoesNotExist:
            raise ValidationError({'details': "User with the given email does not exist."})
