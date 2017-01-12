from __future__ import unicode_literals

import datetime

from os.path import join

from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import models
from django.db.models import Max

from base.models import (TimeStampedModel, )
from challenges.models import ChallengePhase
from participants.models import ParticipantTeam

import logging
logger = logging.getLogger(__name__)

def submission_root(instance):
    return join('submission_files', 'submission_' + str(instance.pk))


def input_file_name(instance, filename='input.txt'):
    return join(submission_root(instance), filename)


def stdout_file_name(instance, filename='stdout.txt'):
    return join(submission_root(instance), filename)


def stderr_file_name(instance, filename='stderr.txt'):
    return join(submission_root(instance), filename)


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
        ParticipantTeam, related_name='submissions')
    challenge_phase = models.ForeignKey(
        ChallengePhase, related_name='submissions')
    created_by = models.ForeignKey(User)
    status = models.CharField(max_length=30, choices=STATUS_OPTIONS)
    is_public = models.BooleanField(default=False)
    submission_number = models.PositiveIntegerField(default=0)
    download_count = models.IntegerField(default=0)
    submitted_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    when_made_public = models.DateTimeField(null=True, blank=True)
    input_file = models.FileField(upload_to=input_file_name)
    stdout_file = models.FileField(upload_to=stdout_file_name, null=True, blank=True)
    stderr_file = models.FileField(upload_to=stderr_file_name, null=True, blank=True)
    execution_time_limit = models.PositiveIntegerField(default=300)

    def __unicode__(self):
        return '{}'.format(self.id)

    class Meta:
        app_label = 'jobs'
        db_table = 'submission'

    def save(self, *args, **kwargs):

        if not self.pk:
            sub_num = Submission.objects.filter(
                challenge_phase=self.challenge_phase,
                participant_team=self.participant_team).aggregate(
                Max('submission_number'))['submission_number__max']
            if sub_num:
                self.submission_number = sub_num + 1
            else:
                self.submission_number = 1

            failed_count = Submission.objects.filter(
                challenge_phase=self.challenge_phase,
                participant_team=self.participant_team,
                status=Submission.FAILED).count()

            successful_count = self.submission_number - failed_count

            if successful_count > self.challenge_phase.max_submissions:
                logger.debug("Checking to see if the successful_count {0} ", \
                    " is greater than the maximum allowed {1}".format(
                        successful_count, self.challenge_phase.max_submissions))

                logger.debug("The submission request is submitted by user {0}", \
                    "from participant_team {1} ".format(
                        self.created_by.pk, self.participant_team.pk))

                raise PermissionDenied(
                    "The maximum number of submissions has been reached.")
            else:
                logger.info("Submission is below for user {0} form participant_team {1} for challenge_phase {2}".format(
                    self.created_by.pk, self.participant_team.pk, self.challenge_phase.pk))

            if hasattr(self.challenge_phase, 'max_submissions_per_day'):
                submissions_done_today_count = Submission.objects.filter(
                    challenge_phase__challenge=self.challenge_phase.challenge,
                    participant_team=self.participant_team,
                    challenge_phase=self.challenge_phase,
                    submitted_at__gte=datetime.date.today()).count()

                if ((submissions_done_today_count + 1 - failed_count > self.challenge_phase.max_submissions_per_day) or
                        (self.challenge_phase.max_submissions_per_day == 0)):
                    logger.debug("Permission Denied: The maximum number of submission for today has been reached")
                    raise PermissionDenied(
                        "The maximum number of submission for today has been reached")

            self.is_public = (True if self.challenge_phase.leaderboard_public else False)

            self.status = Submission.SUBMITTED

        submission_instance = super(Submission, self).save(*args, **kwargs)
        return submission_instance
