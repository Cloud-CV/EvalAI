from django.contrib.admin import SimpleListFilter
from django.utils import timezone


class ChallengeFilter(SimpleListFilter):

    title = "Challenges"
    parameter_name = "challenge"

    def lookups(self, request, model_admin):
        options = [
            ("past", "Past"),
            ("present", "Ongoing"),
            ("future", "Upcoming"),
        ]
        return options

    def queryset(self, request, queryset):
        q_params = {
            "published": True,
            "approved_by_admin": True,
            "is_disabled": False,
        }
        if self.value() == "past":
            q_params["end_date__lt"] = timezone.now()
            challenges = queryset.filter(**q_params)
            return challenges

        elif self.value() == "present":
            q_params["start_date__lt"] = timezone.now()
            q_params["end_date__gt"] = timezone.now()
            challenges = queryset.filter(**q_params)
            return challenges

        elif self.value() == "future":
            q_params["start_date__gt"] = timezone.now()
            challenges = queryset.filter(**q_params)
            return challenges
