# -*- coding: utf-8 -*-
import warnings
from django.db.models import fields, ImageField
from django.db.models.fields import related
from django.utils.six import with_metaclass

import autofixture
from autofixture import constraints, generators, signals
from autofixture.values import Values
from autofixture.compat import (
    OrderedDict,
    get_GenericRelation,
    get_remote_field,
    get_remote_field_to,
    getargnames,
)


class CreateInstanceError(Exception):
    pass


class Link(object):
    '''
    Handles logic of following or generating foreignkeys and m2m relations.
    '''
    def __init__(self, fields=None, default=None):
        self.fields = {}
        self.subfields = {}
        self.default = default

        fields = fields or {}
        if fields is True:
            fields = {'ALL': None}
        if not isinstance(fields, dict):
            fields = dict([(v, None) for v in fields])
        for field, value in fields.items():
            try:
                fieldname, subfield = field.split('__', 1)
                self.subfields.setdefault(fieldname, {})[subfield] = value
            except ValueError:
                self.fields[field] = value

    def __getitem__(self, key):
        return self.fields.get(key,
            self.fields.get('ALL', self.default))

    def __iter__(self):
        for field in self.fields:
            yield field
        for key, value in self.subfields.items():
            yield '%s__%s' % (key, value)

    def __contains__(self, value):
        if 'ALL' in self.fields:
            return True
        if value in self.fields:
            return True
        return False

    def get_deep_links(self, field):
        if 'ALL' in self.fields:
            fields = {'ALL': self.fields['ALL']}
        else:
            fields = self.subfields.get(field, {})
            if 'ALL' in fields:
                fields = {'ALL': fields['ALL']}
        return Link(fields, default=self.default)


class AutoFixtureMetaclass(type):
    def __new__(mcs, name, bases, attrs):
        values = Values()
        for base in bases[::-1]:
            values += base.field_values
        values += Values(attrs.pop('Values', {}))
        values += attrs.get('field_values', Values())
        attrs['field_values'] = values
        return super(AutoFixtureMetaclass, mcs).__new__(mcs, name, bases, attrs)


