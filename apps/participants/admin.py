from django.contrib import admin

from base.admin import ImportExportTimeStampedAdmin
from .models import Participant, ParticipantTeam

from import_export import resources


class ParticipantResource(resources.ModelResource):
    class Meta:
        model = Participant
        fields = ("user__username", "user__email", "team", "status")
        export_order = ("user__username", "user__email", "team", "status")


@admin.register(Participant)
class ParticipantAdmin(ImportExportTimeStampedAdmin):
    """
    An abstract base class which provides an
    interface to display user and team status.
    """

    raw_id_fields = ["user", "team"]
    list_display = ("id", "user", "status", "team")
    search_fields = ("id", "user__username", "status", "team__team_name")
    list_filter = ("status",)
    resource_class = ParticipantResource


@admin.register(ParticipantTeam)
class ParticipantTeamAdmin(ImportExportTimeStampedAdmin):
    """
    A class which provides interface to display
    and filter team names.
    """

    raw_id_fields = ["created_by"]
    list_display = (
        "id",
        "team_name",
        "get_all_participants_email",
        "team_url",
    )
    search_fields = ("id", "team_name", "team_url", "created_by__username")
