from __future__ import unicode_literals

from django.db import models

# Create your models here.

class UserStatus(models.Model):
    """
    Model representing the status of a user when invited for hosting/participating a competition
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
    status = models.CharField(max_length=30,unique=True)

    def __unicode__(self):
        return self.name
