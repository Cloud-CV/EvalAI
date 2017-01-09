from __future__ import unicode_literals

from django.db import models
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver

from base.models import (TimeStampedModel,)


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
    UNKNOWN = 'unknown'
    DENIED = 'denied'
    ACCEPTED = 'accepted'
    PENDING = 'pending'
    name = models.CharField(max_length=30)
    status = models.CharField(max_length=30, unique=True)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'accounts'


class Affiliation(TimeStampedModel):
    """
    Model to store the Affiliations
    """
    name = models.TextField()

    class Meta:
        app_label = 'accounts'
        db_table = 'affliation'


class UserAffliation(TimeStampedModel):
    """
    Model to relate the affiliations to a particular user
    """
    affiliation = models.ForeignKey(Affiliation)
    user = models.ForeignKey(User)

    class Meta:
        app_label = 'accounts'
        db_table = 'user_affiliation'


class Profile(TimeStampedModel):
    """
    Model to store profile of a user
    """
    user = models.OneToOneField(User)
    contact_number = models.CharField(max_length=10, blank=False, null=True)
    affiliation = models.CharField(max_length=512)
    receive_participated_challenge_updates = models.BooleanField(default=False)
    recieve_newsletter = models.BooleanField(default=False)

    def __unicode__(self):
        return '{}'.format(self.user)

    class Meta:
        app_label = 'accounts'
        db_table = 'user_profile'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
