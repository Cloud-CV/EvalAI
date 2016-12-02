from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

from base.models import (TimeStampedModel,)
from challenges.models import (Challenge,)


class ParticipantStatus(TimeStampedModel):
    """
    Model representing the status of a challenge's participant
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
        app_label = 'participants'
        db_table = 'participant_status'


class Participant(TimeStampedModel):
    user = models.ForeignKey(User, related_name='participation')
    status = models.ForeignKey(ParticipantStatus)

    def __str__(self):
        return '{}'.format(self.user)

    class Meta:
        app_label = 'participants'
        db_table = 'participant'


class ParticipantTeam(TimeStampedModel):
    """
    Model representing the Teams associated with different challenges
    """
    challenge = models.ForeignKey(Challenge)
    created_by = models.ForeignKey(Participant, default=None)
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
