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
<<<<<<< HEAD
    list_display = ("title", "start_date", "end_date", "creator", "published", "enable_forum", "anonymous_leaderboard",
                    "featured")
    list_filter = ("creator", "published", "enable_forum", "anonymous_leaderboard", "featured")
    search_fields = ("title", "creator__team_name")


@admin.register(DatasetSplit)
class DatasetSplitAdmin(ImportExportTimeStampedAdmin):
    list_display = ("name", "codename")
    list_filter = ("name", "codename")
    search_fields = ("name", "codename")
=======
    readonly_fields = ('created_at',)
    list_display = ('id', 'title', 'start_date', 'end_date', 'creator', 'published',
                    'enable_forum', 'anonymous_leaderboard', 'featured', 'created_at',)
    list_filter = ('published', 'enable_forum', 'anonymous_leaderboard', 'featured', 'start_date', 'end_date',)
    search_fields = ('title', 'creator', 'creator__team_name',)


@admin.register(ChallengeConfiguration)
class ChallengeConfigurationAdmin(ImportExportTimeStampedAdmin):
    list_display = ('id', 'user', 'challenge', 'created_at', 'is_created', 'zip_configuration',)
    list_filter = ('is_created', 'created_at',)
    search_fields = ('challenge__title',)
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe


@admin.register(ChallengePhase)
class ChallengePhaseAdmin(ImportExportTimeStampedAdmin):
<<<<<<< HEAD
    list_display = ("name", "challenge", "start_date", "end_date", "test_annotation", "is_public", "leaderboard_public")
    list_filter = ("leaderboard_public", "challenge")
    search_fields = ("name",)


@admin.register(Leaderboard)
class LeaderboardAdmin(ImportExportTimeStampedAdmin):
    list_display = ("id", "schema")
    search_fields = ("id",)
=======
    list_display = ('id', 'name', 'get_challenge_name_and_id', 'start_date',
                    'end_date', 'test_annotation', 'is_public', 'leaderboard_public',)
    list_filter = ('leaderboard_public', 'start_date', 'end_date',)
    search_fields = ('name', 'challenge__title',)

    def get_challenge_name_and_id(self, obj):
        """Return challenge name corresponding to phase"""
        return "%s - %s" % (obj.challenge.title, obj.challenge.id)
    get_challenge_name_and_id.short_description = 'Challenge'
    get_challenge_name_and_id.admin_order_field = 'challenge'
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe


@admin.register(ChallengePhaseSplit)
class ChallengePhaseSplitAdmin(ImportExportTimeStampedAdmin):
<<<<<<< HEAD
    list_display = ("id", "challenge_phase", "dataset_split", "leaderboard", "visibility")
    list_filter = ("challenge_phase", "dataset_split", "leaderboard", "visibility")
    search_fields = ("challenge_phase__name", "dataset_split__name", "leaderboard__id",
                     "dataset_split__codename")
=======
    list_display = ('id', 'get_challenge', 'challenge_phase', 'dataset_split', 'leaderboard', 'visibility',)
    list_filter = ('dataset_split', 'leaderboard', 'visibility',)
    search_fields = ('challenge_phase__name', 'dataset_split__name', 'leaderboard__id',
                     'dataset_split__codename',)

    def get_challenge(self, obj):
        """Returns challenge name corresponding to phase-split"""
        return obj.challenge_phase.challenge
    get_challenge.short_description = 'Challenge'
    get_challenge.admin_order_field = 'challenge_phase__challenge'


@admin.register(DatasetSplit)
class DatasetSplitAdmin(ImportExportTimeStampedAdmin):
    list_display = ('name', 'codename',)
    list_filter = ('name', 'codename',)
    search_fields = ('name', 'codename',)


@admin.register(Leaderboard)
class LeaderboardAdmin(ImportExportTimeStampedAdmin):
    list_display = ('id', 'schema',)
    search_fields = ('schema',)
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe


@admin.register(LeaderboardData)
class LeaderboardDataAdmin(ImportExportTimeStampedAdmin):
<<<<<<< HEAD
    list_display = ("challenge_phase_split", "submission", "leaderboard", "result")
    list_filter = ("challenge_phase_split", "leaderboard",)
    search_fields = ("challenge_phase_split__challenge_phase__name",
                     "submission__participant_team__team_name", "leaderboard__schema", "result")


@admin.register(ChallengeConfiguration)
class ChallengeConfigurationAdmin(ImportExportTimeStampedAdmin):
    list_display = ('user', 'challenge', 'created_at', 'is_created', 'zip_configuration',)
    list_filter = ('user', 'is_created',)
    search_fields = ('user__username', 'challenge__title',)
=======
    list_display = ('id', 'get_challenge', 'challenge_phase_split', 'submission', 'leaderboard', 'result',)
    list_filter = ('challenge_phase_split', 'created_at', 'modified_at',)
    search_fields = ('challenge_phase_split__challenge_phase__name',
                     'submission__participant_team__team_name', 'leaderboard__schema', 'result',)

    def get_challenge(self, obj):
        """Returns challenge name corresponding to leaderboard data entry"""
        return obj.challenge_phase_split.challenge_phase.challenge
    get_challenge.short_description = 'Challenge'
    get_challenge.admin_order_field = 'challenge_phase__challenge'
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe


@admin.register(StarChallenge)
class StarChallengeAdmin(ImportExportTimeStampedAdmin):
<<<<<<< HEAD
    list_display = ('user', 'challenge', 'is_starred')
=======
    list_display = ('user', 'challenge', 'is_starred',)
    list_filter = ('is_starred',)
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe
    search_fields = ('user__username', 'challenge__title',)
