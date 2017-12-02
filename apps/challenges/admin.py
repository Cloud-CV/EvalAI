from django.contrib import admin

from base.admin import ImportExportTimeStampedAdmin

from .models import (Challenge,
                     ChallengeConfiguration,
                     ChallengePhase,
                     ChallengePhaseSplit,
                     DatasetSplit,
                     Leaderboard,
                     LeaderboardData,
                     StarChallenge,)


@admin.register(Challenge)
class ChallengeAdmin(ImportExportTimeStampedAdmin):
    list_display = ("title", "start_date", "end_date", "creator", "published", "enable_forum", "anonymous_leaderboard",
                    "featured")
    list_filter = ("creator", "published", "enable_forum", "anonymous_leaderboard", "featured")
    search_fields = ("title", "creator__team_name")


@admin.register(DatasetSplit)
class DatasetSplitAdmin(ImportExportTimeStampedAdmin):
    list_display = ("name", "codename")
    list_filter = ("name", "codename")
    search_fields = ("name", "codename")


@admin.register(ChallengePhase)
class ChallengePhaseAdmin(ImportExportTimeStampedAdmin):
    list_display = ("name", "challenge", "start_date", "end_date", "test_annotation", "is_public", "leaderboard_public")
    list_filter = ("leaderboard_public", "challenge")
    search_fields = ("name",)


@admin.register(Leaderboard)
class LeaderboardAdmin(ImportExportTimeStampedAdmin):
    list_display = ("id", "schema")
    search_fields = ("id",)


@admin.register(ChallengePhaseSplit)
class ChallengePhaseSplitAdmin(ImportExportTimeStampedAdmin):
    list_display = ("id", "challenge_phase", "dataset_split", "leaderboard", "visibility")
    list_filter = ("challenge_phase", "dataset_split", "leaderboard", "visibility")
    search_fields = ("challenge_phase__name", "dataset_split__name", "leaderboard__id",
                     "dataset_split__codename")


@admin.register(LeaderboardData)
class LeaderboardDataAdmin(ImportExportTimeStampedAdmin):
    list_display = ("challenge_phase_split", "submission", "leaderboard", "result")
    list_filter = ("challenge_phase_split", "leaderboard",)
    search_fields = ("challenge_phase_split__challenge_phase__name",
                     "submission__participant_team__team_name", "leaderboard__schema", "result")


@admin.register(ChallengeConfiguration)
class ChallengeConfigurationAdmin(ImportExportTimeStampedAdmin):
    list_display = ('user', 'challenge', 'is_created', 'zip_configuration',)
    list_filter = ('user', 'is_created',)
    search_fields = ('user__username', 'challenge__title',)


@admin.register(StarChallenge)
class StarChallengeAdmin(ImportExportTimeStampedAdmin):
    list_display = ('user', 'challenge', 'is_starred')
    search_fields = ('user__username', 'challenge__title',)
