from __future__ import unicode_literals

from accounts.models import (TimeStampedModel, UserStatus)
from challenges.models import (Challenge,)
from participants.models import(Participant,)

from django.db import models

class Team(TimeStampedModel):
    """
    Model representing the Teams associated with different challenges
    """
    challenge = models.ForeignKey(Challenge)
    team_name = models.CharField(max_length=64, null=False, blank=False)
    

class TeamMember(TimeStampedModel):
    """
    Model representing members associated with a particular team
    """
    participant = models.ForeignKey(Participant)
    team = models.ForeignKey(Team)
    status = models.ForeignKey(UserStatus)
