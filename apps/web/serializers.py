from rest_framework import serializers

from .models import Contact, News, Subscribers, Team


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = ("name", "email", "message")


class NewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = News
        fields = ("title", "content", "image", "categories")


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
