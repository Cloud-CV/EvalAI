from rest_framework import serializers

from jobs.models import Submission


class ChallengePhaseSubmissionAnalysisSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        fields = ('submissions_count_for_challenge_phase',
                  'participated_teams_count_for_challenge_phase',
                  'challenge_phase',)


class LastSubmissionDateTimeAnalysisSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        fields = ('last_submission_timestamp_in_challenge_phase', 'last_submission_timestamp_in_challenge',
                  'challenge_phase',)
