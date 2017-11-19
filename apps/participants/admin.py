from django.contrib import admin

from base.admin import ImportExportTimeStampedAdmin
from .models import (
    Participant,
    ParticipantTeam,
)

from import_export import resources


class ParticipantResource(resources.ModelResource):

    class Meta:
        model = Participant
        fields = ('user__username', 'user__email', 'team', 'status',)
        export_order = ('user__username', 'user__email', 'team', 'status',)


@admin.register(Participant)
class ParticipantAdmin(ImportExportTimeStampedAdmin):
    """
    An abstract base class which provides an
    interface to display user and team status.
    """
    list_display = ('user', 'status', 'team')
    search_fields = ('user__username', 'status', 'team__team_name')
    list_filter = ('status', 'team')
    resource_class = ParticipantResource


@admin.register(ParticipantTeam)
class ParticipantTeamAdmin(ImportExportTimeStampedAdmin):
    """
    A class which provides interface to display
    and filter team names.
    """
    list_display = ('team_name', 'get_all_participants_email',)
    list_filter = ('team_name',)
