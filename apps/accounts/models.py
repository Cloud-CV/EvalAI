from __future__ import unicode_literals

from base.models import TimeStampedModel
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


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
    github_url = models.URLField(max_length=200, null=True, blank=True)
    google_scholar_url = models.URLField(max_length=200, null=True, blank=True)
    linkedin_url = models.URLField(max_length=200, null=True, blank=True)
    # Student profile fields for challenges requiring complete profile
    address_street = models.CharField(max_length=500, null=True, blank=True)
    address_city = models.CharField(max_length=100, null=True, blank=True)
    address_state = models.CharField(max_length=100, null=True, blank=True)
    address_country = models.CharField(max_length=100, null=True, blank=True)
    university = models.CharField(max_length=512, null=True, blank=True)
    email_bounced = models.BooleanField(default=False)
    email_bounced_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "{}".format(self.user)

    @property
    def is_complete(self):
        """
        Check if the user's profile is complete for challenges requiring complete profile.
        A complete profile requires: first_name, last_name, address_street, address_city,
        address_state, address_country, and university.
        """
        user = self.user
        required_fields = [
            user.first_name,
            user.last_name,
            self.address_street,
            self.address_city,
            self.address_state,
            self.address_country,
            self.university,
        ]
        return all(field and field.strip() for field in required_fields)

    def get_full_name(self):
        """Returns the full name of the user."""
        return "{} {}".format(
            self.user.first_name, self.user.last_name
        ).strip()

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
