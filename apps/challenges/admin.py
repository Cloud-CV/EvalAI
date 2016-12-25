from django.contrib import admin

from base.admin import TimeStampedAdmin

from .models import Challenge, TestEnvironment


@admin.register(Challenge)
class ChallengeAdmin(TimeStampedAdmin):
    list_display = ("title", "start_date", "end_date", "creator", "published", "enable_forum", "anonymous_leaderboard")
    list_filter = ("creator", "published", "enable_forum", "anonymous_leaderboard")
    search_fields = ("title", "creator")


@admin.register(TestEnvironment)
class TestEnvironmentAdmin(TimeStampedAdmin):
    list_display = ("name", "leaderboard_public", "challenge", "start_date", "end_date", "test_annotation")
    list_filter = ("leaderboard_public", "challenge")
    search_fields = ("name",)
