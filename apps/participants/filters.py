import django_filters
from django.db import models
from .models import ParticipantTeam


class ParticipantTeamsFilter(django_filters.FilterSet):
    class Meta:
        model = ParticipantTeam
        fields = ["participant_team__team_name"]
        filter_overrides = {
            models.CharField: {
                "filter_class": django_filters.CharFilter,
                "extra": lambda f: {"lookup_expr": "icontains", },
            },
        }
