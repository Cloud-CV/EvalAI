from rest_framework import serializers

from challenges.serializers import ChallengeSerializer
from .models import ParticipantTeam


class ParticipantTeamSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(ParticipantTeamSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            challenge = context.get('challenge')
            kwargs['data']['challenge'] = challenge.id
        else:
            self.fields['challenge'] = ChallengeSerializer()

    class Meta:
        model = ParticipantTeam
        fields = ('id', 'team_name', 'challenge',)
