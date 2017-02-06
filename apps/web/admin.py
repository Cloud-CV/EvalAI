from django.contrib import admin

from base.admin import TimeStampedAdmin

from .models import Contact, Team


@admin.register(Contact)
class ContactAdmin(TimeStampedAdmin):
    list_display = ("name", "email", "message",)
    list_filter = ("email",)
    search_fields = ("email",)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_filter = ("team_type", "email",)
    list_display = ("name", "email", "team_type",)
    search_fields = ("email",)