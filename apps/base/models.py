from __future__ import unicode_literals

from django.db import models


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


def extra_args(fragment_name, *args, **kwargs):
    def extra_args_inner1(f, *args, **kwargs):
        def extra_args_inner2(sender, instance, **kwargs):
            f(sender, instance, fragment_name=fragment_name, **kwargs)
        return extra_args_inner2
    return extra_args_inner1


def create_post_model_field(sender, instance, fragment_name, **kwargs):
    if getattr(instance, "_original_" + str(fragment_name)) is False:
        print str(fragment_name) + " is added first time !"
    else:
        print str(fragment_name) + " is changed !"
