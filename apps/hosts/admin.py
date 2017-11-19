from django.contrib import admin

from base.admin import ImportExportTimeStampedAdmin

from .models import (ChallengeHost,
                     ChallengeHostTeam)


@admin.register(ChallengeHostTeam)
class ChallengeHostTeamModelAdmin(ImportExportTimeStampedAdmin):
    list_display = ("team_name", "created_by")
    search_fields = ("team_name", "created_by__username")


@admin.register(ChallengeHost)
class ChallengeHostAdmin(ImportExportTimeStampedAdmin):
    list_display = ("user", "team_name", "status", "permissions")
    list_filter = ("status", "permissions")
    search_fields = ("user__username", "team_name__team_name")
