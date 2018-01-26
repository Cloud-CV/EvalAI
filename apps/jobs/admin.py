from django.contrib import admin

from base.admin import ImportExportTimeStampedAdmin

from .models import Submission


@admin.register(Submission)
class SubmissionAdmin(ImportExportTimeStampedAdmin):
    list_display = ('participant_team', 'challenge_phase', 'created_by', 'status', 'is_public',
                    'submission_number', 'submitted_at', 'execution_time', 'input_file', 'stdout_file', 'stderr_file',
                    'submission_result_file', 'submission_metadata_file', )
    list_filter = ('participant_team', 'challenge_phase',
                   'status', 'is_public')
    search_fields = ('participant_team__team_name', 'challenge_phase__name',
                     'created_by__username', 'status')
