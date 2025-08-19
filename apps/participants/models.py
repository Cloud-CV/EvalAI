"""Module for participant-related models in the competition system."""
from __future__ import unicode_literals

from django.contrib.auth.models import User
from django.db import models

from base.models import TimeStampedModel


class Participant(TimeStampedModel):
    """Model representing a participant of the competition.
    
    This model stores information about individual participants, their
    status in the competition, and their team affiliation.
    """

    UNKNOWN = "Unknown"
    SELF = "Self"
    DENIED = "Denied"
    ACCEPTED = "Accepted"
    PENDING = "Pending"

    STATUS_OPTIONS = (
        (ACCEPTED, ACCEPTED),
        (DENIED, DENIED),
        (PENDING, PENDING),
        (SELF, SELF),
        (UNKNOWN, UNKNOWN),
    )

    user = models.ForeignKey(
        User, related_name="participation", on_delete=models.CASCADE
    )
    status = models.CharField(max_length=30, choices=STATUS_OPTIONS)
    team = models.ForeignKey(
        "ParticipantTeam",
        related_name="participants",
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return str(self.user)

    class Meta:
        """Meta class for Participant model."""
        app_label = "participants"
        db_table = "participant"


class ParticipantTeam(TimeStampedModel):
    """Model representing teams associated with different challenges.
    
    Each team can have multiple participants and is created by a user.
    """

    team_name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(User, null=True, on_delete=models.CASCADE)
    team_url = models.CharField(max_length=1000, default="", blank=True)

    def __str__(self):
        return str(self.team_name)

    def get_all_participants_email(self):
        """Get list of email addresses for all team participants.
        
        Returns:
            list: List of email addresses of team participants.
        """
        email_ids = Participant.objects.filter(team=self).values_list(
            "user__email", flat=True
        )
        return list(email_ids)

    class Meta:
        """Meta class for ParticipantTeam model."""
        app_label = "participants"
        db_table = "participant_team"
