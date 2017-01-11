from __future__ import unicode_literals

from os.path import join

from django.db import models
from django.contrib.auth.models import User

from base.models import (TimeStampedModel, )
from challenges.models import ChallengePhase
from participants.models import ParticipantTeam


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
    execution_time_limit = models.PositiveIntegerField(default=300)

    def __unicode__(self):
        return '{}'.format(self.id)

    class Meta:
        app_label = 'jobs'
        db_table = 'submission'
