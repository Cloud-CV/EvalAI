from __future__ import unicode_literals

from accounts.models import (TimeStampedModel)
from django.db import models

from hosts.models import (ChallengeHostTeams)


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
        ChallengeHostTeams, related_name='challenge_creator')
    published = models.BooleanField(
        default=False, verbose_name="Publicly Available")
    enable_forum = models.BooleanField(default=True)
    anonymous_leaderboard = models.BooleanField(default=False)

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge'


class Phase(TimeStampedModel):
    name = models.CharField(max_length=100)
    description = models.TextField()
    leaderboard_public = models.BooleanField(default=False)
    challenge = models.ForeignKey(Challenge)

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge_phase'
