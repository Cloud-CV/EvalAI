from rest_framework import serializers

from hosts.serializers import ChallengeHostTeamSerializer

from .models import Challenge


class ChallengeSerializer(serializers.ModelSerializer):

    creator = ChallengeHostTeamSerializer()

    class Meta:
        model = Challenge
        fields = ('id', 'title', 'description', 'terms_and_conditions',
                  'submission_guidelines', 'evaluation_details',
                  'image', 'start_date', 'end_date', 'creator',
                  'published', 'enable_forum', 'anonymous_leaderboard',)
