from __future__ import unicode_literals

from urllib.parse import urlparse

from base.models import TimeStampedModel
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


def validate_github_url(value):
    if not value:
        return
    obj = urlparse(value)
    if not obj.hostname in ("github.com"):
        raise ValidationError(f"Only URLs from GitHub are allowed")


def validate_linkedin_url(value):
    if not value:
        return
    obj = urlparse(value)
    if not obj.hostname in ("linkedin.com", "www.linkedin.com", "linkedin.in"):
        raise ValidationError(f"Only URLs from LinkedIn are allowed")


def validate_google_scholar_url(value):
    if not value:
        return
    obj = urlparse(value)
    if not obj.hostname in ("scholar.google.com", "www.scholar.google.com"):
        raise ValidationError(f"Only URLs from Google Scholar are allowed")


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

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=10, blank=False, null=True)
    affiliation = models.CharField(max_length=512)
    receive_participated_challenge_updates = models.BooleanField(default=False)
    recieve_newsletter = models.BooleanField(default=False)
    github_url = models.URLField(
        max_length=200, null=True, blank=True, validators=[validate_github_url]
    )
    google_scholar_url = models.URLField(
        max_length=200,
        null=True,
        blank=True,
        validators=[validate_google_scholar_url],
    )
    linkedin_url = models.URLField(
        max_length=200,
        null=True,
        blank=True,
        validators=[validate_linkedin_url],
    )

    def __str__(self):
        return "{}".format(self.user)

    class Meta:
        app_label = "accounts"
        db_table = "user_profile"


class JwtToken(TimeStampedModel):
    """
    Model to store jwt tokens of a user
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    access_token = models.CharField(max_length=512, blank=False, null=True)
    refresh_token = models.CharField(max_length=512, blank=False, null=True)

    def __str__(self):
        return "{}".format(self.user)

    class Meta:
        app_label = "accounts"
        db_table = "jwt_token"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
