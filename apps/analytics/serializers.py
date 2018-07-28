from rest_framework import serializers


class ChallengePhaseSubmissionCount(object):

    def __init__(self, participant_team_submission_count, challenge_phase_pk):
        self.participant_team_submission_count = participant_team_submission_count
        self.challenge_phase = challenge_phase_pk


class ChallengePhaseSubmissionCountSerializer(serializers.Serializer):
    participant_team_submission_count = serializers.IntegerField()
    challenge_phase = serializers.IntegerField()


class LastSubmissionTimestamp(object):

    def __init__(self, last_submission_timestamp_in_challenge,
                 last_submission_timestamp_in_challenge_phase,
                 challenge_phase_pk):
        self.last_submission_timestamp_in_challenge = last_submission_timestamp_in_challenge
        self.last_submission_timestamp_in_challenge_phase = last_submission_timestamp_in_challenge_phase
        self.challenge_phase = challenge_phase_pk


class LastSubmissionTimestampSerializer(serializers.Serializer):
    last_submission_timestamp_in_challenge = serializers.DateTimeField(format=None)
    last_submission_timestamp_in_challenge_phase = serializers.DateTimeField(format=None)
    challenge_phase = serializers.IntegerField()
