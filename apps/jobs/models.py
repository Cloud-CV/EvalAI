from __future__ import unicode_literals

import logging

from django.contrib.auth.models import User
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Max
from rest_framework.exceptions import PermissionDenied
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone


from base.models import TimeStampedModel
from base.utils import RandomFileName
from challenges.models import ChallengePhase
from jobs.constants import submission_status_to_exclude
from participants.models import ParticipantTeam

logger = logging.getLogger(__name__)

# submission.pk is not available when saving input_file
# OutCome: `input_file` was saved for submission in folder named `submission_None`
# why is the hack not done for `stdout_file` and `stderr_file`
# Because they will be saved only after a submission instance is saved(pk will be available)


@receiver(pre_save, sender="jobs.Submission")
def skip_saving_file(sender, instance, **kwargs):
    if not instance.pk and not hasattr(instance, "_input_file"):
        setattr(instance, "_input_file", instance.input_file)
        instance.input_file = None


@receiver(post_save, sender="jobs.Submission")
def save_file(sender, instance, created, **kwargs):
    if created and hasattr(instance, "_input_file"):
        instance.input_file = getattr(instance, "_input_file")
        instance.save()


class Submission(TimeStampedModel):

    SUBMITTED = "submitted"
    RUNNING = "running"
    FAILED = "failed"
    CANCELLED = "cancelled"
    FINISHED = "finished"
    SUBMITTING = "submitting"

    STATUS_OPTIONS = (
        (SUBMITTED, SUBMITTED),
        (RUNNING, RUNNING),
        (FAILED, FAILED),
        (CANCELLED, CANCELLED),
        (FINISHED, FINISHED),
        (SUBMITTING, SUBMITTING),
    )

    participant_team = models.ForeignKey(
        ParticipantTeam, related_name="submissions"
    )
    challenge_phase = models.ForeignKey(
        ChallengePhase, related_name="submissions"
    )
    created_by = models.ForeignKey(User)
    status = models.CharField(
        max_length=30, choices=STATUS_OPTIONS, db_index=True
    )
    is_public = models.BooleanField(default=True)
    is_flagged = models.BooleanField(default=False)
    submission_number = models.PositiveIntegerField(default=0)
    download_count = models.IntegerField(default=0)
    output = models.TextField(blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True, db_index=True)
    started_at = models.DateTimeField(null=True, blank=True, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    when_made_public = models.DateTimeField(null=True, blank=True)
    input_file = models.FileField(
        upload_to=RandomFileName("submission_files/submission_{id}")
    )
    stdout_file = models.FileField(
        upload_to=RandomFileName("submission_files/submission_{id}"),
        null=True,
        blank=True,
    )
    stderr_file = models.FileField(
        upload_to=RandomFileName("submission_files/submission_{id}"),
        null=True,
        blank=True,
    )
    submission_result_file = models.FileField(
        upload_to=RandomFileName("submission_files/submission_{id}"),
        null=True,
        blank=True,
    )
    submission_metadata_file = models.FileField(
        upload_to=RandomFileName("submission_files/submission_{id}"),
        null=True,
        blank=True,
    )
    execution_time_limit = models.PositiveIntegerField(default=300)
    method_name = models.CharField(
        max_length=1000, default="", db_index=True, blank=True
    )
    method_description = models.TextField(blank=True, default="")
    publication_url = models.CharField(max_length=1000, default="", blank=True)
    project_url = models.CharField(max_length=1000, default="", blank=True)
    is_baseline = models.BooleanField(default=False)
    job_name = ArrayField(
        models.TextField(null=True, blank=True),
        default=[],
        blank=True,
        null=True,
    )

    def __str__(self):
        return "{}".format(self.id)

    class Meta:
        app_label = "jobs"
        db_table = "submission"

    @property
    def execution_time(self):
        """Returns the execution time of a submission"""
        # if self.self.completed_at and self.started_at:
        try:
            return (self.completed_at - self.started_at).total_seconds()
        except:  # noqa: E722
            return "None"
        # else:
        #     return None

    def save(self, *args, **kwargs):

        if not self.pk:
            sub_num = Submission.objects.filter(
                challenge_phase=self.challenge_phase,
                participant_team=self.participant_team,
            ).aggregate(Max("submission_number"))["submission_number__max"]
            if sub_num:
                self.submission_number = sub_num + 1
            else:
                self.submission_number = 1

            submissions = Submission.objects.filter(
                challenge_phase=self.challenge_phase,
                participant_team=self.participant_team,
            )

            num_submissions_to_ignore = submissions.filter(
                status__in=submission_status_to_exclude
            ).count()

            successful_count = (
                self.submission_number - num_submissions_to_ignore
            )

            if successful_count > self.challenge_phase.max_submissions:
                logger.info(
                    "Checking to see if the successful_count {0} is greater than maximum allowed {1}".format(
                        successful_count, self.challenge_phase.max_submissions
                    )
                )

                logger.info(
                    "The submission request is submitted by user {0} from participant_team {1} ".format(
                        self.created_by.pk, self.participant_team.pk
                    )
                )

                raise PermissionDenied(
                    {
                        "error": "The maximum number of submissions has been reached"
                    }
                )
            else:
                logger.info(
                    "Submission is below for user {0} form participant_team {1} for challenge_phase {2}".format(
                        self.created_by.pk,
                        self.participant_team.pk,
                        self.challenge_phase.pk,
                    )
                )

            total_submissions_done = Submission.objects.filter(
                challenge_phase__challenge=self.challenge_phase.challenge,
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
            )

            submissions_done_today_count = (
                total_submissions_done.filter(
                    submitted_at__gte=timezone.now().replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                )
                .exclude(status__in=submission_status_to_exclude)
                .count()
            )

            submissions_done_in_month_count = (
                total_submissions_done.filter(
                    submitted_at__gte=timezone.now().replace(
                        day=1, hour=0, minute=0, second=0, microsecond=0
                    )
                )
                .exclude(status__in=submission_status_to_exclude)
                .count()
            )

            if (
                self.challenge_phase.max_submissions_per_month
                - submissions_done_in_month_count
                == 0
            ):
                logger.info(
                    "Permission Denied: The maximum number of submission for this month has been reached"
                )
                raise PermissionDenied(
                    {
                        "error": "The maximum number of submission for this month has been reached"
                    }
                )
            if (
                self.challenge_phase.max_submissions_per_day
                - submissions_done_today_count
                == 0
            ):
                logger.info(
                    "Permission Denied: The maximum number of submission for today has been reached"
                )
                raise PermissionDenied(
                    {
                        "error": "The maximum number of submission for today has been reached"
                    }
                )

            self.is_public = (
                True if self.challenge_phase.is_submission_public else False
            )

            self.status = Submission.SUBMITTED

        submission_instance = super(Submission, self).save(*args, **kwargs)
        return submission_instance
