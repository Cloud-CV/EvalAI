from django.contrib.auth.models import User

from rest_framework import serializers

from challenges.models import Challenge
from participants.models import Participant, ParticipantTeam
class ChallengePhaseSubmissionAnalytics(object):
    def __init__(
        self,
        total_submissions,
        participant_team_count,
        flagged_submissions_count,
        public_submissions_count,
        challenge_phase_pk,
    ):
        self.total_submissions = total_submissions
        self.participant_team_count = participant_team_count
        self.flagged_submissions_count = flagged_submissions_count
        self.public_submissions_count = public_submissions_count
        self.challenge_phase = challenge_phase_pk


class ChallengePhaseSubmissionAnalyticsSerializer(serializers.Serializer):
    total_submissions = serializers.IntegerField()
    participant_team_count = serializers.IntegerField()
    flagged_submissions_count = serializers.IntegerField()
    public_submissions_count = serializers.IntegerField()
    challenge_phase = serializers.IntegerField()


class ChallengePhaseSubmissionCount(object):
    def __init__(self, participant_team_submission_count, challenge_phase_pk):
        self.participant_team_submission_count = (
            participant_team_submission_count
        )
        self.challenge_phase = challenge_phase_pk


class ChallengePhaseSubmissionCountSerializer(serializers.Serializer):
    participant_team_submission_count = serializers.IntegerField()
    challenge_phase = serializers.IntegerField()


class LastSubmissionTimestamp(object):
    def __init__(
        self,
        last_submission_timestamp_in_challenge,
        last_submission_timestamp_in_challenge_phase,
        challenge_phase_pk,
    ):
        self.last_submission_timestamp_in_challenge = (
            last_submission_timestamp_in_challenge
        )
        self.last_submission_timestamp_in_challenge_phase = (
            last_submission_timestamp_in_challenge_phase
        )
        self.challenge_phase = challenge_phase_pk


class LastSubmissionTimestampSerializer(serializers.Serializer):
    last_submission_timestamp_in_challenge = serializers.DateTimeField(
        format=None
    )
    last_submission_timestamp_in_challenge_phase = serializers.DateTimeField(
        format=None
    )
    challenge_phase = serializers.IntegerField()


class ChallengeParticipantSerializer(serializers.Serializer):
    team_name = serializers.SerializerMethodField()
    team_members = serializers.SerializerMethodField()
    team_members_email_ids = serializers.SerializerMethodField()

    class Meta:
        model = Challenge
        fields = (
            "team_name",
            "team_members",
            "team_members_email_ids",
        )

    def get_team_name(self, obj):
        return obj.team_name

    def get_team_members(self, obj):
        try:
            participant_team = ParticipantTeam.objects.get(
                team_name=obj.team_name
            )
        except ParticipantTeam.DoesNotExist:
            return "Participant team does not exist"

        participant_ids = Participant.objects.filter(
            team=participant_team
        ).values_list("user_id", flat=True)
        return list(
            User.objects.filter(id__in=participant_ids).values_list(
                "username", flat=True
            )
        )

    def get_team_members_email_ids(self, obj):
        try:
            participant_team = ParticipantTeam.objects.get(
                team_name=obj.team_name
            )
        except ParticipantTeam.DoesNotExist:
            return "Participant team does not exist"

        participant_ids = Participant.objects.filter(
            team=participant_team
        ).values_list("user_id", flat=True)
        return list(
            User.objects.filter(id__in=participant_ids).values_list(
                "email", flat=True
            )
        )

