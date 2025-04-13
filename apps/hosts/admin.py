from base.admin import ImportExportTimeStampedAdmin
from django.contrib import admin

from .models import ChallengeHost, ChallengeHostTeam, ChallengeHostTeamInvitation


@admin.register(ChallengeHostTeam)
class ChallengeHostTeamModelAdmin(ImportExportTimeStampedAdmin):
    raw_id_fields = ["created_by"]
    list_display = ("id", "team_name", "created_by", "team_url")
    search_fields = ("id", "team_name", "created_by__username")


@admin.register(ChallengeHost)
class ChallengeHostAdmin(ImportExportTimeStampedAdmin):
    raw_id_fields = ["user", "team_name"]
    list_display = ("id", "user", "team_name", "status", "permissions")
    list_filter = ("status", "permissions")
    search_fields = ("id", "user__username", "team_name__team_name")

@admin.register(ChallengeHostTeamInvitation)
class ChallengeHostTeamInvitationAdmin(admin.ModelAdmin):
    list_display = ('email', 'team', 'invited_by', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('email', 'team__team_name', 'invited_by__username')
    readonly_fields = ('invitation_key',)
