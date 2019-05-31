from django.contrib import admin

from base.admin import ImportExportTimeStampedAdmin

from .models import (
    Challenge,
    ChallengeConfiguration,
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
    StarChallenge,
    UserInvitation,
)


@admin.register(Challenge)
class ChallengeAdmin(ImportExportTimeStampedAdmin):
    readonly_fields = ("created_at",)
    list_display = (
        "id",
        "title",
        "start_date",
        "end_date",
        "creator",
        "published",
        "is_registration_open",
        "enable_forum",
        "anonymous_leaderboard",
        "featured",
        "created_at",
        "is_docker_based",
        "slug",
    )
    list_filter = (
        "published",
        "is_registration_open",
        "enable_forum",
        "anonymous_leaderboard",
        "featured",
        "start_date",
        "end_date",
    )
    search_fields = ("title", "creator", "creator__team_name", "slug")


@admin.register(ChallengeConfiguration)
class ChallengeConfigurationAdmin(ImportExportTimeStampedAdmin):
    list_display = (
        "id",
        "user",
        "challenge",
        "created_at",
        "is_created",
        "zip_configuration",
    )
    list_filter = ("is_created", "created_at")
    search_fields = ("challenge__title",)


@admin.register(ChallengePhase)
class ChallengePhaseAdmin(ImportExportTimeStampedAdmin):
    list_display = (
        "id",
        "name",
        "get_challenge_name_and_id",
        "start_date",
        "end_date",
        "test_annotation",
        "is_public",
        "leaderboard_public",
    )
    list_filter = ("leaderboard_public", "start_date", "end_date")
    search_fields = ("name", "challenge__title")

    def get_challenge_name_and_id(self, obj):
        """Return challenge name corresponding to phase"""
        return "%s - %s" % (obj.challenge.title, obj.challenge.id)

    get_challenge_name_and_id.short_description = "Challenge"
    get_challenge_name_and_id.admin_order_field = "challenge"


@admin.register(ChallengePhaseSplit)
class ChallengePhaseSplitAdmin(ImportExportTimeStampedAdmin):
    list_display = (
        "id",
        "get_challenge",
        "challenge_phase",
        "dataset_split",
        "leaderboard",
        "visibility",
    )
    list_filter = ("dataset_split", "leaderboard", "visibility")
    search_fields = (
        "challenge_phase__name",
        "dataset_split__name",
        "leaderboard__id",
        "dataset_split__codename",
    )

    def get_challenge(self, obj):
        """Returns challenge name corresponding to phase-split"""
        return obj.challenge_phase.challenge

    get_challenge.short_description = "Challenge"
    get_challenge.admin_order_field = "challenge_phase__challenge"


@admin.register(DatasetSplit)
class DatasetSplitAdmin(ImportExportTimeStampedAdmin):
    list_display = ("name", "codename")
    list_filter = ("name", "codename")
    search_fields = ("name", "codename")


@admin.register(Leaderboard)
class LeaderboardAdmin(ImportExportTimeStampedAdmin):
    list_display = ("id", "schema")
    search_fields = ("schema",)


@admin.register(LeaderboardData)
class LeaderboardDataAdmin(ImportExportTimeStampedAdmin):
    list_display = (
        "id",
        "get_challenge",
        "challenge_phase_split",
        "submission",
        "leaderboard",
        "result",
    )
    list_filter = ("challenge_phase_split", "created_at", "modified_at")
    search_fields = (
        "challenge_phase_split__challenge_phase__name",
        "submission__participant_team__team_name",
        "leaderboard__schema",
        "result",
    )

    def get_challenge(self, obj):
        """Returns challenge name corresponding to leaderboard data entry"""
        return obj.challenge_phase_split.challenge_phase.challenge

    get_challenge.short_description = "Challenge"
    get_challenge.admin_order_field = "challenge_phase__challenge"


@admin.register(StarChallenge)
class StarChallengeAdmin(ImportExportTimeStampedAdmin):
    list_display = ("user", "challenge", "is_starred")
    list_filter = ("is_starred",)
    search_fields = ("user__username", "challenge__title")


@admin.register(UserInvitation)
class UserInvitationAdmin(ImportExportTimeStampedAdmin):
    list_display = (
        "email",
        "invitation_key",
        "status",
        "get_challenge_name_and_id",
        "get_username_and_id",
        "get_host_team_and_member_name",
    )
    list_filter = ("status", "challenge__title")
    search_fields = ("email",)

    def get_challenge_name_and_id(self, obj):
        """Return challenge name and id for a challenge"""
        return "%s - %s" % (obj.challenge.title, obj.challenge.id)

    get_challenge_name_and_id.short_description = "Challenge"
    get_challenge_name_and_id.admin_order_field = "challenge"

    def get_username_and_id(self, obj):
        """Return username and id of a user"""
        return "%s - %s" % (obj.user.username, obj.user.id)

    get_username_and_id.short_description = "User"
    get_username_and_id.admin_order_field = "username"

    def get_host_team_and_member_name(self, obj):
        """Returns the host team name and the member name"""
        return "%s - %s" % (
            obj.invited_by.team_name.team_name,
            obj.invited_by.user.username,
        )

    get_host_team_and_member_name.short_description = "Invited by"
    get_host_team_and_member_name.admin_order_field = "invited_by"
