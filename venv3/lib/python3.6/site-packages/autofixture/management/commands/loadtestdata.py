# -*- coding: utf-8 -*-
'''
Use the ``loadtestdata`` command like this::

    django-admin.py loadtestdata [options] app.Model:# [app.Model:# ...]

Its nearly self explanatory. Supply names of models, prefixed with their app
name. After that, place a colon and tell the command how many objects you want
to create. Here is an example of how to create three categories and twenty
entries for you blogging app::

    django-admin.py loadtestdata blog.Category:3 blog.Entry:20

Voila! You have ready to use testing data populated to your database. The
model fields are filled with data by producing randomly generated values
depending on the type of the field. E.g. text fields are filled with lorem
ipsum dummies, date fields are populated with random dates from the last
years etc.

There are a few command line options available. Mainly to control the
behavior of related fields. If foreingkey or many to many fields should be
populated with existing data or if the related models are also generated on
the fly. Please have a look at the help page of the command for more
information::

    django-admin.py help loadtestdata
'''
import django
from django.utils.encoding import smart_text
from django.db import models
from django.core.management.base import BaseCommand, CommandError
import autofixture
from autofixture import signals
from ...compat import atomic
from ...compat import importlib
from ...compat import get_model

if django.VERSION < (1, 9):
    from optparse import make_option
else:
    def make_option(*args, **kwargs):
        return {'args': args, 'kwargs': kwargs}


