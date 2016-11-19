from __future__ import unicode_literals

from django.db import models
from django.contrib.auth.models import User


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-managed `created_at` and
    `modified_at` fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = 'accounts'


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
