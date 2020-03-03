from django.contrib import admin

from base.admin import ImportExportTimeStampedAdmin

from .models import Contact, Subscribers, Team, Organization


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "message",
        "status",
        "created_at",
        "modified_at",
    )
    search_fields = ("email",)


@admin.register(Subscribers)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = (
        "email",
    )
    search_fields = ("email",)


@admin.register(Team)
class TeamAdmin(ImportExportTimeStampedAdmin):
    list_filter = ("team_type",)
    list_display = ("position", "name", "email", "team_type")
    search_fields = ("email", "name")


@admin.register(Organization)
class OrganizationAdmin(ImportExportTimeStampedAdmin):
    list_filter = ("name",)
    list_display = ("name",)
    search_fields = ("name",)
