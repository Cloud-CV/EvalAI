from django.contrib import admin
from django import forms
from base.admin import ImportExportTimeStampedAdmin

from django.contrib.admin.helpers import ActionForm
from django.contrib import messages

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

from .aws_utils import (
    start_workers,
    stop_workers,
    scale_workers,
    delete_workers,
    restart_workers,
)


class UpdateNumOfWorkersForm(ActionForm):
    num_of_tasks = forms.IntegerField(initial=-1, label=" Number of Workers. (Enter a whole number while scaling. Otherwise, ignore.)")


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
        "banned_email_ids",
        "workers",
        "task_def_arn",
    )
    list_filter = (
        "published",
        "is_registration_open",
        "enable_forum",
        "anonymous_leaderboard",
        "featured",
        "start_date",
        "end_date",
        "workers",
    )
    search_fields = ("title", "creator__team_name", "slug")

    actions = ["start_selected_workers", "stop_selected_workers", "scale_selected_workers", "restart_selected_workers", "delete_selected_workers"]

    action_form = UpdateNumOfWorkersForm

    def start_selected_workers(self, request, queryset):
        response = start_workers(queryset)
        count = response["count"]
        message = response["message"]

        if(count == queryset.count()):
            messages.success(request, message)
        else:
            messages.success(request, "{} challenge workers were succesfully started.".format(count))
            messages.error(request, message)
    start_selected_workers.short_description = "Start all selected challenge workers."

    def stop_selected_workers(self, request, queryset):
        response = stop_workers(queryset)
        count = response["count"]
        message = response["message"]

        if(count == queryset.count()):
            messages.success(request, message)
        else:
            messages.success(request, "{} challenge workers were succesfully stopped.".format(count))
            messages.error(request, message)
    stop_selected_workers.short_description = "Stop all selected challenge workers."

    def scale_selected_workers(self, request, queryset):
        num_of_tasks = int(request.POST['num_of_tasks'])
        if (num_of_tasks >= 0):
            response = scale_workers(queryset, num_of_tasks)
            count = response["count"]
            message = response["message"]
            if(count == queryset.count()):
                messages.success(request, message)
            else:
                messages.success(request, "{} challenge workers were succesfully scaled.".format(count))
                messages.error(request, message)
        else:
            messages.warning(request, "Please enter a valid whole number to scale.")
    scale_selected_workers.short_description = "Scale all selected challenge workers to a given number."

    def restart_selected_workers(self, request, queryset):
        response = restart_workers(queryset)
        count = response["count"]
        message = response["message"]

        if(count == queryset.count()):
            messages.success(request, message)
        else:
            messages.success(request, "{} challenge workers were succesfully restarted.".format(count))
            messages.error(request, message)
    restart_selected_workers.short_description = "Restart all selected challenge workers."

    def delete_selected_workers(self, request, queryset):
        response = delete_workers(queryset)
        count = response["count"]
        message = response["message"]

        if(count == queryset.count()):
            messages.success(request, message)
        else:
            messages.success(request, "{} challenge workers were succesfully deleted.".format(count))
            messages.error(request, message)
    delete_selected_workers.short_description = "Delete all selected challenge workers."

    actions = ["start_selected_workers", "stop_selected_workers", "scale_selected_workers", "restart_selected_workers", "delete_selected_workers"]

    action_form = UpdateNumOfWorkersForm

    def start_selected_workers(self, request, queryset):
        response = start_workers(queryset)
        count = response["count"]
        message = response["message"]

        if(count == queryset.count()):
            messages.success(request, message)
        else:
            messages.success(request, "{} challenge workers were succesfully started.".format(count))
            messages.error(request, message)
    start_selected_workers.short_description = "Start all selected challenge workers."

    def stop_selected_workers(self, request, queryset):
        response = stop_workers(queryset)
        count = response["count"]
        message = response["message"]

        if(count == queryset.count()):
            messages.success(request, message)
        else:
            messages.success(request, "{} challenge workers were succesfully stopped.".format(count))
            messages.error(request, message)
    stop_selected_workers.short_description = "Stop all selected challenge workers."

    def scale_selected_workers(self, request, queryset):
        num_of_tasks = int(request.POST['num_of_tasks'])
        if (num_of_tasks >= 0):
            response = scale_workers(queryset, num_of_tasks)
            count = response["count"]
            message = response["message"]
            if(count == queryset.count()):
                messages.success(request, message)
            else:
                messages.success(request, "{} challenge workers were succesfully scaled.".format(count))
                messages.error(request, message)
        else:
            messages.warning(request, "Please enter a valid whole number to scale.")
    scale_selected_workers.short_description = "Scale all selected challenge workers to a given number."

    def restart_selected_workers(self, request, queryset):
        response = restart_workers(queryset)
        count = response["count"]
        message = response["message"]

        if(count == queryset.count()):
            messages.success(request, message)
        else:
            messages.success(request, "{} challenge workers were succesfully restarted.".format(count))
            messages.error(request, message)
    restart_selected_workers.short_description = "Restart all selected challenge workers."

    def delete_selected_workers(self, request, queryset):
        response = delete_workers(queryset)
        count = response["count"]
        message = response["message"]

        if(count == queryset.count()):
            messages.success(request, message)
        else:
            messages.success(request, "{} challenge workers were succesfully deleted.".format(count))
            messages.error(request, message)
    delete_selected_workers.short_description = "Delete all selected challenge workers."


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
