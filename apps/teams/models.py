from __future__ import unicode_literals

from django.db import models

from accounts.models import (TimeStampedModel, UserStatus)
from challenges.models import (Challenge,)
from participants.models import (Participant,)


class Team(TimeStampedModel):
    """
    Model representing the Teams associated with different challenges
    """
    challenge = models.ForeignKey(Challenge)
    team_name = models.CharField(max_length=100)

    def __str__(self):
        return '{}'.format(self.team_name)

    class Meta:
        app_label = 'teams'
        db_table = 'team'


class TeamMember(TimeStampedModel):
    """
    Model representing members associated with a particular team
    """
    participant = models.ForeignKey(Participant)
    team = models.ForeignKey(Team)

    class Meta:
        app_label = 'teams'
        db_table = 'team_member'
