from rest_framework import serializers

from .models import ChallengeHostTeam


class ChallengeHostTeamSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(ChallengeHostTeamSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            request = context.get('request')
            kwargs['data']['created_by'] = request.user.pk

    class Meta:
        model = ChallengeHostTeam
        fields = ('id', 'team_name', 'created_by',)
