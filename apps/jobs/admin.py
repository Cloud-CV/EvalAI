import logging

from base.admin import ImportExportTimeStampedAdmin
from django.contrib import admin

from .models import Submission
from .sender import publish_submission_message
from .utils import handle_submission_rerun, update_processed_submissions

logger = logging.getLogger(__name__)


@admin.register(Submission)
class SubmissionAdmin(ImportExportTimeStampedAdmin):
    actions = [
        "submit_job_to_worker",
        "make_submission_public",
        "make_submission_private",
        "change_submission_status_to_cancel",
    ]
    list_display = (
        "id",
        "participant_team",
        "get_challenge_name_and_id",
        "challenge_phase",
        "created_by",
        "status",
        "is_public",
        "submission_number",
        "submitted_at",
        "execution_time",
        "input_file",
        "submission_input_file",
        "stdout_file",
        "stderr_file",
        "environment_log_file",
        "submission_result_file",
        "submission_metadata_file",
        "job_name",
    )
    list_filter = (
        "challenge_phase__challenge",
        "challenge_phase",
        "status",
        "is_public",
    )
    search_fields = (
        "participant_team__team_name",
        "challenge_phase__name",
        "challenge_phase__challenge__title",
        "created_by__username",
        "status",
    )

    def get_challenge_name_and_id(self, obj):
        """Return challenge name corresponding to phase"""
        return "%s - %s" % (
            obj.challenge_phase.challenge.title,
            obj.challenge_phase.challenge.id,
        )

    get_challenge_name_and_id.short_description = "Challenge"
    get_challenge_name_and_id.admin_order_field = "challenge_phase__challenge"

    def submit_job_to_worker(self, request, queryset):
        for submission in queryset:
            original_status = submission.status
            message = handle_submission_rerun(submission, Submission.CANCELLED)
            if original_status in [Submission.SUBMITTED, Submission.RUNNING, Submission.SUBMITTING]:
                update_processed_submissions(submission)
            publish_submission_message(message)

    submit_job_to_worker.short_description = "Re-run selected submissions (will set the status to canceled for existing submissions)"

    def make_submission_public(self, request, queryset):
        for submission in queryset:
            submission.is_public = True
            submission.save()

    make_submission_public.short_description = "Make submission public"

    def make_submission_private(self, request, queryset):
        for submission in queryset:
            submission.is_public = False
            submission.save()

    make_submission_private.short_description = "Make submission private"

    def change_submission_status_to_cancel(self, request, queryset):
        for submission in queryset:
            original_status = submission.status
            submission.status = Submission.CANCELLED
            submission.save()
            if original_status in [Submission.SUBMITTED, Submission.RUNNING, Submission.SUBMITTING]:
                update_processed_submissions(submission)

    change_submission_status_to_cancel.short_description = "Cancel selected submissions (will set the status to canceled for the submissions) "
