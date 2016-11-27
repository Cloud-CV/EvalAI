from django.contrib import admin

from base.admin import TimeStampedAdmin

from .models import ChallengeHostTeam, ChallengeHost


@admin.register(ChallengeHostTeam)
class HostTeamModelAdmin(TimeStampedAdmin):
    list_display = ("team_name", "created_by")
    list_filter = ("team_name", "created_by")
    search_fields = ("team_name", "created_by")


@admin.register(ChallengeHost)
class HostModelAdmin(TimeStampedAdmin):
    list_display = ("user", "team_name", "status")
    list_filter = ("user", "team_name", "status")
    search_fields = ("user", "team_name", "status")
