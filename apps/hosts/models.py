from __future__ import unicode_literals
import uuid
from django.conf import settings
from base.models import TimeStampedModel
from django.contrib.auth.models import User
from django.db import models

# from challenges.models import (Challenge, )


class ChallengeHostTeam(TimeStampedModel):
    """
    Model representing the Host Team for a particular challenge
    """

    team_name = models.CharField(max_length=100, unique=True)
    created_by = models.ForeignKey(
        User,
        related_name="challenge_host_team_creator",
        on_delete=models.CASCADE,
    )
    team_url = models.CharField(max_length=1000, default="", blank=True)

    def __str__(self):
        return "{0}: {1}".format(self.team_name, self.created_by)

    def get_all_challenge_host_email(self):
        email_ids = ChallengeHost.objects.filter(team_name=self).values_list(
            "user__email", flat=True
        )
        return list(email_ids)

    class Meta:
        app_label = "hosts"
        db_table = "challenge_host_teams"


class ChallengeHost(TimeStampedModel):

    # permission options
    ADMIN = "Admin"
    READ = "Read"
    RESTRICTED = "Restricted"
    WRITE = "Write"

    # status options
    ACCEPTED = "Accepted"
    DENIED = "Denied"
    PENDING = "Pending"
    SELF = "Self"
    UNKNOWN = "Unknown"

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

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    team_name = models.ForeignKey(
        "ChallengeHostTeam", on_delete=models.CASCADE
    )
    status = models.CharField(max_length=30, choices=STATUS_OPTIONS)
    permissions = models.CharField(max_length=30, choices=PERMISSION_OPTIONS)

    def __str__(self):
        return "{0}:{1}:{2}".format(
            self.team_name, self.user, self.permissions
        )

    class Meta:
        app_label = "hosts"
        db_table = "challenge_host"

class ChallengeHostTeamInvitation(TimeStampedModel):
    """
    Model to store invitations to a challenge host team
    """
    email = models.EmailField(max_length=200)
    invitation_key = models.CharField(max_length=64, unique=True)
    status = models.CharField(
        max_length=30,
        choices=(
            ('pending', 'Pending'),
            ('accepted', 'Accepted'),
            ('declined', 'Declined'),
        ),
        default='pending'
    )
    team = models.ForeignKey(
        'ChallengeHostTeam',
        related_name='invitations',
        on_delete=models.CASCADE
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name='sent_host_invitations',
        on_delete=models.CASCADE
    )
    
    def generate_invitation_key(self):
        """Generate a unique invitation key"""
        return uuid.uuid4().hex
    
    def save(self, *args, **kwargs):
        if not self.invitation_key:
            self.invitation_key = self.generate_invitation_key()
        super(ChallengeHostTeamInvitation, self).save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.email} invitation to {self.team.team_name}'
    
    class Meta:
        app_label = "hosts"
        db_table = "challenge_host_team_invitations"

