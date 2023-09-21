from django import forms
from django.contrib import admin, messages

from django.contrib.admin.helpers import ActionForm

from base.admin import ImportExportTimeStampedAdmin

from .aws_utils import (
    delete_workers,
    restart_workers,
    scale_workers,
    start_workers,
    stop_workers,
)

from .admin_filters import ChallengeFilter

from .models import (
    Challenge,
    ChallengeConfiguration,
    ChallengeEvaluationCluster,
    ChallengePhase,
    ChallengePhaseSplit,
    ChallengeTemplate,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
    PWCChallengeLeaderboard,
    StarChallenge,
    UserInvitation,
    ChallengeSponsor,
    ChallengePrize,
)


class UpdateNumOfWorkersForm(ActionForm):
    label = "Number of workers. (Enter a whole number while scaling. Otherwise, ignore.)"
    num_of_tasks = forms.IntegerField(initial=-1, label=label, required=False)


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
        "is_static_dataset_code_upload",
        "slug",
        "submission_time_limit",
        "banned_email_ids",
        "workers",
        "task_def_arn",
        "github_repository",
    )
    list_filter = (
        ChallengeFilter,
        "published",
        "is_registration_open",
        "enable_forum",
        "anonymous_leaderboard",
        "featured",
        "start_date",
        "end_date",
    )
    search_fields = (
        "id",
        "title",
        "creator__team_name",
        "slug",
        "github_repository",
    )
    actions = [
        "start_selected_workers",
        "stop_selected_workers",
        "scale_selected_workers",
        "restart_selected_workers",
        "delete_selected_workers",
    ]
    action_form = UpdateNumOfWorkersForm

    def start_selected_workers(self, request, queryset):
        response = start_workers(queryset)
        count, failures = response["count"], response["failures"]

        if count == queryset.count():
            message = "All selected challenge workers successfully started."
            messages.success(request, message)
        else:
            messages.success(
                request,
                "{} challenge workers were succesfully started.".format(count),
            )
            for fail in failures:
                challenge_pk, message = fail["challenge_pk"], fail["message"]
                display_message = "Challenge {}: {}".format(
                    challenge_pk, message
                )
                messages.error(request, display_message)

    start_selected_workers.short_description = (
        "Start all selected challenge workers."
    )

    def stop_selected_workers(self, request, queryset):
        response = stop_workers(queryset)
        count, failures = response["count"], response["failures"]

        if count == queryset.count():
            message = "All selected challenge workers successfully stopped."
            messages.success(request, message)
        else:
            messages.success(
                request,
                "{} challenge workers were succesfully stopped.".format(count),
            )
            for fail in failures:
                challenge_pk, message = fail["challenge_pk"], fail["message"]
                display_message = "Challenge {}: {}".format(
                    challenge_pk, message
                )
                messages.error(request, display_message)

    stop_selected_workers.short_description = (
        "Stop all selected challenge workers."
    )

    def scale_selected_workers(self, request, queryset):
        num_of_tasks = int(request.POST["num_of_tasks"])
        if num_of_tasks >= 0 and num_of_tasks % 1 == 0:
            response = scale_workers(queryset, num_of_tasks)
            count, failures = response["count"], response["failures"]
            if count == queryset.count():
                message = "All selected challenge workers successfully scaled."
                messages.success(request, message)
            else:
                messages.success(
                    request,
                    "{} challenge workers were succesfully scaled.".format(
                        count
                    ),
                )
                for fail in failures:
                    challenge_pk, message = (
                        fail["challenge_pk"],
                        fail["message"],
                    )
                    display_message = "Challenge {}: {}".format(
                        challenge_pk, message
                    )
                    messages.error(request, display_message)
        else:
            messages.warning(
                request, "Please enter a valid whole number to scale."
            )

    scale_selected_workers.short_description = (
        "Scale all selected challenge workers to a given number."
    )

    def restart_selected_workers(self, request, queryset):
        response = restart_workers(queryset)
        count, failures = response["count"], response["failures"]

        if count == queryset.count():
            message = "All selected challenge workers successfully restarted."
            messages.success(request, message)
        else:
            messages.success(
                request,
                "{} challenge workers were succesfully restarted.".format(
                    count
                ),
            )
            for fail in failures:
                challenge_pk, message = fail["challenge_pk"], fail["message"]
                display_message = "Challenge {}: {}".format(
                    challenge_pk, message
                )
                messages.error(request, display_message)

    restart_selected_workers.short_description = (
        "Restart all selected challenge workers."
    )

    def delete_selected_workers(self, request, queryset):
        response = delete_workers(queryset)
        count, failures = response["count"], response["failures"]

        if count == queryset.count():
            message = "All selected challenge workers successfully deleted."
            messages.success(request, message)
        else:
            messages.success(
                request,
                "{} challenge workers were succesfully deleted.".format(count),
            )
            for fail in failures:
                challenge_pk, message = fail["challenge_pk"], fail["message"]
                display_message = "Challenge {}: {}".format(
                    challenge_pk, message
                )
                messages.error(request, display_message)

    delete_selected_workers.short_description = (
        "Delete all selected challenge workers."
    )


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
    search_fields = ("id", "challenge__title")


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
        "is_submission_public",
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
    raw_id_fields = ["challenge_phase", "leaderboard", "dataset_split"]
    list_display = (
        "id",
        "get_challenge",
        "challenge_phase",
        "dataset_split",
        "leaderboard",
        "visibility",
        "leaderboard_decimal_precision",
        "is_leaderboard_order_descending",
        "show_execution_time",
    )
    list_filter = ("visibility",)
    search_fields = (
        "id",
        "challenge_phase__challenge__title",
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


@admin.register(ChallengeTemplate)
class ChallengeTemplate(ImportExportTimeStampedAdmin):
    list_display = (
        "id",
        "title",
        "image",
        "dataset",
        "eval_metrics",
        "phases",
        "splits",
    )
    list_filter = ("title", "dataset", "phases", "splits", "eval_metrics")
    search_fields = (
        "id",
        "title",
        "dataset",
        "phases",
        "splits",
        "eval_metrics",
    )


@admin.register(DatasetSplit)
class DatasetSplitAdmin(ImportExportTimeStampedAdmin):
    list_display = ("name", "codename")
    list_filter = ("name", "codename")
    search_fields = ("id", "name", "codename")


@admin.register(Leaderboard)
class LeaderboardAdmin(ImportExportTimeStampedAdmin):
    list_display = ("id", "schema")
    search_fields = ("id", "schema")


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
        "id",
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
    search_fields = ("id", "user__username", "challenge__title")


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


@admin.register(ChallengeEvaluationCluster)
class ChallengeEvaluationClusterAdmin(ImportExportTimeStampedAdmin):
    readonly_fields = ("created_at",)
    list_display = ("id", "name", "cluster_yaml", "kube_config")
    list_filter = ("name",)
    search_fields = ("id", "name")


@admin.register(PWCChallengeLeaderboard)
class PWCChallengeLeaderboardAdmin(ImportExportTimeStampedAdmin):
    raw_id_fields = ["phase_split"]
    readonly_fields = ("created_at",)
    list_display = (
        "id",
        "get_challenge_name_and_id",
        "phase_split",
        "get_challenge_phase_split_id",
        "area",
        "task",
        "dataset",
        "enable_sync",
    )
    list_filter = ("area", "enable_sync")
    search_fields = ("id", "area", "task", "dataset")

    def get_challenge_phase_split_id(self, obj):
        """Return challenge phase split id for a challenge phase and split"""
        return "%s" % (obj.phase_split.id)

    get_challenge_phase_split_id.short_description = "Challenge Phase Split ID"
    get_challenge_phase_split_id.admin_order_field = "phase_split"

    def get_challenge_name_and_id(self, obj):
        """Return challenge name and id for a challenge"""
        return "%s - %s" % (
            obj.phase_split.challenge_phase.challenge.title,
            obj.phase_split.challenge_phase.challenge.id,
        )

    get_challenge_name_and_id.short_description = "Challenge Name - ID"
    get_challenge_name_and_id.admin_order_field = "challenge_phase__challenge"


@admin.register(ChallengeSponsor)
class ChallengeSponsorAdmin(ImportExportTimeStampedAdmin):
    list_display = ("id", "name", "website")
    list_filter = ("name",)
    search_fields = ("id", "name")


@admin.register(ChallengePrize)
class ChallengePrizeAdmin(ImportExportTimeStampedAdmin):
    list_display = ("id", "amount", "rank")
    list_filter = ("rank",)
    search_fields = ("id", "rank")
