from rest_framework import serializers

from challenges.serializers import ChallengeSerializer
from .models import Team


class TeamChallengeSerializer(serializers.ModelSerializer):

    challenge = ChallengeSerializer()

    class Meta:
        model = Team
        fields = ('id', 'team_name', 'challenge')
