from __future__ import unicode_literals
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User

from base.models import (TimeStampedModel, )
from challenges.models import ChallengePhase
from participants.models import ParticipantTeam


def input_file_name(instance, filename):
    return '/'.join(['submission_files', str(instance.pk), filename])


def stdout_file_name(instance, filename):
    return '/'.join(['submission_files', str(instance.pk), 'stdout.log'])


def stderr_file_name(instance, filename):
    return '/'.join(['submission_files', str(instance.pk), 'stderr.log'])


class Submission(TimeStampedModel):

    SUBMITTED = "submitted"
    RUNNING = "running"
    FAILED = "failed"
    CANCELLED = "cancelled"
    FINISHED = "finished"

    STATUS_OPTIONS = (
        (SUBMITTED, SUBMITTED),
        (RUNNING, RUNNING),
        (FAILED, FAILED),
        (CANCELLED, CANCELLED),
        (FINISHED, FINISHED),
    )

    participant_team = models.ForeignKey(ParticipantTeam, related_name='submissions')
    challenge_phase = models.ForeignKey(ChallengePhase, related_name='submissions')
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
    execution_time_limit = models.PositiveIntegerField(default=timedelta(seconds=300))

    def __unicode__(self):
        return '{}'.format(self.id)

    class Meta:
        app_label = 'jobs'
        db_table = 'submission'
