# -*- coding: utf-8 -*-
from django.db.models.fields import related
from .compat import get_field, get_remote_field_to


class InvalidConstraint(Exception):
    def __init__(self, fields, *args, **kwargs):
        self.fields = fields
        super(InvalidConstraint, self).__init__(*args, **kwargs)


def _is_unique_field(field):
    if not field.unique:
        return False
    if field.primary_key:
        # Primary key fields should not generally be checked for unique constraints, except when the
        # primary key is a OneToOne mapping to an external table not via table inheritance, in which
        # case we don't want to create new objects which will overwrite existing objects.
        return (isinstance(field, related.OneToOneField) and
                not issubclass(field.model, get_remote_field_to(field)))
    else:
        return True


def unique_constraint(model, instance):
    error_fields = []
    for field in instance._meta.fields:
        if _is_unique_field(field):
            value = getattr(instance, field.name)

            # If the value is none and the field allows nulls, skip it
            if value is None and field.null:
                continue

            check = {field.name: value}

            if model._default_manager.filter(**check).exists():
                error_fields.append(field)
    if error_fields:
        raise InvalidConstraint(error_fields)


def unique_together_constraint(model, instance):
    if not instance._meta.unique_together:
        return
    error_fields = []
    for unique_fields in instance._meta.unique_together:
        check = {}
        for field_name in unique_fields:
            if not get_field(instance, field_name).primary_key:
                check[field_name] = getattr(instance, field_name)
        if all(e is None for e in check.values()):
            continue

        if model._default_manager.filter(**check).exists():
            error_fields.extend([
                get_field(instance, field_name)
                for field_name in unique_fields
            ])
    if error_fields:
        raise InvalidConstraint(error_fields)
