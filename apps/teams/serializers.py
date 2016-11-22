from rest_framework import serializers

from challenges.serializers import ChallengeSerializer
from .models import Team


class TeamSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(TeamSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            challenge = context.get('challenge')
            kwargs['data']['challenge'] = challenge.id
        else:
            self.fields['challenge'] = ChallengeSerializer()

    class Meta:
        model = Team
        fields = ('id', 'team_name', 'challenge',)
