from challenges.models import Challenge
from django.contrib.admin import SimpleListFilter
from django.utils import timezone


class OngoingChallengesFilter(SimpleListFilter):
    """
    List filter that shows only ongoing challenges in the dropdown,
    reducing clutter when filtering submissions by challenge.
    """

    title = "By challenge"
    parameter_name = "challenge"

    def lookups(self, request, model_admin):
        now = timezone.now()
        ongoing = Challenge.objects.filter(
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            start_date__lte=now,
            end_date__gte=now,
        ).order_by("title")
        return [(c.id, c.title) for c in ongoing]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(challenge_phase__challenge_id=self.value())
        return queryset
