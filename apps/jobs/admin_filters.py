from datetime import timedelta

from challenges.models import Challenge, ChallengePhase
from django.contrib.admin import SimpleListFilter
from django.db.models import Count, Exists, OuterRef, Q
from django.utils import timezone

from .models import Submission


def _get_top_challenge_ids():
    """Return IDs of top 10 challenges by submission count in last 30 days."""
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_submissions = Submission.objects.filter(
        challenge_phase__challenge_id=OuterRef("pk"),
        submitted_at__gte=thirty_days_ago,
    )
    top_challenges = (
        Challenge.objects.filter(
            published=True,
            approved_by_admin=True,
            is_disabled=False,
        )
        .annotate(has_recent_submission=Exists(recent_submissions))
        .filter(has_recent_submission=True)
        .annotate(
            submission_count=Count(
                "challengephase__submissions",
                filter=Q(
                    challengephase__submissions__submitted_at__gte=thirty_days_ago
                ),
            )
        )
        .order_by("-submission_count")[:10]
    )
    return list(top_challenges.values_list("id", flat=True))


class TopActiveChallengesFilter(SimpleListFilter):
    """
    List filter that shows top 10 challenges by submission count
    that have received submissions in the last 30 days.
    """

    title = "Top active challenges (last 30 days)"
    parameter_name = "challenge"

    def lookups(self, request, model_admin):
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_submissions = Submission.objects.filter(
            challenge_phase__challenge_id=OuterRef("pk"),
            submitted_at__gte=thirty_days_ago,
        )
        top_challenges = (
            Challenge.objects.filter(
                published=True,
                approved_by_admin=True,
                is_disabled=False,
            )
            .annotate(has_recent_submission=Exists(recent_submissions))
            .filter(has_recent_submission=True)
            .annotate(
                submission_count=Count(
                    "challengephase__submissions",
                    filter=Q(
                        challengephase__submissions__submitted_at__gte=thirty_days_ago
                    ),
                )
            )
            .order_by("-submission_count")[:10]
        )
        return [
            (c.id, f"{c.title} ({c.submission_count})") for c in top_challenges
        ]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(challenge_phase__challenge_id=self.value())
        return queryset


class ActiveChallengePhaseFilter(SimpleListFilter):
    """
    List filter for challenge phase. When a challenge is selected, only phases
    for that challenge are shown. Otherwise, only phases from top active
    challenges (last 30 days) are shown.
    """

    title = "Phase (top active challenges)"
    parameter_name = "challenge_phase"

    def lookups(self, request, model_admin):
        challenge_id = request.GET.get("challenge")
        if challenge_id:
            phases = ChallengePhase.objects.filter(
                challenge_id=challenge_id
            ).order_by("name")
            return [(p.id, p.name) for p in phases]
        # When no challenge selected, show only phases from top active
        # challenges
        top_challenge_ids = _get_top_challenge_ids()
        if not top_challenge_ids:
            return []
        phases = (
            ChallengePhase.objects.filter(challenge_id__in=top_challenge_ids)
            .select_related("challenge")
            .order_by("challenge__title", "name")
        )
        return [(p.id, f"{p.challenge.title} — {p.name}") for p in phases]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(challenge_phase_id=self.value())
        return queryset
