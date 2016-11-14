from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

from accounts.models import (TimeStampedModel, )
from challenge.models import (Challenge,)


class ChallengeHostPermission(TimeStampedModel):
    """
    Model representing the permissions for a Challenge Hosting Member
    .. note::
        There are four different status:
            - Admin (Includes CRUD).
            - Write (Includes CRU).
            - Read (Includes R)
            - Restricted (Default).
    """
    ADMIN = 'Admin'
    WRITE = 'Write'
    READ = 'Read'
    RESTRICTED = 'Restricted'
    status = models.CharField(max_length=30, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge_host_permission'


class ChallengeHostStatus(TimeStampedModel):
    """
    Model representing the status of a challenge's host
    .. note::
        There are five different status:
            - Unknown.
            - Denied.
            - self.
            - Approved.
            - Pending.
    """

    UNKNOWN = 'unknown'
    SELF = 'self'
    DENIED = 'denied'
    ACCEPTED = 'accepted'
    PENDING = 'pending'

    status = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return '{} - {}'.format(self.id, self.status)

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge_host_status'


class ChallengeHostTeams(TimeStampedModel):
    """
    Model representing the Host Team for a partiuclar challenge
    """
    challenge = models.ForeignKey(Challenge, related_name='host_teams')
    team_name = models.CharField(max_length=100,)

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge_host_teams'


class ChallengeHost(TimeStampedModel):
    user = models.ForeignKey(User)
    team_name = models.ForeignKey(ChallengeHostTeams)
    status = models.ForeignKey(ChallengeHostStatus)
    permissions = models.ForeignKey(ChallengeHostPermission)

    class Meta:
        app_label = 'challenges'
        db_table = 'challenge_host'
