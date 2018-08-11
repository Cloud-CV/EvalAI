import django


def get_GenericForeignKey():
    try:
        from django.contrib.contenttypes.fields import GenericForeignKey
    # For Django 1.6 and earlier
    except ImportError:
        from django.contrib.contenttypes.generic import GenericForeignKey
    return GenericForeignKey


def get_GenericRelation():
    try:
        from django.contrib.contenttypes.fields import GenericRelation
    # For Django 1.6 and earlier
    except ImportError:
        from django.contrib.contenttypes.generic import GenericRelation
    return GenericRelation

try:
    from collections import OrderedDict
except ImportError:
    from django.utils.datastructures import SortedDict as OrderedDict


try:
    import importlib
except ImportError:
    from django.utils import importlib


try:
    from django.db.transaction import atomic
# For django 1.5 and earlier
except ImportError:
    from django.db.transaction import commit_on_success as atomic


try:
    from django.apps import apps
    get_model = apps.get_model
except ImportError:
    from django.db.models import get_model


def get_field(model, field_name):
    if django.VERSION < (1, 8):
        return model._meta.get_field_by_name(field_name)[0]
    else:
        return model._meta.get_field(field_name)


def get_remote_field(field):
    if django.VERSION < (1, 9):
        return field.rel
    else:
        return field.remote_field


def get_remote_field_to(field):
    if django.VERSION < (1, 9):
        return field.rel.to
    else:
        return field.remote_field.model


try:
    # added in Python 3.0
    from inspect import signature
    def getargnames(callable):
        return list(signature(callable).parameters.keys())

except ImportError:
    # loud DeprecationWarnings in 3.5
    from inspect import getargspec
    def getargnames(callable):
        return getargspec(callable).args
