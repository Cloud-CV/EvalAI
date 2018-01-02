from __future__ import unicode_literals

import logging

from django.db import models

from challenges.sender import publish_challenge_edit_message


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


def model_field_name(field_name, *args, **kwargs):
    """
    The decorator is used to pass model field names to create_post_model_field function for logging change.
    """
    def model_field_name_decorator(f, *args, **kwargs):
        def model_field_name_wrapper(sender, instance, **kwargs):
            f(sender, instance, field_name=field_name, **kwargs)
        return model_field_name_wrapper
    return model_field_name_decorator


def create_post_model_field(sender, instance, field_name, **kwargs):
    """
    When any model field value changes, it is used to log the change.
    """
    if getattr(instance, '_original_{}'.format(field_name)) is False:
        logger.info('{} for {} is added first time !'.format(field_name, instance.pk))
    else:
        logger.info('{} for {} changed !'.format(field_name, instance.pk))
    """
    Whenever evaluation_script or test_annotation file is changed we send the pk of the edited Challenge
    model to sender.py in challenges so it can publishes a challenge edit message to reload the changed
    files.
    """
    if field_name == "evaluation_script":
        challenge_pk = instance.pk
        publish_challenge_edit_message(challenge_pk)
    elif field_name == "test_annotation":
        challenge_pk = instance.challenge.pk
        publish_challenge_edit_message(challenge_pk)
