from django.contrib import admin

from import_export.admin import ImportExportMixin


class TimeStampedAdmin(admin.ModelAdmin):
    exclude = ("created_at", "modified_at")


class ImportExportTimeStampedAdmin(ImportExportMixin, admin.ModelAdmin):
    exclude = ("created_at", "modified_at")
