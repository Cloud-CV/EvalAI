from django.contrib.auth.models import User

from rest_framework import serializers

from challenges.models import LeaderboardData
from participants.models import Participant, ParticipantTeam

from .models import Submission


class SubmissionSerializer(serializers.ModelSerializer):

    participant_team_name = serializers.SerializerMethodField()
    execution_time = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        context = kwargs.get('context')
        if context and context.get('request').method == 'POST':
            created_by = context.get('request').user
            kwargs['data']['created_by'] = created_by.pk

            participant_team = context.get('participant_team').pk
            kwargs['data']['participant_team'] = participant_team

            challenge_phase = context.get('challenge_phase').pk
            kwargs['data']['challenge_phase'] = challenge_phase

        super(SubmissionSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Submission
        fields = ('id', 'participant_team', 'participant_team_name', 'execution_time', 'challenge_phase',
                  'created_by', 'status', 'input_file', 'stdout_file', 'stderr_file', 'submitted_at',
                  'method_name', 'method_description', 'project_url', 'publication_url', 'is_public',
                  'submission_result_file',)

    def get_participant_team_name(self, obj):
        return obj.participant_team.team_name

    def get_execution_time(self, obj):
        return obj.execution_time


class LeaderboardDataSerializer(serializers.ModelSerializer):

    participant_team_name = serializers.SerializerMethodField()
    leaderboard_schema = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(LeaderboardDataSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaderboardData
        fields = "__all__"
        fields = ('id', 'participant_team_name', 'challenge_phase_split', 'leaderboard_schema', 'result')

    def get_participant_team_name(self, obj):
        return obj.submission.participant_team.team_name

    def get_leaderboard_schema(self, obj):
        return obj.leaderboard.schema


class ChallengeSubmissionManagementSerializer(serializers.ModelSerializer):

    participant_team = serializers.SerializerMethodField()
    challenge_phase = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    participant_team_members_email_id = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = ('id', 'participant_team', 'challenge_phase', 'created_by', 'status', 'is_public',
                  'submission_number', 'submitted_at', 'execution_time', 'input_file', 'stdout_file',
                  'stderr_file', 'submission_result_file', 'submission_metadata_file',
                  'participant_team_members_email_id',)

    def get_participant_team(self, obj):
        return obj.participant_team.team_name

    def get_challenge_phase(self, obj):
        return obj.challenge_phase.name

    def get_created_by(self, obj):
        return obj.created_by.username

    def get_participant_team_members_email_ids(self, obj):
        try:
            participant_team = ParticipantTeam.objects.get(team_name=obj.participant_team.team_name)
        except ParticipantTeam.DoesNotExist:
            return 'Participant team does not exist'

        participant_ids = Participant.objects.filter(team=participant_team).values_list('user_id', flat=True)
        return User.objects.filter(id__in=participant_ids).values_list('email', flat=True)
