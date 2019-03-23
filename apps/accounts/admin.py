from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User

from import_export import resources
from import_export.admin import ExportMixin
from rest_framework.authtoken.admin import TokenAdmin
from rest_framework.authtoken.models import Token

from .models import InviteUserToChallenge
from base.admin import ImportExportTimeStampedAdmin


class UserResource(resources.ModelResource):
    class Meta:
        model = User
        fields = (
            "id",
            "date_joined",
            "email",
            "first_name",
            "last_login",
            "last_name",
            "staff_status",
            "username",
        )


class UserAdmin(ExportMixin, UserAdmin):
    resource_class = UserResource


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


class TokenResource(resources.ModelResource):
    class Meta:
        model = Token


class TokenAdmin(TokenAdmin):
    resource_class = TokenResource
    list_filter = ("created",)
    search_fields = ("user__username",)


admin.site.unregister(Token)
admin.site.register(Token, TokenAdmin)


@admin.register(InviteUserToChallenge)
class InviteUserToChallengeAdmin(ImportExportTimeStampedAdmin):
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

    get_host_team_and_member_name.short_description = "Invited bY"
    get_host_team_and_member_name.admin_order_field = "invited_by"
