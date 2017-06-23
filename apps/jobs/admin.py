from django.contrib import admin

from base.admin import TimeStampedAdmin

from .models import Submission

from import_export.admin import ImportExportModelAdmin


@admin.register(Submission)
class SubmissionAdmin(TimeStampedAdmin, ImportExportModelAdmin):
    list_display = ('participant_team', 'challenge_phase', 'created_by', 'status', 'is_public',
                    'submission_number', 'submitted_at', 'execution_time', 'input_file', 'stdout_file', 'stderr_file',
                    'submission_result_file', 'submission_metadata_file', )
    list_filter = ('participant_team', 'challenge_phase',
                   'status', 'is_public')
    search_fields = ('participant_team', 'challenge_phase',
                     'created_by', 'status')
