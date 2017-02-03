from django.contrib import admin

from base.admin import TimeStampedAdmin

from .models import Challenge, ChallengePhase, DatasetSplit, Leaderboard, ChallengePhaseSplit

@admin.register(Challenge)
class ChallengeAdmin(TimeStampedAdmin):
    list_display = ("title", "start_date", "end_date", "creator", "published", "enable_forum", "anonymous_leaderboard")
    list_filter = ("creator", "published", "enable_forum", "anonymous_leaderboard")
    search_fields = ("title", "creator")


@admin.register(DatasetSplit)
class DatasetSplitAdmin(TimeStampedAdmin):
    list_display = ("name", "codename")
    list_filter = ("name", "codename")
    search_fields = ("name", "codename")


@admin.register(ChallengePhase)
class ChallengePhaseAdmin(TimeStampedAdmin):
    list_display = ("name", "challenge", "start_date", "end_date", "test_annotation", "is_public", "leaderboard_public")
    list_filter = ("leaderboard_public", "challenge")
    search_fields = ("name",)


@admin.register(Leaderboard)
class LeaderboardAdmin(TimeStampedAdmin):
    list_display = ("id", "schema")
    list_filter = ("id",)
    search_fields = ("id",)

    
@admin.register(ChallengePhaseSplit)
class ChallengePhaseSplitAdmin(TimeStampedAdmin):
    list_display = ("id", "challenge_phase", "dataset_split", "leaderboard", "visibility")
    list_filter = ("id", "challenge_phase", "dataset_split", "leaderboard", "visibility")
    search_fields = ("challenge_phase", "dataset_split", "leaderboard")
