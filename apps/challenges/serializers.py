from rest_framework import serializers

from hosts.serializers import ChallengeHostTeamSerializer

from .models import Challenge


class ChallengeSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(ChallengeSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get('context')
        if context:
            challenge_host_team = context.get('challenge_host_team')
            kwargs['data']['creator'] = challenge_host_team.pk
        else:
            self.fields['creator'] = ChallengeHostTeamSerializer()

    class Meta:
        model = Challenge
        fields = ('id', 'title', 'description', 'terms_and_conditions',
                  'submission_guidelines', 'evaluation_details',
                  'image', 'start_date', 'end_date', 'creator',
                  'published', 'enable_forum', 'anonymous_leaderboard',)
