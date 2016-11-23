from django.contrib import admin


from .models import Challenge,Phase
from base.admin import TimeStampedAdmin

@admin.register(Challenge)
class ChallengeModelAdmin(TimeStampedAdmin):
    list_display = ("title","description","terms_and_conditions","submission_guidelines","evaluation_details","image","start_date","end_date","creator","published","enable_forum","anonymous_leaderboard")
    list_filter = ("title","description","terms_and_conditions","submission_guidelines","evaluation_details","image","start_date","end_date","creator","published","enable_forum","anonymous_leaderboard")
    search_fields = ("title","description","terms_and_conditions","submission_guidelines","evaluation_details","image","start_date","end_date","creator","published","enable_forum","anonymous_leaderboard")
    class Meta:
        model = Challenge

@admin.register(Phase)
class PhaseModelAdmin(TimeStampedAdmin):
    list_display = ("name","description","leaderboard_public","challenge")
    list_filter = ("name","description","leaderboard_public","challenge")
    search_fields = ("name","description","leaderboard_public","challenge")
    class Meta:
        model = Phase
