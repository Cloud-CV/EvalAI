from django.contrib import admin

from base.admin import ImportExportTimeStampedAdmin

from .models import Contact, Team


@admin.register(Contact)
class ContactAdmin(ImportExportTimeStampedAdmin):
    list_display = ("name", "email", "message",)
    search_fields = ("email",)


@admin.register(Team)
class TeamAdmin(ImportExportTimeStampedAdmin):
    list_filter = ("team_type",)
    list_display = ("name", "email", "team_type",)
    search_fields = ("email", "name",)
