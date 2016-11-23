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
    challenge = models.ForeignKey(Challenge, related_name='participants')
    status = models.ForeignKey(ParticipantStatus)

    def __str__(self):
        return '{}'.format(self.user)

    class Meta:
        app_label = 'participants'
        db_table = 'participant'
