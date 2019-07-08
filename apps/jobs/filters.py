import django_filters
from .models import Submission
from django.db import models


class SubmissionFilter(django_filters.FilterSet):
    class Meta:
        model = Submission
        fields = ["participant_team__team_name"]