class Command(BaseCommand):
    help = 'Create random model instances for testing purposes.'
    args = 'app.Model:# [app.Model:# ...]'

    def __init__(self, *args, **kwargs):
        params = (
            make_option('-d', '--overwrite-defaults', action='store_true',
                        dest='overwrite_defaults', default=None,
                        help=u'Generate values for fields with default values. Default is to use ' +
                        'default values.'),
            make_option('--no-follow-fk', action='store_true', dest='no_follow_fk', default=None,
                        help=u'Ignore foreignkeys while creating model instances.'),
            make_option('--generate-fk', action='store', dest='generate_fk', default=None,
                        help=u'Do not use already existing instances for ForeignKey relations. ' +
                        'Create new instances instead. You can specify a comma sperated list of ' +
                        'field names or ALL to indicate that all foreignkeys should be generated ' +
                        'automatically.'),
            make_option('--no-follow-m2m', action='store_true', dest='no_follow_m2m', default=None,
                        help=u'Ignore many to many fields while creating model instances.'),
            make_option('--follow-m2m', action='store', dest='follow_m2m', default=None,
                        help=u'Specify minimum and maximum number of instances that are assigned ' +
                        'to  a m2m relation. Use two, colon separated numbers in the form of: ' +
                        'min,max. Default is 1,5.\nYou can limit following of many to many ' +
                        'relations to specific fields using the following format:\nfield1:min:max' +
                        ',field2:min:max ...'),
            make_option('--generate-m2m', action='store', dest='generate_m2m', default=None,
                        help=u'Specify minimum and maximum number of instances that are newly ' +
                        'created and assigned to a m2m relation. Use two, colon separated ' +
                        'numbers in the form of: min:max. Default is to not generate many to ' +
                        'many related models automatically. You can select specific of many to ' +
                        'many fields which are automatically generated. Use the following ' +
                        'format:\nfield1:min:max,field2:min:max ...'),
            make_option('-u', '--use', action='store', dest='use', default='',
                        help=u'Specify a autofixture subclass that is used to create the test ' +
                        'data. E.g. myapp.autofixtures.MyAutoFixture')
        )

        if django.VERSION < (1, 9):
            self.option_list = BaseCommand.option_list + params
        else:
            self.argument_params = params
        super(Command, self).__init__(*args, **kwargs)

    def add_arguments(self, parser):
        parser.add_argument('args', nargs='+')
        for option in self.argument_params:
            parser.add_argument(*option['args'], **option['kwargs'])

    def format_output(self, obj):
        output = smart_text(obj)
        if len(output) > 50:
            output = u'{0} ...'.format(output[:50])
        return output

    def print_instance(self, sender, model, instance, **kwargs):
        if self.verbosity < 1:
            return
        print(u'{0}(pk={1}): {2}'.format(
            '.'.join((
                model._meta.app_label,
                model._meta.object_name)),
            smart_text(instance.pk),
            self.format_output(instance),
        ))
        if self.verbosity < 2:
            return
        for field in instance._meta.fields:
            if isinstance(field, models.ForeignKey):
                obj = getattr(instance, field.name)
                if isinstance(obj, models.Model):
                    print('|   {0} (pk={1}): {2}'.format(
                        field.name,
                        obj.pk,
                        self.format_output(obj)))
        for field in instance._meta.many_to_many:
            qs = getattr(instance, field.name).all()
            if qs.exists():
                print('|   {0} (count={1}):'.format(
                    field.name,
                    qs.count()))
                for obj in qs:
                    print('|   |   (pk={0}): {1}'.format(
                        obj.pk,
                        self.format_output(obj)))

    @atomic
    def handle(self, *attrs, **options):
        error_option = None
        #
        # follow options
        #
        if options['no_follow_fk'] is None:
            follow_fk = None
        else:
            follow_fk = False
        if options['no_follow_m2m'] is None:
            follow_m2m = None
            # this is the only chance for the follow_m2m options to be parsed
            if options['follow_m2m']:
                try:
                    value = options['follow_m2m'].split(',')
                    if len(value) == 1 and value[0].count(':') == 1:
                        follow_m2m = [int(i) for i in value[0].split(':')]
                    else:
                        follow_m2m = {}
                        for field in value:
                            key, minval, maxval = field.split(':')
                            follow_m2m[key] = int(minval), int(maxval)
                except ValueError:
                    error_option = '--follow-m2m={0}'.format(options['follow_m2m'])
        else:
            follow_m2m = False
        #
        # generation options
        #
        if options['generate_fk'] is None:
            generate_fk = None
        else:
            generate_fk = options['generate_fk'].split(',')
        generate_m2m = None
        if options['generate_m2m']:
            try:
                value = [v for v in options['generate_m2m'].split(',') if v]
                if len(value) == 1 and value[0].count(':') == 1:
                    generate_m2m = [int(i) for i in value[0].split(':')]
                else:
                    generate_m2m = {}
                    for field in value:
                        key, minval, maxval = field.split(':')
                        generate_m2m[key] = int(minval), int(maxval)
            except ValueError:
                error_option = '--generate-m2m={0}'.format(options['generate_m2m'])

        if error_option:
            raise CommandError(
                u'Invalid option {0}\nExpected: {1}=field:min:max,field2:min:max... (min and max must be numbers)'.format(
                    error_option,
                    error_option.split('=', 1)[0]))

        use = options['use']
        if use:
            use = use.split('.')
            use = getattr(importlib.import_module('.'.join(use[:-1])), use[-1])

        overwrite_defaults = options['overwrite_defaults']
        self.verbosity = int(options['verbosity'])

        models = []
        for attr in attrs:
            try:
                app_label, model_label = attr.split('.')
                model_label, count = model_label.split(':')
                count = int(count)
            except ValueError:
                raise CommandError(
                    u'Invalid argument: {0}\nExpected: app_label.ModelName:count (count must be a number)'.format(attr))
            model = get_model(app_label, model_label)
            if not model:
                raise CommandError(
                    u'Unknown model: {0}.{1}'.format(app_label, model_label))
            models.append((model, count))

        signals.instance_created.connect(
            self.print_instance)

        autofixture.autodiscover()

        kwargs = {
            'overwrite_defaults': overwrite_defaults,
            'follow_fk': follow_fk,
            'generate_fk': generate_fk,
            'follow_m2m': follow_m2m,
            'generate_m2m': generate_m2m,
        }

        for model, count in models:
            if use:
                fixture = use(model, **kwargs)
                fixture.create(count)
            else:
                autofixture.create(model, count, **kwargs)

