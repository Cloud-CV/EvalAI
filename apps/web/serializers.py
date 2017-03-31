from rest_framework import serializers

from .models import Contact, Team


class ContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = ('name', 'email', 'message')


class TeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = Team
        fields = ('name', 'description', 'headshot', 'background_image', 'github_url', 'linkedin_url',
                  'personal_website', 'team_type')


class ContributorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Team
        fields = ('name', 'email', 'headshot', 'background_image', 'github_url', 'linkedin_url',
                  'personal_website', 'team_type')
