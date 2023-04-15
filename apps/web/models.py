from __future__ import unicode_literals

from urllib.parse import urlparse

from base.models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.db import models


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

class Contact(TimeStampedModel):
    """Model representing details of User submitting queries."""

    PENDING = "Pending"
    RESOLVED = "Resolved"

    STATUS_OPTIONS = ((PENDING, PENDING), (RESOLVED, RESOLVED))
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=70)
    message = models.CharField(max_length=500)
    status = models.CharField(
        max_length=30, choices=STATUS_OPTIONS, default=PENDING
    )

    def __str__(self):
        return "{0}: {1}: {2}".format(self.name, self.email, self.message)

    class Meta:
        app_label = "web"
        db_table = "contact"


class Subscribers(TimeStampedModel):
    """Model representing subbscribed user's email"""

    email = models.EmailField(max_length=70)

    def __str__(self):
        return "{}".format(self.email)

    class Meta:
        app_label = "web"
        db_table = "subscribers"
        verbose_name_plural = "Subscribers"


class Team(models.Model):
    """Model representing details of Team"""

    # Team Type Options
    CORE_TEAM = "Core Team"
    CONTRIBUTOR = "Contributor"

    TEAM_TYPE_OPTIONS = ((CORE_TEAM, CORE_TEAM), (CONTRIBUTOR, CONTRIBUTOR))

    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=70, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    headshot = models.ImageField(upload_to="headshots", null=True, blank=True)
    visible = models.BooleanField(default=False)
    github_url = models.CharField(
        max_length=200, null=True, blank=True, validators=[validate_github_url]
    )
    linkedin_url = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        validators=[validate_linkedin_url],
    )
    personal_website = models.CharField(max_length=200, null=True, blank=True)
    background_image = models.ImageField(
        upload_to="bg-images", null=True, blank=True
    )
    team_type = models.CharField(choices=TEAM_TYPE_OPTIONS, max_length=50)
    position = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name

    class Meta:
        app_label = "web"
        db_table = "teams"
