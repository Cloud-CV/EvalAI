from django.contrib.auth import get_user_model
from rest_auth.serializers import PasswordResetSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from .models import JwtToken, Profile


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

    affiliation = serializers.CharField(
        source="profile.affiliation", allow_blank=True
    )
    github_url = serializers.URLField(
        source="profile.github_url", allow_blank=True
    )
    google_scholar_url = serializers.URLField(
        source="profile.google_scholar_url", allow_blank=True
    )
    linkedin_url = serializers.URLField(
        source="profile.linkedin_url", allow_blank=True
    )
    # Student profile fields
    address_street = serializers.CharField(
        source="profile.address_street", allow_blank=True, required=False
    )
    address_city = serializers.CharField(
        source="profile.address_city", allow_blank=True, required=False
    )
    address_state = serializers.CharField(
        source="profile.address_state", allow_blank=True, required=False
    )
    address_country = serializers.CharField(
        source="profile.address_country", allow_blank=True, required=False
    )
    university = serializers.CharField(
        source="profile.university", allow_blank=True, required=False
    )
    is_profile_complete = serializers.SerializerMethodField()

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
            "address_street",
            "address_city",
            "address_state",
            "address_country",
            "university",
            "is_profile_complete",
        )

    def get_is_profile_complete(self, obj):
        """Returns whether the user's profile is complete."""
        if hasattr(obj, "profile"):
            return obj.profile.is_complete
        return False

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", {})
        affiliation = profile_data.get("affiliation")
        github_url = profile_data.get("github_url")
        google_scholar_url = profile_data.get("google_scholar_url")
        linkedin_url = profile_data.get("linkedin_url")
        address_street = profile_data.get("address_street")
        address_city = profile_data.get("address_city")
        address_state = profile_data.get("address_state")
        address_country = profile_data.get("address_country")
        university = profile_data.get("university")

        instance = super(ProfileSerializer, self).update(
            instance, validated_data
        )

        profile = instance.profile
        if profile_data:
            profile.affiliation = affiliation
            profile.github_url = github_url
            profile.google_scholar_url = google_scholar_url
            profile.linkedin_url = linkedin_url
            if address_street is not None:
                profile.address_street = address_street
            if address_city is not None:
                profile.address_city = address_city
            if address_state is not None:
                profile.address_state = address_state
            if address_country is not None:
                profile.address_country = address_country
            if university is not None:
                profile.university = university
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
            "address_street",
            "address_city",
            "address_state",
            "address_country",
            "university",
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
            user = get_user_model().objects.get(email=self.data["email"])
            if not user.is_active:
                raise ValidationError(
                    {
                        "details": "Account is not active. Please contact the administrator."
                    }
                )
            else:
                return super().get_email_options()
        except get_user_model().DoesNotExist:
            raise ValidationError(
                {"details": "User with the given email does not exist."}
            )
