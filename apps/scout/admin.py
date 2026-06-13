from django.contrib import admin
from scout.models import Scout, ScoutChallenge, ScoutRun


class _NoAddDeleteAdmin(admin.ModelAdmin):
    """Scout tables are populated by the webhook and management commands.
    Block create/delete from the admin so an operator can't accidentally
    insert a fake row or wipe the audit trail. Change is left enabled for
    rows that legitimately get edited (e.g. paused_at, outreach_sent_at)."""

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Scout)
class ScoutAdmin(_NoAddDeleteAdmin):
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
    """Audit log — fully read-only."""

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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(ScoutChallenge)
class ScoutChallengeAdmin(_NoAddDeleteAdmin):
    list_display = (
        "benchmark_name",
        "conference",
        "year",
        "evalai_suitable",
        "first_seen",
        "outreach_sent_at",
        "organizers",
    )
    search_fields = ("benchmark_name", "conference", "canonical_key")
    list_filter = ("evalai_suitable", "conference", "year")
    readonly_fields = (
        "canonical_key",
        "first_seen",
        "source_run",
    )
