from django.contrib import admin

from base.admin import TimeStampedAdmin



class SubmissionAdmin(TimeStampedAdmin):
    list_display = ('participant_team', 'challenge_phase', 'created_by', 'status', 'is_public',
                    'submission_number', 'submitted_at', 'input_file', 'stdout_file', 'stderr_file')
    list_filter = ('participant_team', 'challenge_phase',
                   'created_by', 'status', 'is_public')
    search_fields = ('participant_team', 'challenge_phase',
                     'created_by', 'status')
