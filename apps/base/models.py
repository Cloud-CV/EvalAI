from __future__ import unicode_literals

import logging

from django.db import models

# Get an instance of a logger
logger = logging.getLogger(__name__)


class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-managed `created_at` and
    `modified_at` fields.
    """

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        app_label = "base"


def model_field_name(field_name, *args, **kwargs):
    """
    The decorator is used to pass model field names to create_post_model_field function for logging change.
    """

    def model_field_name_decorator(f, *args, **kwargs):
        def model_field_name_wrapper(sender, instance, **kwargs):
            f(sender, instance, field_name=field_name, **kwargs)

        return model_field_name_wrapper

    return model_field_name_decorator
