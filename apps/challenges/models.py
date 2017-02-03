from __future__ import unicode_literals

from django.utils import timezone
from django.contrib.postgres.fields import JSONField
from django.db import models

from base.models import (TimeStampedModel, )
from hosts.models import (ChallengeHostTeam, )  # noqa
from participants.models import (ParticipantTeam, )


class Challenge(TimeStampedModel):

    """Model representing a hosted Challenge"""
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    terms_and_conditions = models.TextField(null=True, blank=True)
    submission_guidelines = models.TextField(null=True, blank=True)
    evaluation_details = models.TextField(null=True, blank=True)
    image = models.ImageField(
        upload_to='logos', null=True, blank=True, verbose_name="Logo")
    start_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Start Date (UTC)")
    end_date = models.DateTimeField(
        null=True, blank=True, verbose_name="End Date (UTC)")
    creator = models.ForeignKey(
        'hosts.ChallengeHostTeam', related_name='challenge_creator')
    published = models.BooleanField(
        default=False, verbose_name="Publicly Available")
    enable_forum = models.BooleanField(default=True)
    anonymous_leaderboard = models.BooleanField(default=False)
    participant_teams = models.ManyToManyField(ParticipantTeam, blank=True)
    is_disabled = models.BooleanField(default=False)
    evaluation_script = models.FileField(default=False, upload_to="evaluation_scripts")  # should be zip format
    approved_by_admin = models.BooleanField(
        default=False, verbose_name="Approved By Admin")

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge'

    def __str__(self):
        """Returns the title of Challenge"""
        return self.title

    def get_image_url(self):
        """Returns the url of logo of Challenge"""
        if self.image:
            return self.image.url
        return None

    def get_evaluation_script_path(self):
        """Returns the path of evaluation script"""
        if self.evaluation_script:
            return self.evaluation_script.url
        return None

    def get_start_date(self):
        """Returns the start date of Challenge"""
        return self.start_date

    def get_end_date(self):
        """Returns the end date of Challenge"""
        return self.end_date

    @property
    def is_active(self):
        """Returns if the challenge is active or not"""
        if self.start_date < timezone.now() and self.end_date > timezone.now():
            return True
        return False


class DatasetSplit(TimeStampedModel):
    name = models.CharField(max_length=100)
    codename = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'challenges'
        db_table = 'dataset_split'


class ChallengePhase(TimeStampedModel):

    """Model representing a Challenge Phase"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    leaderboard_public = models.BooleanField(default=False)
    start_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Start Date (UTC)")
    end_date = models.DateTimeField(
        null=True, blank=True, verbose_name="End Date (UTC)")
    challenge = models.ForeignKey('Challenge')
    is_public = models.BooleanField(default=False)
    test_annotation = models.FileField(upload_to="test_annotations")
    max_submissions_per_day = models.PositiveIntegerField(default=100000)
    max_submissions = models.PositiveIntegerField(default=100000)
    codename = models.CharField(max_length=100, default="Phase Code Name")
    dataset_split = models.ManyToManyField(DatasetSplit, blank=True)

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge_phase'
        unique_together = (('codename', 'challenge'),)

    def __str__(self):
        """Returns the name of Phase"""
        return self.name

    def get_start_date(self):
        """Returns the start date of Phase"""
        return self.start_date

    def get_end_date(self):
        """Returns the end date of Challenge"""
        return self.end_date

    @property
    def is_active(self):
        """Returns if the challenge is active or not"""
        if self.start_date < timezone.now() and self.end_date > timezone.now():
            return True
        return False


class Leaderboard(TimeStampedModel):

    schema = JSONField()

    def __unicode__(self):
        return "%s"%(self.id)

    class Meta:
        app_label = 'challenges'
        db_table = 'leaderboard'
