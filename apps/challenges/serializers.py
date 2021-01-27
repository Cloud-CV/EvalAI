from rest_framework import serializers

from accounts.serializers import UserDetailsSerializer
from hosts.serializers import ChallengeHostTeamSerializer

from .models import (
    Challenge,
    ChallengeConfiguration,
    ChallengeEvaluationCluster,
    ChallengePhase,
    ChallengePhaseSplit,
    ChallengeTemplate,
    DatasetSplit,
    Leaderboard,
    PWCChallengeLeaderboard,
    StarChallenge,
    UserInvitation,
)


class ChallengeSerializer(serializers.ModelSerializer):

    is_active = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(ChallengeSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context and context.get("request").method != "GET":
            challenge_host_team = context.get("challenge_host_team")
            kwargs["data"]["creator"] = challenge_host_team.pk
        else:
            self.fields["creator"] = ChallengeHostTeamSerializer()

    class Meta:
        model = Challenge
        fields = (
            "id",
            "title",
            "short_description",
            "description",
            "terms_and_conditions",
            "submission_guidelines",
            "evaluation_details",
            "image",
            "start_date",
            "end_date",
            "creator",
            "published",
            "is_registration_open",
            "enable_forum",
            "anonymous_leaderboard",
            "is_active",
            "leaderboard_description",
            "allowed_email_domains",
            "blocked_email_domains",
            "banned_email_ids",
            "approved_by_admin",
            "forum_url",
            "is_docker_based",
            "slug",
            "max_docker_image_size",
            "cli_version",
            "remote_evaluation",
        )


class ChallengePhaseSerializer(serializers.ModelSerializer):

    is_active = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(ChallengePhaseSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            challenge = context.get("challenge")
            if challenge:
                kwargs["data"]["challenge"] = challenge.pk

    class Meta:
        model = ChallengePhase
        fields = (
            "id",
            "name",
            "description",
            "leaderboard_public",
            "start_date",
            "end_date",
            "challenge",
            "max_submissions_per_day",
            "max_submissions_per_month",
            "max_submissions",
            "is_public",
            "is_active",
            "codename",
            "slug",
            "max_concurrent_submissions_allowed",
            "is_restricted_to_select_one_submission",
            "submission_meta_attributes",
            "is_partial_submission_evaluation_enabled",
            "allowed_submission_file_types",
            "default_submission_meta_attributes",
        )


class ChallengeTemplateSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(ChallengeTemplateSerializer, self).__init__(*args, **kwargs)

    class Meta:
        model = ChallengeTemplate
        fields = (
            "id",
            "title",
            "image",
            "dataset",
            "eval_metrics",
            "phases",
            "splits",
        )


class DatasetSplitSerializer(serializers.ModelSerializer):
    def __init__(self, *args, **kwargs):
        super(DatasetSplitSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            config_id = context.get("config_id")
            if config_id:
                kwargs["data"]["config_id"] = config_id

    class Meta:
        model = DatasetSplit
        fields = ("id", "name", "codename", "config_id")


class ChallengePhaseSplitSerializer(serializers.ModelSerializer):
    """Serialize the ChallengePhaseSplits Model"""

    dataset_split_name = serializers.SerializerMethodField()
    challenge_phase_name = serializers.SerializerMethodField()

    class Meta:
        model = ChallengePhaseSplit
        fields = (
            "id",
            "dataset_split",
            "challenge_phase",
            "challenge_phase_name",
            "dataset_split_name",
            "visibility",
            "show_leaderboard_by_latest_submission",
        )

    def get_dataset_split_name(self, obj):
        return obj.dataset_split.name

    def get_challenge_phase_name(self, obj):
        return obj.challenge_phase.name


class ChallengeConfigSerializer(serializers.ModelSerializer):
    """
    Serialize the ChallengeConfiguration Model.
    """

    def __init__(self, *args, **kwargs):
        super(ChallengeConfigSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            request = context.get("request")
            kwargs["data"]["user"] = request.user.pk

    class Meta:
        model = ChallengeConfiguration
        fields = ("zip_configuration", "user")


class LeaderboardSerializer(serializers.ModelSerializer):
    """
    Serialize the Leaderboard Model.
    """

    def __init__(self, *args, **kwargs):
        super(LeaderboardSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            config_id = context.get("config_id")
            if config_id:
                kwargs["data"]["config_id"] = config_id

    class Meta:
        model = Leaderboard
        fields = ("id", "schema", "config_id")


class ZipChallengeSerializer(ChallengeSerializer):
    """
    Serializer used for creating challenge through zip file.
    """

    def __init__(self, *args, **kwargs):
        super(ZipChallengeSerializer, self).__init__(*args, **kwargs)

        context = kwargs.get("context")
        if context:
            image = context.get("image")
            if image:
                kwargs["data"]["image"] = image
            evaluation_script = context.get("evaluation_script")
            if evaluation_script:
                kwargs["data"]["evaluation_script"] = evaluation_script
            github_repository = context.get("github_repository")
            if github_repository:
                kwargs["data"]["github_repository"] = github_repository

    class Meta:
        model = Challenge
        fields = (
            "id",
            "title",
            "short_description",
            "description",
            "terms_and_conditions",
            "submission_guidelines",
            "start_date",
            "end_date",
            "creator",
            "evaluation_details",
            "published",
            "is_registration_open",
            "enable_forum",
            "anonymous_leaderboard",
            "leaderboard_description",
            "image",
            "is_active",
            "evaluation_script",
            "allowed_email_domains",
            "blocked_email_domains",
            "banned_email_ids",
            "forum_url",
            "remote_evaluation",
            "is_docker_based",
            "slug",
            "max_docker_image_size",
            "cli_version",
            "github_repository",
        )


class ZipChallengePhaseSplitSerializer(serializers.ModelSerializer):
    """
    Serializer used for creating challenge phase split through zip file.
    """

    def __init__(self, *args, **kwargs):
        super(ZipChallengePhaseSplitSerializer, self).__init__(*args, **kwargs)

        context = kwargs.get("context")
        if context:
            exclude_fields = context.get("exclude_fields")
            if exclude_fields:
                # check to avoid exception because of invalid fields
                existing = set(self.fields.keys())
                exclude_fields = set(exclude_fields)
                for field in existing.intersection(exclude_fields):
                    self.fields.pop(field)

    class Meta:
        model = ChallengePhaseSplit
        fields = (
            "id",
            "challenge_phase",
            "dataset_split",
            "leaderboard",
            "visibility",
            "leaderboard_decimal_precision",
            "is_leaderboard_order_descending",
            "show_leaderboard_by_latest_submission",
        )


class ChallengePhaseCreateSerializer(serializers.ModelSerializer):

    is_active = serializers.ReadOnlyField()

    def __init__(self, *args, **kwargs):
        super(ChallengePhaseCreateSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            challenge = context.get("challenge")
            if challenge:
                kwargs["data"]["challenge"] = challenge.pk
            test_annotation = context.get("test_annotation")
            if test_annotation:
                kwargs["data"]["test_annotation"] = test_annotation
            exclude_fields = context.get("exclude_fields")
            if exclude_fields:
                # check to avoid exception because of invalid fields
                existing = set(self.fields.keys())
                exclude_fields = set(exclude_fields)
                for field in existing.intersection(exclude_fields):
                    self.fields.pop(field)
            config_id = context.get("config_id")
            if config_id:
                kwargs["data"]["config_id"] = config_id

    class Meta:
        model = ChallengePhase
        fields = (
            "id",
            "name",
            "description",
            "leaderboard_public",
            "start_date",
            "end_date",
            "challenge",
            "max_submissions_per_day",
            "max_submissions_per_month",
            "max_submissions",
            "is_public",
            "is_active",
            "is_submission_public",
            "codename",
            "test_annotation",
            "slug",
            "max_concurrent_submissions_allowed",
            "environment_image",
            "is_restricted_to_select_one_submission",
            "submission_meta_attributes",
            "is_partial_submission_evaluation_enabled",
            "config_id",
            "allowed_submission_file_types",
            "default_submission_meta_attributes",
        )


class StarChallengeSerializer(serializers.ModelSerializer):

    count = serializers.SerializerMethodField()

    def __init__(self, *args, **kwargs):
        super(StarChallengeSerializer, self).__init__(*args, **kwargs)
        context = kwargs.get("context")
        if context:
            challenge = context.get("challenge")
            if challenge:
                kwargs["data"]["challenge"] = challenge.pk
            request = context.get("request")
            if request:
                kwargs["data"]["user"] = request.user.pk
            starred = context.get("is_starred")
            if starred:
                kwargs["data"]["is_starred"] = starred

    class Meta:
        model = StarChallenge
        fields = ("user", "challenge", "count", "is_starred")

    def get_count(self, obj):
        count = StarChallenge.objects.filter(
            challenge=obj.challenge, is_starred=True
        ).count()
        return count


class UserInvitationSerializer(serializers.ModelSerializer):
    """
    Serializer to store the invitation details
    """

    challenge_title = serializers.SerializerMethodField()
    challenge_host_team_name = serializers.SerializerMethodField()
    user_details = serializers.SerializerMethodField()

    class Meta:
        model = UserInvitation
        fields = (
            "email",
            "invitation_key",
            "status",
            "challenge",
            "user",
            "challenge_title",
            "challenge_host_team_name",
            "invited_by",
            "user_details",
        )

    def get_challenge_title(self, obj):
        return obj.challenge.title

    def get_challenge_host_team_name(self, obj):
        return obj.challenge.creator.team_name

    def get_user_details(self, obj):
        serializer = UserDetailsSerializer(obj.user)
        return serializer.data


class ChallengeEvaluationClusterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChallengeEvaluationCluster
        fields = (
            "id",
            "challenge",
            "name",
            "cluster_endpoint",
            "cluster_ssl",
            "cluster_yaml",
            "kube_config",
            "eks_arn_role",
            "node_group_arn_role",
            "ecr_all_access_policy_arn",
            "vpc_id",
            "subnet_1_id",
            "subnet_2_id",
            "security_group_id",
            "internet_gateway_id",
            "route_table_id",
        )


class PWCChallengeLeaderboardSerializer(serializers.ModelSerializer):

    challenge_id = serializers.SerializerMethodField()
    leaderboard = serializers.SerializerMethodField()
    leaderboard_decimal_precision = serializers.SerializerMethodField()
    is_leaderboard_order_descending = serializers.SerializerMethodField()

    class Meta:
        model = PWCChallengeLeaderboard
        fields = (
            "challenge_id",
            "phase_split",
            "leaderboard_decimal_precision",
            "is_leaderboard_order_descending",
            "leaderboard",
            "area",
            "task",
            "dataset",
            "enable_sync",
        )

    def get_challenge_id(self, obj):
        return obj.phase_split.challenge_phase.challenge.id

    def get_leaderboard_decimal_precision(self, obj):
        return obj.phase_split.leaderboard_decimal_precision

    def get_is_leaderboard_order_descending(self, obj):
        return obj.phase_split.is_leaderboard_order_descending

    def get_leaderboard(self, obj):
        """Get the leaderboard metrics array

        Note: PWC requires the default sorted by metric at the index '0' of the array

        Args:
            obj ([Model Class Object]): [PWCChallengeLeaderboard model object]

        Returns:
            [array]: [Leaderboard metrics for the phase split]
        """
        leaderboard_schema = obj.phase_split.leaderboard.schema
        default_order_by = leaderboard_schema["default_order_by"]
        labels = leaderboard_schema["labels"]
        default_order_by_index = labels.index(default_order_by)
        # PWC requires the default sorted by metric at the index "0" of the array
        labels.insert(0, labels.pop(default_order_by_index))
        return labels
