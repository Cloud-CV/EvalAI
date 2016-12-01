from django.contrib import admin

from base.admin import TimeStampedAdmin
from .models import (
    ParticipantStatus,
    Participant,
    ParticipantTeam,
    ParticipantTeamMember,
)


@admin.register(ParticipantStatus)
class ParticipantStatusAdmin(TimeStampedAdmin):
    list_display = ('status',)


@admin.register(Participant)
class ParticipantAdmin(TimeStampedAdmin):
    list_display = ('user', 'challenge', 'status',)
    search_fields = ('user', 'challenge', 'status',)
    list_filter = ('user', 'challenge', 'status',)


@admin.register(ParticipantTeam)
class ParticipantTeamAdmin(TimeStampedAdmin):
    list_display = ('challenge', 'team_name',)
    search_fields = ('challenge',)
    list_filter = ('team_name', 'challenge',)


@admin.register(ParticipantTeamMember)
class ParticipantTeamMemberAdmin(TimeStampedAdmin):
    list_display = ('participant', 'team',)
    search_fields = ('participant',)
    list_filter = ('participant', 'team',)
