from __future__ import unicode_literals

import uuid
from datetime import timedelta

from base.models import TimeStampedModel
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

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
            ("pending", "Pending"),
            ("accepted", "Accepted"),
            ("declined", "Declined"),
            ("expired", "Expired"),  # Added expired status
        ),
        default="pending",
    )
    team = models.ForeignKey(
        "ChallengeHostTeam",
        related_name="invitations",
        on_delete=models.CASCADE,
    )
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="sent_host_invitations",
        on_delete=models.CASCADE,
    )

    INVITATION_EXPIRY_DAYS = getattr(settings, "INVITATION_EXPIRY_DAYS", 7)

    def generate_invitation_key(self):
        """Generate a unique invitation key"""
        return uuid.uuid4().hex

    def save(self, *args, **kwargs):
        if not self.invitation_key:
            self.invitation_key = self.generate_invitation_key()
        super(ChallengeHostTeamInvitation, self).save(*args, **kwargs)

    def is_expired(self):
        """
        Determine whether this invitation has expired.

        Returns True if the invitation creation date plus the expiration
        period is less than or equal to the current date/time.
        """
        expiration_date = self.created_at + timedelta(
            days=self.INVITATION_EXPIRY_DAYS
        )
        return timezone.now() > expiration_date

    def is_usable(self):
        """
        Return whether this invitation is still valid for accepting.

        An invitation is usable if it's in 'pending' status and hasn't expired.
        """
        return self.status == "pending" and not self.is_expired()

    def mark_as_expired(self):
        """Mark the invitation as expired if it's currently pending"""
        if self.status == "pending" and self.is_expired():
            self.status = "expired"
            self.save(update_fields=["status"])

    @classmethod
    def expire_old_invitations(cls):
        """
        Class method to expire all pending invitations that have passed their expiration date.
        This can be called by a scheduled task (e.g., Celery).
        """
        pending_invitations = cls.objects.filter(status="pending")
        for invitation in pending_invitations:
            if invitation.is_expired():
                invitation.status = "expired"
                invitation.save(update_fields=["status"])

    def __str__(self):
        return f"{self.email} invitation to {self.team.team_name}"

    class Meta:
        app_label = "hosts"
        db_table = "challenge_host_team_invitations"
