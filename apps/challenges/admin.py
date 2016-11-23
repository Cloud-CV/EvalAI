from django.contrib import admin
from .models import Challenge, Phase
# Register your models here.
class challengesAD(admin.ModelAdmin):
  list_display = ['title', 'description', 'terms_and_conditions', 'submission_guidelines', 'evaluation_details', 'image', 'start_date', 'end_date', 'creator', 'published', 'enable_forum', 'anonymous_leaderboard']
  search_fields = ['title', 'description','creator']
  list_filter = ['start_date']
  class Meta:
    models = Challenge
admin.site.register(challenge, challengesAD)

class phaseAD(admin.ModelAdmin):
  list_display = ['name', 'description', 'leaderboard_public', 'challenge']
  search_fields = ['name', 'description','challenge']
  list_filter = ['']
  class Meta:
    models = Phase
admin.site.register(Phase, phaseAD)
