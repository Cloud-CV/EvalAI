from django.contrib import admin

from base.admin import TimeStampedAdmin

from .models import Contact


@admin.register(Contact)
class ContactAdmin(TimeStampedAdmin):
    list_display = ("name", "email", "message",)
    list_filter = ("email",)
    search_fields = ("email",)
