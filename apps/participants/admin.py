from django.contrib import admin

from base.admin import TimeStampedAdmin
from .models import (
    Participant,
    ParticipantTeam,
    ParticipantTeamMember,
)


@admin.register(Participant)
class ParticipantAdmin(TimeStampedAdmin):
    list_display = ('user', 'status',)
    search_fields = ('user', 'status',)
    list_filter = ('user', 'status',)


@admin.register(ParticipantTeam)
class ParticipantTeamAdmin(TimeStampedAdmin):
    list_display = ('team_name',)
    list_filter = ('team_name',)


@admin.register(ParticipantTeamMember)
class ParticipantTeamMemberAdmin(TimeStampedAdmin):
    list_display = ('participant', 'team',)
    search_fields = ('participant',)
    list_filter = ('participant', 'team',)
