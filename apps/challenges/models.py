from __future__ import unicode_literals

from django.db import models

from base.models import (TimeStampedModel, )
from hosts.models import (ChallengeHostTeam, )
from participants.models import (ParticipantTeam, )


class Challenge(TimeStampedModel):
    """
    Model representing a hosted Challenge
    """
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

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge'


class TestEnvironment(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    leaderboard_public = models.BooleanField(default=False)
    start_date = models.DateTimeField(
        null=True, blank=True, verbose_name="Start Date (UTC)")
    end_date = models.DateTimeField(
        null=True, blank=True, verbose_name="End Date (UTC)")
    challenge = models.ForeignKey('Challenge')
    test_annotation = models.FileField(upload_to="test_annotations")

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge_test_env'
