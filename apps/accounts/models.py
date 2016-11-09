from __future__ import unicode_literals

from django.db import models


class TimeStampedModel(models.Model):
    """ TimeStampedModel
    An abstract base class model that provides self-managed "created" and
    "modified" fields.
    """
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserStatus(TimeStampedModel):
    """
    Model representing the status of a user being invited by other user to host/participate in a competition
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
