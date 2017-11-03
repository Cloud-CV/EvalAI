from rest_framework import serializers

from jobs.models import Submission


class ChallengePhaseSubmissionCount(object):

    def __init__(self, submission_count, participant_team_count, challenge_phase_pk):
        self.submission_count = submission_count
        self.participant_team_count = participant_team_count
        self.challenge_phase = challenge_phase_pk


class ChallengePhaseSubmissionCountSerializer(serializers.Serializer):
    submission_count = serializers.IntegerField()
    participant_team_count = serializers.IntegerField()
    challenge_phase = serializers.IntegerField()


class LastSubmissionDateTimeAnalysisSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        fields = ('last_submission_timestamp_in_challenge_phase', 'last_submission_timestamp_in_challenge',
                  'challenge_phase',)
