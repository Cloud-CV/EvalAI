from django.contrib import admin


class TimeStampedAdmin(admin.ModelAdmin):
    exclude = ('created_at', 'modified_at',)
