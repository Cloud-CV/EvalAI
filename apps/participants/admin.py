from django.contrib import admin
from base.admin import TimeStampedAdmin
from .models import ParticipantStatus, Participant


class ParticipantStatusAdmin(TimeStampedAdmin):
    list_display = ('status',)


class ParticipantAdmin(TimeStampedAdmin):
    list_display = ('user', 'challenge', 'status',)
    search_fields = ('user', 'challenge', 'status',)
    list_filter = ('user', 'challenge', 'status',)


admin.site.register(ParticipantStatus, ParticipantStatusAdmin)
admin.site.register(Participant, ParticipantAdmin)
