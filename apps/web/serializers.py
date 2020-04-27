from rest_framework import serializers

from .models import Contact, Subscribers, Team, Organization


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ("name", "email", "message")


class SubscribeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscribers
        fields = ("email",)


class TeamSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = (
            "name",
            "description",
            "email",
            "headshot",
            "background_image",
            "github_url",
            "linkedin_url",
            "personal_website",
            "team_type",
        )


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = (
            "name",
            "logo",
            "is_active",
        )
