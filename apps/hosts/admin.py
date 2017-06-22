from django.contrib import admin

from base.admin import TimeStampedAdmin

from .models import (ChallengeHost,
                     ChallengeHostTeam)

from import_export.admin import ImportExportModelAdmin


@admin.register(ChallengeHostTeam)
class ChallengeHostTeamModelAdmin(TimeStampedAdmin, ImportExportModelAdmin):
    list_display = ("team_name", "created_by")
    list_filter = ("created_by", )
    search_fields = ("team_name", "created_by")


@admin.register(ChallengeHost)
class ChallengeHostAdmin(TimeStampedAdmin, ImportExportModelAdmin):
    list_display = ("user", "team_name", "status", "permissions")
    list_filter = ("status", "permissions")
    search_fields = ("user", "team_name")
