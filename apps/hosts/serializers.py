from rest_framework import serializers

from .models import (ChallengeHost,
                     ChallengeHostTeam,)


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


class ChallengeHostSerializer(serializers.ModelSerializer):

    status = serializers.ChoiceField(choices=ChallengeHost.STATUS_OPTIONS)
    permissions = serializers.ChoiceField(choices=ChallengeHost.PERMISSION_OPTIONS)

    class Meta:
        model = ChallengeHost
        fields = ('id', 'user', 'team_name', 'status', 'permissions',)
