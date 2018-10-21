import logging

from django.contrib import admin

from base.admin import ImportExportTimeStampedAdmin

from .models import Submission
from .sender import publish_submission_message


logger = logging.getLogger(__name__)


@admin.register(Submission)
class SubmissionAdmin(ImportExportTimeStampedAdmin):
    list_display = ('participant_team', 'challenge_phase', 'created_by', 'status', 'is_public',
                    'submission_number', 'submitted_at', 'execution_time', 'input_file', 'stdout_file', 'stderr_file',
                    'submission_result_file', 'submission_metadata_file', )
    list_filter = ('participant_team', 'challenge_phase',
                   'status', 'is_public')
    search_fields = ('participant_team__team_name', 'challenge_phase__name',
                     'created_by__username', 'status')

    actions = ['submit_job_to_worker']

    def submit_job_to_worker(self, request, queryset):
        for submission in queryset:
            challenge_id = submission.challenge_phase.challenge.id
            challenge_phase_id = submission.challenge_phase.id
            submission_id = submission.id
            logger.info("[x] Received submission message with challenge id {}, challenge phase id {}, submission id {}"
                        .format(challenge_id, challenge_phase_id, submission_id))
            publish_submission_message(challenge_id, challenge_phase_id, submission.id)
            queryset.update(status=Submission.SUBMITTED)

    submit_job_to_worker.short_description = "Run selected submissions"
