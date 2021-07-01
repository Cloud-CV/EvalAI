from django.contrib.auth.models import User

from rest_framework import serializers

from challenges.models import ChallengePhase, LeaderboardData
from participants.models import Participant, ParticipantTeam

from .models import Submission


class SubmissionSerializer(serializers.ModelSerializer):

    participant_team_name = serializers.SerializerMethodField()
    execution_time = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        context = kwargs.get("context")
        if context and context.get("request").method == "POST":
            created_by = context.get("request").user
            kwargs["data"]["created_by"] = created_by.pk

            participant_team = context.get("participant_team").pk
            kwargs["data"]["participant_team"] = participant_team

            challenge_phase = context.get("challenge_phase").pk
            kwargs["data"]["challenge_phase"] = challenge_phase
        if context and context.get("request").method == "DELETE":
            ignore_submission = context.get("ignore_submission")
            kwargs["data"]["ignore_submission"] = ignore_submission

        super(SubmissionSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = Submission
        fields = (
            "id",
            "participant_team",
            "participant_team_name",
            "execution_time",
            "challenge_phase",
            "created_by",
            "status",
            "input_file",
            "submission_input_file",
            "stdout_file",
            "stderr_file",
            "started_at",
            "completed_at",
            "submitted_at",
            "method_name",
            "method_description",
            "project_url",
            "publication_url",
            "is_public",
            "is_flagged",
            "ignore_submission",
            "submission_result_file",
            "when_made_public",
            "is_baseline",
            "job_name",
            "submission_metadata",
            "is_verified_by_host",
        )

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
        fields = (
            "id",
            "participant_team_name",
            "challenge_phase_split",
            "leaderboard_schema",
            "result",
            "error",
        )

    def get_participant_team_name(self, obj):
        return obj.submission.participant_team.team_name

    def get_leaderboard_schema(self, obj):
        return obj.leaderboard.schema


class ChallengeSubmissionManagementSerializer(serializers.ModelSerializer):

    participant_team = serializers.SerializerMethodField()
    challenge_phase = serializers.SerializerMethodField()
    created_by = serializers.SerializerMethodField()
    participant_team_members_email_ids = serializers.SerializerMethodField()
    participant_team_members_affiliations = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()
    participant_team_members = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = (
            "id",
            "participant_team",
            "challenge_phase",
            "created_by",
            "status",
            "is_public",
            "is_flagged",
            "submission_number",
            "submitted_at",
            "execution_time",
            "input_file",
            "submission_input_file",
            "stdout_file",
            "stderr_file",
            "submission_result_file",
            "submission_metadata_file",
            "participant_team_members_email_ids",
            "participant_team_members_affiliations",
            "created_at",
            "method_name",
            "participant_team_members",
            "submission_metadata",
            "method_description",
            "publication_url",
            "project_url",
            "is_verified_by_host",
        )

    def get_participant_team(self, obj):
        return obj.participant_team.team_name

    def get_challenge_phase(self, obj):
        return obj.challenge_phase.name

    def get_created_by(self, obj):
        return obj.created_by.username

    def get_participant_team_members_email_ids(self, obj):
        try:
            participant_team = ParticipantTeam.objects.get(
                team_name=obj.participant_team.team_name
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

    def get_created_at(self, obj):
        return obj.created_at

    def get_participant_team_members(self, obj):
        try:
            participant_team = ParticipantTeam.objects.get(
                team_name=obj.participant_team.team_name
            )
        except ParticipantTeam.DoesNotExist:
            return "Participant team does not exist"

        participant_ids = Participant.objects.filter(
            team=participant_team
        ).values_list("user_id", flat=True)
        return list(
            User.objects.filter(id__in=participant_ids).values(
                "username", "email"
            )
        )

    def get_participant_team_members_affiliations(self, obj):
        try:
            participant_team = ParticipantTeam.objects.get(
                team_name=obj.participant_team.team_name
            )
        except ParticipantTeam.DoesNotExist:
            return "Participant team does not exist"

        participant_ids = Participant.objects.filter(
            team=participant_team
        ).values_list("user_id", flat=True)
        users = User.objects.filter(id__in=participant_ids)
        return [user.profile.affiliation for user in users]


class SubmissionCount(object):
    def __init__(self, submission_count):
        self.submission_count = submission_count


class SubmissionCountSerializer(serializers.Serializer):
    submission_count = serializers.IntegerField()


class LastSubmissionDateTime(object):
    def __init__(self, last_submission_datetime):
        self.last_submission_datetime = last_submission_datetime


class LastSubmissionDateTimeSerializer(serializers.Serializer):
    last_submission_datetime = serializers.DateTimeField()


class CreateLeaderboardDataSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        context = kwargs.get("context")
        if context and context.get("request").method == "PUT":
            challenge_phase_split = context.get("challenge_phase_split")
            kwargs["data"]["challenge_phase_split"] = challenge_phase_split.pk

            submission = context.get("submission").pk
            kwargs["data"]["submission"] = submission

            kwargs["data"][
                "leaderboard"
            ] = challenge_phase_split.leaderboard.pk

        super(CreateLeaderboardDataSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = LeaderboardData
        fields = (
            "challenge_phase_split",
            "submission",
            "result",
            "leaderboard",
        )


class RemainingSubmissionDataSerializer(serializers.ModelSerializer):
    limits = serializers.SerializerMethodField()

    class Meta:
        model = ChallengePhase
        fields = ("slug", "name", "start_date", "end_date", "limits", "id")

    def get_limits(self, obj):
        return self.context.get("limits")
