from __future__ import unicode_literals

from django.db import models

from base.models import (TimeStampedModel, )


class Contact(TimeStampedModel):
    """Model representing details of User submitting queries."""
    name = models.CharField(max_length=100,)
    email = models.EmailField(max_length=70,)
    message = models.CharField(max_length=500,)

    def __unicode__(self):
        return "%s: %s: %s" % (self.name, self.email, self.message)

    class Meta:
        app_label = 'contactUs'
        db_table = 'contact'