class AutoFixtureBase(object):
    '''
    .. We don't support the following fields yet:

        * ``XMLField``
        * ``FileField``

        Patches are welcome.
    '''
    class IGNORE_FIELD(object):
        pass

    overwrite_defaults = False
    follow_fk = True
    generate_fk = False
    follow_m2m = {'ALL': (1,5)}
    generate_m2m = False

    none_p = 0.2
    tries = 1000

    field_to_generator = OrderedDict((
        (fields.BooleanField, generators.BooleanGenerator),
        (fields.NullBooleanField, generators.NullBooleanGenerator),
        (fields.DateTimeField, generators.DateTimeGenerator),
        (fields.DateField, generators.DateGenerator),
        (fields.PositiveSmallIntegerField, generators.PositiveSmallIntegerGenerator),
        (fields.PositiveIntegerField, generators.PositiveIntegerGenerator),
        (fields.SmallIntegerField, generators.SmallIntegerGenerator),
        (fields.IntegerField, generators.IntegerGenerator),
        (fields.FloatField, generators.FloatGenerator),
        (fields.IPAddressField, generators.IPAddressGenerator),
        (fields.GenericIPAddressField, generators.IPAddressGenerator),
        (fields.TextField, generators.LoremGenerator),
        (fields.TimeField, generators.TimeGenerator),
        (ImageField, generators.ImageGenerator),
    ))

    # UUIDField was added in Django 1.8
    if hasattr(fields, 'UUIDField'):
        field_to_generator[fields.UUIDField] = generators.UUIDGenerator

    field_values = Values()

    default_constraints = [
        constraints.unique_constraint,
        constraints.unique_together_constraint]

    def __init__(self, model,
            field_values=None, none_p=None, overwrite_defaults=None,
            constraints=None, follow_fk=None, generate_fk=None,
            follow_m2m=None, generate_m2m=None):
        '''
        Parameters:
            ``model``: A model class which is used to create the test data.

            ``field_values``: A dictionary with field names of ``model`` as
            keys. Values may be static values that are assigned to the field,
            a ``Generator`` instance that generates a value on the fly or a
            callable which takes no arguments and returns the wanted value.

            ``none_p``: The chance (between 0 and 1, 1 equals 100%) to
            assign ``None`` to nullable fields.

            ``overwrite_defaults``: All default values of fields are preserved
            by default. If set to ``True``, default values will be treated
            like any other field.

            ``constraints``: A list of callables. The constraints are used to
            verify if the created model instance may be used. The callable
            gets the actual model as first and the instance as second
            parameter. The instance is not populated yet at this moment.  The
            callable may raise an :exc:`InvalidConstraint` exception to
            indicate which fields violate the constraint.

            ``follow_fk``: A boolean value indicating if foreign keys should be
            set to random, already existing, instances of the related model.

            ``generate_fk``: A boolean which indicates if related models should
            also be created with random values. The *follow_fk* parameter will
            be ignored if *generate_fk* is set to ``True``.

            ``follow_m2m``: A tuple containing minium and maximum of model
            instances that are assigned to ``ManyToManyField``. No new
            instances will be created. Default is (1, 5).  You can ignore
            ``ManyToManyField`` fields by setting this parameter to ``False``.

            ``generate_m2m``: A tuple containing minimum and maximum number of
            model instance that are newly created and assigned to the
            ``ManyToManyField``. Default is ``False`` which disables the
            generation of new related instances. The value of ``follow_m2m``
            will be ignored if this parameter is set.
        '''
        self.model = model
        self.field_values = Values(self.__class__.field_values)
        self.field_values += Values(field_values)
        self.constraints = constraints or []
        if none_p is not None:
            self.none_p = none_p
        if overwrite_defaults is not None:
            self.overwrite_defaults = overwrite_defaults

        if follow_fk is not None:
            self.follow_fk = follow_fk
        if not isinstance(self.follow_fk, Link):
            self.follow_fk = Link(self.follow_fk)

        if generate_fk is not None:
            self.generate_fk = generate_fk
        if not isinstance(self.generate_fk, Link):
            self.generate_fk = Link(self.generate_fk)

        if follow_m2m is not None:
            if not isinstance(follow_m2m, dict):
                if follow_m2m:
                    follow_m2m = Link({'ALL': follow_m2m})
                else:
                    follow_m2m = Link(False)
            self.follow_m2m = follow_m2m
        if not isinstance(self.follow_m2m, Link):
            self.follow_m2m = Link(self.follow_m2m)

        if generate_m2m is not None:
            if not isinstance(generate_m2m, dict):
                if generate_m2m:
                    generate_m2m = Link({'ALL': generate_m2m})
                else:
                    generate_m2m = Link(False)
            self.generate_m2m = generate_m2m
        if not isinstance(self.generate_m2m, Link):
            self.generate_m2m = Link(self.generate_m2m)

        for constraint in self.default_constraints:
            self.add_constraint(constraint)

        self._field_generators = {}

        self.prepare_class()

    def prepare_class(self):
        '''
        This method is called after the :meth:`__init__` method. It has no
        semantic by default.
        '''
        pass

    def add_field_value(self, name, value):
        '''
        Pass a *value* that should be assigned to the field called *name*.
        Thats the same as specifying it in the *field_values* argument of the
        :meth:`constructor <autofixture.base.AutoFixture.__init__>`.
        '''
        self.field_values[name] = value

    def add_constraint(self, constraint):
        '''
        Add a *constraint* to the autofixture.
        '''
        self.constraints.append(constraint)

    def is_inheritance_parent(self, field):
        '''
        Checks if the field is the automatically created OneToOneField used by
        django mulit-table inheritance
        '''
        return (
            isinstance(field, related.OneToOneField) and
            field.primary_key and
            issubclass(field.model, get_remote_field_to(field))
        )

    def get_generator(self, field):
        '''
        Return a value generator based on the field instance that is passed to
        this method. This function may return ``None`` which means that the
        specified field will be ignored (e.g. if no matching generator was
        found).
        '''
        if isinstance(field, fields.AutoField):
            return None
        if self.is_inheritance_parent(field):
            return None
        if (
            field.default is not fields.NOT_PROVIDED and
            not self.overwrite_defaults and
            field.name not in self.field_values):
                return None
        kwargs = {}

        if field.name in self.field_values:
            value = self.field_values[field.name]
            if isinstance(value, generators.Generator):
                return value
            elif isinstance(value, AutoFixture):
                return generators.InstanceGenerator(autofixture=value)
            elif callable(value):
                return generators.CallableGenerator(value=value)
            return generators.StaticGenerator(value=value)

        if field.null:
            kwargs['empty_p'] = self.none_p
        if field.choices:
            return generators.ChoicesGenerator(choices=field.choices, **kwargs)
        if isinstance(field, related.ForeignKey):
            # if generate_fk is set, follow_fk is ignored.
            is_self_fk = (get_remote_field_to(field)().__class__ == self.model)
            if field.name in self.generate_fk and not is_self_fk:
                return generators.InstanceGenerator(
                    autofixture.get(
                        get_remote_field_to(field),
                        follow_fk=self.follow_fk.get_deep_links(field.name),
                        generate_fk=self.generate_fk.get_deep_links(field.name)),
                    limit_choices_to=get_remote_field(field).limit_choices_to)
            if field.name in self.follow_fk:
                selected = generators.InstanceSelector(
                    get_remote_field_to(field),
                    limit_choices_to=get_remote_field(field).limit_choices_to)
                if selected.get_value() is not None:
                    return selected
            if field.blank or field.null:
                return generators.NoneGenerator()
            if is_self_fk and not field.null:
                raise CreateInstanceError(
                    u'Cannot resolve self referencing field "%s" to "%s" without null=True' % (
                        field.name,
                        '%s.%s' % (
                            get_remote_field_to(field)._meta.app_label,
                            get_remote_field_to(field)._meta.object_name,
                        )
                ))
            raise CreateInstanceError(
                u'Cannot resolve ForeignKey "%s" to "%s". Provide either '
                u'"follow_fk" or "generate_fk" parameters.' % (
                    field.name,
                    '%s.%s' % (
                        get_remote_field_to(field)._meta.app_label,
                        get_remote_field_to(field)._meta.object_name,
                    )
            ))
        if isinstance(field, related.ManyToManyField):
            if field.name in self.generate_m2m:
                min_count, max_count = self.generate_m2m[field.name]
                return generators.MultipleInstanceGenerator(
                    autofixture.get(get_remote_field_to(field)),
                    limit_choices_to=get_remote_field(field).limit_choices_to,
                    min_count=min_count,
                    max_count=max_count,
                    **kwargs)
            if field.name in self.follow_m2m:
                min_count, max_count = self.follow_m2m[field.name]
                return generators.InstanceSelector(
                    get_remote_field_to(field),
                    limit_choices_to=get_remote_field(field).limit_choices_to,
                    min_count=min_count,
                    max_count=max_count,
                    **kwargs)
            if field.blank or field.null:
                return generators.StaticGenerator([])
            raise CreateInstanceError(
                u'Cannot assign instances of "%s" to ManyToManyField "%s". '
                u'Provide either "follow_m2m" or "generate_m2m" argument.' % (
                    '%s.%s' % (
                        get_remote_field_to(field)._meta.app_label,
                        get_remote_field_to(field)._meta.object_name,
                    ),
                    field.name,
            ))
        if isinstance(field, fields.FilePathField):
            return generators.FilePathGenerator(
                path=field.path, match=field.match, recursive=field.recursive,
                max_length=field.max_length, **kwargs)
        if isinstance(field, fields.CharField):
            if isinstance(field, fields.SlugField):
                generator = generators.SlugGenerator
            elif isinstance(field, fields.EmailField):
                return generators.EmailGenerator(
                    max_length=min(field.max_length, 30))
            elif isinstance(field, fields.URLField):
                return generators.URLGenerator(
                    max_length=min(field.max_length, 25))
            elif field.max_length > 15:
                return generators.LoremSentenceGenerator(
                    common=False,
                    max_length=field.max_length)
            else:
                generator = generators.StringGenerator
            return generator(max_length=field.max_length)
        if isinstance(field, fields.DecimalField):
            return generators.DecimalGenerator(
                decimal_places=field.decimal_places,
                max_digits=field.max_digits)
        if hasattr(fields, 'BigIntegerField'):
            if isinstance(field, fields.BigIntegerField):
                return generators.IntegerGenerator(
                    min_value=-field.MAX_BIGINT - 1,
                    max_value=field.MAX_BIGINT,
                    **kwargs)
        if isinstance(field, ImageField):
            return generators.ImageGenerator(storage=field.storage, **kwargs)
        for field_class, generator in self.field_to_generator.items():
            if isinstance(field, field_class):
                return generator(**kwargs)
        return None

    def get_value(self, field):
        '''
        Return a random value that can be assigned to the passed *field*
        instance.
        '''
        if field not in self._field_generators:
            self._field_generators[field] = self.get_generator(field)
        generator = self._field_generators[field]
        if generator is None:
            return self.IGNORE_FIELD
        value = generator()
        return value

    def process_field(self, instance, field):
        value = self.get_value(field)
        if value is self.IGNORE_FIELD:
            return
        setattr(instance, field.name, value)

    def process_m2m(self, instance, field):
        # check django's version number to determine how intermediary models
        # are checked if they are auto created or not.
        auto_created_through_model = False
        through = get_remote_field(field).through
        auto_created_through_model = through._meta.auto_created

        if auto_created_through_model:
            return self.process_field(instance, field)
        # if m2m relation has intermediary model:
        #   * only generate relation if 'generate_m2m' is given
        #   * first generate intermediary model and assign a newly created
        #     related model to the foreignkey
        kwargs = {}
        if field.name in self.generate_m2m:
            # get fk to related model on intermediary model
            related_fks = [fk
                for fk in through._meta.fields
                if isinstance(fk, related.ForeignKey) and \
                    get_remote_field_to(fk) is get_remote_field_to(field)]
            self_fks = [fk
                for fk in through._meta.fields
                if isinstance(fk, related.ForeignKey) and \
                    get_remote_field_to(fk) is self.model]
            assert len(related_fks) == 1
            assert len(self_fks) == 1
            related_fk = related_fks[0]
            self_fk = self_fks[0]
            min_count, max_count = self.generate_m2m[field.name]
            intermediary_model = generators.MultipleInstanceGenerator(
                AutoFixture(
                    through,
                    field_values={
                        self_fk.name: instance,
                        related_fk.name: generators.InstanceGenerator(
                            autofixture.get(get_remote_field_to(field)))
                    }),
                min_count=min_count,
                max_count=max_count,
                **kwargs).generate()

    def check_constrains(self, *args, **kwargs):
        raise TypeError(
            'This method was renamed recently, since it contains a typo. '
            'Please use the check_constraints method from now on.')

    def check_constraints(self, instance):
        '''
        Return fieldnames which need recalculation.
        '''
        recalc_fields = []
        for constraint in self.constraints:
            try:
                constraint(self.model, instance)
            except constraints.InvalidConstraint as e:
                recalc_fields.extend(e.fields)
        return recalc_fields

    def post_process_instance(self, instance, commit):
        '''
        Overwrite this method to modify the created *instance* before it gets
        returned by the :meth:`create` or :meth:`create_one`.
        It gets the generated *instance* and must return the modified
        instance. The *commit* parameter indicates the *commit* value that the
        user passed into the :meth:`create` method. It defaults to ``True``
        and should be respected, which means if it is set to ``False``, the
        *instance* should not be saved.
        '''
        return instance

    def pre_process_instance(self, instance):
        '''
        Same as :meth:`post_process_instance`, but it is being called before
        saving an *instance*.
        '''
        return instance

    def create_one(self, commit=True):
        '''
        Create and return one model instance. If *commit* is ``False`` the
        instance will not be saved and many to many relations will not be
        processed.

        Subclasses that override ``create_one`` can specify arbitrary keyword
        arguments. They will be passed through by the
        :meth:`autofixture.base.AutoFixture.create` method and the helper
        functions :func:`autofixture.create` and
        :func:`autofixture.create_one`.

        May raise :exc:`CreateInstanceError` if constraints are not satisfied.
        '''
        tries = self.tries
        instance = self.model()
        process = instance._meta.fields
        while process and tries > 0:
            for field in process:
                self.process_field(instance, field)
            process = self.check_constraints(instance)
            tries -= 1
        if tries == 0:
            raise CreateInstanceError(
                u'Cannot solve constraints for "%s", tried %d times. '
                u'Please check value generators or model constraints. '
                u'At least the following fields are involved: %s' % (
                    '%s.%s' % (
                        self.model._meta.app_label,
                        self.model._meta.object_name),
                    self.tries,
                    ', '.join([field.name for field in process]),
            ))

        instance = self.pre_process_instance(instance)

        if commit:
            instance.save()

            #to handle particular case of GenericRelation
            #in Django pre 1.6 it appears in .many_to_many
            many_to_many = [f for f in instance._meta.many_to_many
                            if not isinstance(f, get_GenericRelation())]
            for field in many_to_many:
                self.process_m2m(instance, field)
        signals.instance_created.send(
            sender=self,
            model=self.model,
            instance=instance,
            committed=commit)

        post_process_kwargs = {}
        if 'commit' in getargnames(self.post_process_instance):
            post_process_kwargs['commit'] = commit
        else:
            warnings.warn(
                "Subclasses of AutoFixture need to provide a `commit` "
                "argument for post_process_instance methods", DeprecationWarning)
        return self.post_process_instance(instance, **post_process_kwargs)

    def create(self, count=1, commit=True, **kwargs):
        '''
        Create and return ``count`` model instances. If *commit* is ``False``
        the instances will not be saved and many to many relations will not be
        processed.

        May raise ``CreateInstanceError`` if constraints are not satisfied.

        The method internally calls :meth:`create_one` to generate instances.
        '''
        object_list = []
        for i in range(count):
            instance = self.create_one(commit=commit, **kwargs)
            object_list.append(instance)
        return object_list

    def iter(self, count=1, commit=True):
        for i in range(count):
            yield self.create_one(commit=commit)

    def __iter__(self):
        yield self.create_one()


class AutoFixture(with_metaclass(AutoFixtureMetaclass, AutoFixtureBase)):
    pass
