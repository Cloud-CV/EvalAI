from __future__ import unicode_literals

from django.db import models

from base.models import (TimeStampedModel, )


class Contact(TimeStampedModel):
    """Model representing details of User submitting queries."""
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=70)
    message = models.CharField(max_length=500)

    def __unicode__(self):
        return "%s: %s: %s" % (self.name, self.email, self.message)

    class Meta:
        app_label = 'web'
        db_table = 'contact'


class Team(models.Model):
    """Model representing details of Team"""

    # Team Type Options
    CORE_TEAM = 'Core Team'
    CONTRIBUTOR = 'Contributor'

    TEAM_TYPE_OPTIONS = (
        (CORE_TEAM, CORE_TEAM),
        (CONTRIBUTOR, CONTRIBUTOR),
    )

    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=70)
    headshot = models.ImageField(upload_to="headshots", null=True, blank=True)
    visible = models.BooleanField(default=True)
    github_url = models.URLField(max_length=200)
    linkedin_url = models.URLField(max_length=200)
    personal_website = models.URLField(max_length=200)
    team_type = models.CharField(choices=TEAM_TYPE_OPTIONS, max_length=50)

    def __unicode__(self):
        return self.name

    class Meta:
        app_label = 'web'
        db_table = 'teams'

