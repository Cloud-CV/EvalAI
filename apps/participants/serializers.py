from rest_framework import serializers

from .models import ParticipantTeam


class ParticipantTeamSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(ParticipantTeamSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            request = context.get('request')
            kwargs['data']['created_by'] = request.user.pk

    class Meta:
        model = ParticipantTeam
        fields = ('id', 'team_name', 'created_by')
