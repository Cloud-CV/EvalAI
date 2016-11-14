from __future__ import unicode_literals

from accounts.models import (TimeStampedModel, UserStatus)

from django.db import models
from django.contrib.auth.models import User


class HostPermission(TimeStampedModel):
    """
    Model representing the status of a competition's participant
    .. note::
        There are four different status:
            - Admin.
            - Write.
            - Read
            - Restricted (Default).
    """
    ADMIN = 'Admin'
    WRITE = 'Write'
    READ = 'Read'
    RESTRICTED = 'Restricted'
    name = models.CharField(max_length=30)
    status = models.CharField(max_length=30, unique=True)

    def __unicode__(self):
        return self.name


class ChallengeHostTeams(TimeStampedModel):
    team_name = models.CharField(max_length=64, null=False, blank=False)

    class Meta:
        app_label = 'hosts'


class ChallengeHost(TimeStampedModel):
    user = models.ForeignKey(User)
    affiliation = models.CharField(max_length=255, null=False, blank=False)
    team_name = models.ForeignKey(ChallengeHostTeams)
    status = models.ForeignKey(UserStatus)
    permissions = models.ForeignKey(HostPermission)
    # TODO: More field names to be added
