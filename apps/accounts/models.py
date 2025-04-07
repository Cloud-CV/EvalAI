"""Models for user profile, JWT tokens, and user invitation status."""

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from base.models import TimeStampedModel


class UserStatus(TimeStampedModel):
    """
    Model representing the status of a user being invited by another
    user to host/participate in a competition.

    .. note::
        There are four different statuses:
            - Unknown
            - Denied
            - Accepted
            - Pending
    """

    UNKNOWN = "unknown"
    DENIED = "denied"
    ACCEPTED = "accepted"
    PENDING = "pending"

    name = models.CharField(max_length=30)
    status = models.CharField(max_length=30, unique=True)

    def __str__(self) -> str:
        return str(self.name)

    class Meta:
        app_label = "accounts"


class Profile(TimeStampedModel):
    """
    Model to store the profile information of a user.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=10, null=True)
    affiliation = models.CharField(max_length=512)
    receive_participated_challenge_updates = models.BooleanField(default=False)
    recieve_newsletter = models.BooleanField(default=False)
    github_url = models.URLField(max_length=200, null=True, blank=True)
    google_scholar_url = models.URLField(max_length=200, null=True, blank=True)
    linkedin_url = models.URLField(max_length=200, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.user}"

    class Meta:
        app_label = "accounts"
        db_table = "user_profile"


class JwtToken(TimeStampedModel):
    """
    Model to store JWT tokens for a user.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=512, null=True)
    refresh_token = models.CharField(max_length=512, null=True)

    def __str__(self) -> str:
        return f"{self.user}"

    class Meta:
        app_label = "accounts"
        db_table = "jwt_token"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Signal receiver to create Profile when a new User is created.
    """
    if created:
        Profile.objects.create(user=instance)
        
