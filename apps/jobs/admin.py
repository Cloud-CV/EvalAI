import logging
import requests

from django.contrib import admin, messages

from base.admin import ImportExportTimeStampedAdmin

from .models import Submission
from .sender import publish_submission_message

logger = logging.getLogger(__name__)


@admin.register(Submission)
class SubmissionAdmin(ImportExportTimeStampedAdmin):
    actions = [
        "submit_job_to_worker",
        "make_submission_public",
        "make_submission_private",
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
        "stdout_file",
        "stderr_file",
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
            challenge_id = submission.challenge_phase.challenge.id
            challenge_phase_id = submission.challenge_phase.id
            submission_id = submission.id
            logger.info(
                "[x] Received submission message with challenge id {}, challenge phase id {}, submission id {}".format(
                    challenge_id, challenge_phase_id, submission_id
                )
            )
            message = {
                "challenge_pk": challenge_id,
                "phase_pk": challenge_phase_id,
                "submission_pk": submission.id,
            }

            if submission.challenge_phase.challenge.is_docker_based:
                try:
                    response = requests.get(submission.input_file.url)
                except Exception as e:
                    messages.error(
                        request,
                        "Failed to get input_file with exception: {0}".format(
                            e
                        ),
                    )
                    return

                if response and response.status_code == 200:
                    message["submitted_image_uri"] = response.json()[
                        "submitted_image_uri"
                    ]

            publish_submission_message(message)
            queryset.update(status=Submission.SUBMITTED)

    submit_job_to_worker.short_description = "Run selected submissions"

    def make_submission_public(self, request, queryset):
        for submision in queryset:
            submision.is_public = True
            submision.save()

    make_submission_public.short_description = "Make submission public"

    def make_submission_private(self, request, queryset):
        for submision in queryset:
            submision.is_public = False
            submision.save()

    make_submission_public.short_description = "Make submission private"
