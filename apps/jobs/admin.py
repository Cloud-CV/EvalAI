import logging

from base.admin import ImportExportTimeStampedAdmin
from django.contrib import admin

from .models import Submission
from .sender import publish_submission_message
from .utils import handle_submission_rerun

logger = logging.getLogger(__name__)


@admin.register(Submission)
class SubmissionAdmin(ImportExportTimeStampedAdmin):
    """
    Admin interface for managing Submission objects.
    """
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

    @staticmethod
    def get_challenge_name_and_id(obj):
        """Return challenge name corresponding to phase"""
        return (
            f"{obj.challenge_phase.challenge.title} - "
            f"{obj.challenge_phase.challenge.id}"
        )

    get_challenge_name_and_id.short_description = "Challenge"
    get_challenge_name_and_id.admin_order_field = "challenge_phase__challenge"

    @staticmethod
    def submit_job_to_worker(request, queryset):
        """Submit selected jobs to worker"""
        for submission in queryset:
            message = handle_submission_rerun(submission, Submission.CANCELLED)
            publish_submission_message(message)

    submit_job_to_worker.short_description = (
        "Re-run submissions (sets existing to canceled)"
    )

    @staticmethod
    def make_submission_public(request, queryset):
        """Make submissions public"""
        for submission in queryset:
            submission.is_public = True
            submission.save()

    make_submission_public.short_description = "Make public"

    @staticmethod
    def make_submission_private(request, queryset):
        """Make submissions private"""
        for submission in queryset:
            submission.is_public = False
            submission.save()

    make_submission_private.short_description = "Make private"

    @staticmethod
    def change_submission_status_to_cancel(request, queryset):
        """Set selected submissions to canceled status"""
        for submission in queryset:
            submission.status = Submission.CANCELLED
            submission.save()

    change_submission_status_to_cancel.short_description = (
        "Cancel submissions (sets status to canceled)"
    )
