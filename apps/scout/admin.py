from django.contrib import admin
from scout.models import Scout, ScoutChallenge, ScoutRun


@admin.register(Scout)
class ScoutAdmin(admin.ModelAdmin):
    list_display = ("name", "scout_id", "created_at", "paused_at")
    readonly_fields = (
        "scout_id",
        "query_hash",
        "webhook_url",
        "webhook_token",
        "yutori_view_url",
        "created_at",
    )


@admin.register(ScoutRun)
class ScoutRunAdmin(admin.ModelAdmin):
    list_display = ("received_at", "scout", "new_challenge_count")
    list_filter = ("scout",)
    readonly_fields = (
        "scout",
        "received_at",
        "raw_payload",
        "new_challenge_count",
        "parse_warnings",
    )
    ordering = ("-received_at",)


@admin.register(ScoutChallenge)
class ScoutChallengeAdmin(admin.ModelAdmin):
    list_display = (
        "benchmark_name",
        "conference",
        "year",
        "evalai_suitable",
        "first_seen",
        "outreach_sent_at",
    )
    search_fields = ("benchmark_name", "conference", "canonical_key")
    list_filter = ("evalai_suitable", "conference", "year")
    readonly_fields = (
        "canonical_key",
        "first_seen",
        "source_run",
    )
