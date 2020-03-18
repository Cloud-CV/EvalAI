from rest_framework import serializers

from accounts.serializers import UserDetailsSerializer
from hosts.serializers import ChallengeHostTeamSerializer

from .models import (
    Challenge,
    ChallengeConfiguration,
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
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
        )


class DatasetSplitSerializer(serializers.ModelSerializer):
    class Meta:
        model = DatasetSplit
        fields = ("id", "name", "codename")


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

    class Meta:
        model = Leaderboard
        fields = ("id", "schema")


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
        )


class ZipChallengePhaseSplitSerializer(serializers.ModelSerializer):
    """
    Serializer used for creating challenge phase split through zip file.
    """

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
            "environment_image",
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
