from django.contrib import admin

from base.admin import TimeStampedAdmin

from .models import Challenge, Phase


@admin.register(Challenge)
class ChallengeModelAdmin(TimeStampedAdmin):
    list_display = ("title",
                    "start_date",
                    "end_date",
                    "creator",
                    "published",
                    "enable_forum",
                    "anonymous_leaderboard")
    list_filter = ("creator",
                   "published",
                   "enable_forum",
                   "anonymous_leaderboard")
    search_fields = ("title", "creator")


@admin.register(Phase)
class PhaseModelAdmin(TimeStampedAdmin):
    list_display = ("name", "leaderboard_public", "challenge")
    list_filter = ("leaderboard_public", "challenge")
    search_fields = ("name")
