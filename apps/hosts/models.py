from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

from accounts.models import (TimeStampedModel, )
# from challenges.models import (Challenge, )


class ChallengeHostTeam(TimeStampedModel):
    """
    Model representing the Host Team for a partiuclar challenge
    """
    team_name = models.CharField(max_length=100,)
    created_by = models.ForeignKey(User, related_name='challenge_host_team_creator')

    class Meta:
        app_label = 'hosts'
        db_table = 'challenge_host_teams'


class ChallengeHost(TimeStampedModel):

    # permission options
    ADMIN = 'Admin'
    READ = 'Read'
    RESTRICTED = 'Restricted'
    WRITE = 'Write'

    # status options
    ACCEPTED = 'Accepted'
    DENIED = 'Denied'
    PENDING = 'Pending'
    SELF = 'Self'
    UNKNOWN = 'Unknown'

    PERMISSION_OPTIONS = (
        (ADMIN, ADMIN),
        (READ, READ),
        (RESTRICTED, RESTRICTED),
        (WRITE, WRITE),
    )

    STATUS_OPTIONS = (
        (ACCEPTED, ACCEPTED),
        (DENIED, DENIED),
        (PENDING, PENDING),
        (SELF, SELF),
        (UNKNOWN, UNKNOWN),
    )

    user = models.ForeignKey(User)
    team_name = models.ForeignKey('ChallengeHostTeam')
    status = models.CharField(max_length=30, choices=PERMISSION_OPTIONS)
    permissions = models.CharField(max_length=30, choices=STATUS_OPTIONS)

    class Meta:
        app_label = 'hosts'
        db_table = 'challenge_host'
