import django_filters
from django.db import models
from .models import ChallengeHostTeam


class HostTeamsFilter(django_filters.FilterSet):
    class Meta:
        model = ChallengeHostTeam
        fields = ["team_name"]
        filter_overrides = {
            models.CharField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {"lookup_expr": "icontains", },
            },
        }
