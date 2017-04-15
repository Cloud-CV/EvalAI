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
        app_label = 'base'


"""
The decorator below is used to pass model field names to django signals function.
"""


def extra_args(field_name, *args, **kwargs):
    def extra_args_decorator(f, *args, **kwargs):
        def extra_args_wrapper(sender, instance, **kwargs):
            f(sender, instance, field_name=field_name, **kwargs)
        return extra_args_wrapper
    return extra_args_decorator


"""
The function below is used to log the change when any attribute of model field instance is changed.
"""


def create_post_model_field(sender, instance, field_name, **kwargs):
    if getattr(instance, "_original_{}".format(field_name)) is False:
        logger.info("{} is added first time !".format(field_name))
    else:
        logger.info("{} is changed !".format(field_name))
