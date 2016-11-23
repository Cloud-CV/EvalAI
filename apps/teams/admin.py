from django.contrib import admin
from base.admin import TimeStampedAdmin
from .models import Team, TeamMember

class TeamAdmin(TimeStampedAdmin):
    list_display = ('challenge', 'team_name',)
    search_fields = ('challenge',)
    list_filter = ('team_name', 'challenge',)


class TeamMemberAdmin(TimeStampedAdmin):
    list_display = ('participant', 'team',)
    search_fields = ('participant',)
    list_filter = ('participant', 'team',)


admin.site.register(Team ,TeamAdmin)
admin.site.register(TeamMember, TeamMemberAdmin)
