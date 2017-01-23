from rest_framework import serializers

from participants.serializers import ParticipantTeamSerializer

from .models import Submission


class SubmissionSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        context = kwargs.get('context')
        if context:
            created_by = context.get('request').user
            kwargs['data']['created_by'] = created_by.pk

            participant_team = context.get('participant_team').pk
            kwargs['data']['participant_team'] = participant_team

            challenge_phase = context.get('challenge_phase').pk
            kwargs['data']['challenge_phase'] = challenge_phase

        super(SubmissionSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Submission
        fields = ('participant_team', 'challenge_phase', 'created_by', 'status', 'input_file')


class LeaderboardSerializer(serializers.ModelSerializer):

    def __init__(self, *args, **kwargs):
        super(LeaderboardSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Submission
        fields = ('participant_team', 'challenge_phase', 'created_by', 'status', 'input_file', 'output', 'id')
