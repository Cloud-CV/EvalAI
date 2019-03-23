from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from base.models import TimeStampedModel
from challenges.models import Challenge
from hosts.models import ChallengeHost


class UserStatus(TimeStampedModel):
    """
    Model representing the status of a user being invited by
    other user to host/participate in a competition
    .. note::
        There are four different status:
            - Unknown.
            - Denied.
            - Accepted
            - Pending.
    """

    UNKNOWN = "unknown"
    DENIED = "denied"
    ACCEPTED = "accepted"
    PENDING = "pending"
    name = models.CharField(max_length=30)
    status = models.CharField(max_length=30, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        app_label = "accounts"


class Profile(TimeStampedModel):
    """
    Model to store profile of a user
    """

    user = models.OneToOneField(User)
    contact_number = models.CharField(max_length=10, blank=False, null=True)
    affiliation = models.CharField(max_length=512)
    receive_participated_challenge_updates = models.BooleanField(default=False)
    recieve_newsletter = models.BooleanField(default=False)

    def __str__(self):
        return "{}".format(self.user)

    class Meta:
        app_label = "accounts"
        db_table = "user_profile"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class InviteUserToChallenge(TimeStampedModel):
    """
    Model to store invitation status
    """

    ACCEPTED = "accepted"
    PENDING = "pending"

    STATUS_OPTIONS = ((ACCEPTED, ACCEPTED), (PENDING, PENDING))
    email = models.EmailField(max_length=200)
    invitation_key = models.CharField(max_length=200)
    status = models.CharField(
        max_length=30, choices=STATUS_OPTIONS, db_index=True
    )
    challenge = models.ForeignKey(Challenge, related_name="challenge")
    user = models.ForeignKey(User)
    invited_by = models.ForeignKey(ChallengeHost)

    class Meta:
        app_label = "accounts"
        db_table = "invite_user_to_challenge"

    def __str__(self):
        """Returns the email of the user"""
        return self.email
