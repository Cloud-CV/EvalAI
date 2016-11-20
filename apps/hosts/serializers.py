from rest_framework import serializers

from .models import ChallengeHostTeam


class ChallengeHostTeamSerializer(serializers.ModelSerializer):

    class Meta:
        model = ChallengeHostTeam
        fields = ('id', 'team_name', 'created_by',)
