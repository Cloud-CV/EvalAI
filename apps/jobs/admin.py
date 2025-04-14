import logging

from django.contrib import admin
from apps.base.admin import ImportExportTimeStampedAdmin

from apps.jobs.models import Submission
from apps.jobs.sender import publish_submission_message
from apps.jobs.utils import handle_submission_rerun

logger = logging.getLogger(__name__)


@admin.register(Submission)
class SubmissionAdmin(ImportExportTimeStampedAdmin): # pylint: disable=too-many-ancestors
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

    def get_challenge_name_and_id(self, obj):  # pylint: disable=no-self-use
        """Return challenge name corresponding to phase"""
        title = obj.challenge_phase.challenge.title
        cid = obj.challenge_phase.challenge.id
        return f"{title} - {cid}"

    get_challenge_name_and_id.short_description = "Challenge"
    get_challenge_name_and_id.admin_order_field = "challenge_phase__challenge"

    def submit_job_to_worker(self, request, queryset): # pylint: disable=no-self-use
        for submission in queryset:
            message = handle_submission_rerun(submission, Submission.CANCELLED)
            publish_submission_message(message)

    submit_job_to_worker.short_description = (
        "Re-run selected submissions"
        " (will set the status to canceled for existing submissions)" )  
    def make_submission_public(self, request, queryset): # pylint: disable=no-self-use
        for submission in queryset:
            submission.is_public = True
            submission.save()

    make_submission_public.short_description = "Make submission public"

    def make_submission_private(self, request, queryset): # pylint: disable=no-self-use
        for submission in queryset:
            submission.is_public = False
            submission.save()

    make_submission_private.short_description = "Make submission private"

    def change_submission_status_to_cancel(self, request, queryset): # pylint: disable=no-self-use
        for submission in queryset:
            submission.status = Submission.CANCELLED
            submission.save()

    change_submission_status_to_cancel.short_description = (
        "Cancel selected submissions "
        "(will set the status to canceled for the submissions) ")
