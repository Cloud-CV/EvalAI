from django.contrib.auth import get_user_model

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

    affiliation = serializers.CharField(source="profile.affiliation")
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
        if profile_data and affiliation:
            profile.affiliation = affiliation
            profile.github_url = github_url
            profile.google_scholar_url = google_scholar_url
            profile.linkedin_url = linkedin_url
            profile.save()
        return instance
