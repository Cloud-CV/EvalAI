from challenges.models import ChallengePhase
from hosts.models import ChallengeHost
from rest_framework import serializers
from .models import Submission

class SubmissionSerializer(serializers.ModelSerializer):
    participant_team_name = serializers.SerializerMethodField()
    execution_time = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        context = kwargs.get("context")
        self.created_by = None
        if context:
            created_by = context.get("request").user
            self.created_by = created_by

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

        super().__init__(*args, **kwargs)

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
            "environment_log_file",
            "started_at",
            "completed_at",
            "submitted_at",
            "rerun_resumed_at",
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

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        challenge_host_team = ChallengePhase.objects.get(
            pk=ret["challenge_phase"]
        ).challenge.creator
        challenge_hosts_pk = ChallengeHost.objects.filter(
            team_name=challenge_host_team
        ).values_list("user__pk", flat=True)
        if self.created_by and self.created_by.pk not in challenge_hosts_pk:
            ret.pop("environment_log_file", None)

        return ret

    @staticmethod
    def get_participant_team_name(obj):
        return obj.participant_team.team_name

    @staticmethod
    def get_execution_time(obj):
        return obj.execution_time
