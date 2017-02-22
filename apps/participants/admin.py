from django.contrib import admin

from base.admin import TimeStampedAdmin
from .models import (
    Participant,
    ParticipantTeam,
)


@admin.register(Participant)
class ParticipantAdmin(TimeStampedAdmin):
    """
    An abstract base class which provides an
    interface to display user and team status.
    """
    list_display = ('user', 'status', 'team')
    search_fields = ('user', 'status', 'team')
    list_filter = ('user', 'status', 'team')


@admin.register(ParticipantTeam)
class ParticipantTeamAdmin(TimeStampedAdmin):
    """
    A class which provides interface to display
    and filter team names.
    """
    list_display = ('team_name',)
    list_filter = ('team_name',)
