from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

from base.models import (TimeStampedModel,)


class Participant(TimeStampedModel):

    UNKNOWN = 'Unknown'
    SELF = 'Self'
    DENIED = 'Denied'
    ACCEPTED = 'Accepted'
    PENDING = 'Pending'

    STATUS_OPTIONS = (
        (ACCEPTED, ACCEPTED),
        (DENIED, DENIED),
        (PENDING, PENDING),
        (SELF, SELF),
        (UNKNOWN, UNKNOWN),
    )

    user = models.ForeignKey(User, related_name='participation')
    status = models.CharField(max_length=30, choices=STATUS_OPTIONS)

    def __str__(self):
        return '{}'.format(self.user)

    class Meta:
        app_label = 'participants'
        db_table = 'participant'


class ParticipantTeam(TimeStampedModel):
    """
    Model representing the Teams associated with different challenges
    """
    team_name = models.CharField(max_length=100)
    created_by = models.ForeignKey(User, null=True)

    def __str__(self):
        return '{}'.format(self.team_name)

    class Meta:
        app_label = 'participants'
        db_table = 'participant_team'


class ParticipantTeamMember(TimeStampedModel):
    """
    Model representing participants associated with a particular team
    """
    participant = models.ForeignKey(Participant)
    team = models.ForeignKey(ParticipantTeam)

    class Meta:
        app_label = 'participants'
        db_table = 'participant_team_member'
