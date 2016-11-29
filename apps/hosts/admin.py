from django.contrib import admin

from base.admin import TimeStampedAdmin

from .models import (ChallengeHost,
                     ChallengeHostTeam)


@admin.register(ChallengeHostTeam)
class HostTeamModelAdmin(TimeStampedAdmin):
    list_display = ("team_name", "created_by")
    list_filter = ("created_by", )
    search_fields = ("team_name", "created_by")


@admin.register(ChallengeHost)
class HostModelAdmin(TimeStampedAdmin):
    list_display = ("user", "team_name", "status", "permissions")
    list_filter = ("status", "permissions")
    search_fields = ("user", "team_name")
