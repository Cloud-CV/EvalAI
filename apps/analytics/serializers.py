from rest_framework import serializers

from jobs.models import Submission


class ChallengePhaseSubmissionAnalysisSerializer(serializers.ModelSerializer):

    class Meta:
        model = Submission
        fields = ('submissions_count_for_challenge_phase',
                  'participated_teams_count_for_challenge_phase',
                  'total_submissions_by_participant_team_in_challenge_phase',)
