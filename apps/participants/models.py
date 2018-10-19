from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User

from base.models import (TimeStampedModel,)


class Participant(TimeStampedModel):
    """Model representing the Participant of the competition. """
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
    team = models.ForeignKey('ParticipantTeam', related_name='participants', null=True)

    def __str__(self):
        return '{}'.format(self.user)

    class Meta:
        app_label = 'participants'
        db_table = 'participant'


class ParticipantTeam(TimeStampedModel):
    """Model representing the Teams associated with different challenges"""
    team_name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, null=True)
    team_url = models.CharField(max_length=1000, default="", blank=True)

    def __str__(self):
        return '{}'.format(self.team_name)

    def get_all_participants_email(self):
        email_ids = Participant.objects.filter(team=self).values_list('user__email', flat=True)
        return list(email_ids)

    class Meta:
        app_label = 'participants'
        db_table = 'participant_team'
