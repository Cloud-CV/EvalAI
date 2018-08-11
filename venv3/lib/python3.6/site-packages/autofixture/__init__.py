# -*- coding: utf-8 -*-
import sys
import warnings
from autofixture.base import AutoFixture
from autofixture.constraints import InvalidConstraint
from autofixture.compat import getargnames


if sys.version_info[0] < 3:
    string_types = basestring
else:
    string_types = str


__version__ = '0.12.1'


REGISTRY = {}


def register(model, autofixture, overwrite=False, fail_silently=False):
    '''
    Register a model with the registry.

    Arguments:

        *model* can be either a model class or a string that contains the model's
        app label and class name seperated by a dot, e.g. ``"app.ModelClass"``.

        *autofixture* is the :mod:`AutoFixture` subclass that shall be used to
        generated instances of *model*.

        By default :func:`register` will raise :exc:`ValueError` if the given
        *model* is already registered. You can overwrite the registered *model* if
        you pass ``True`` to the *overwrite* argument.

        The :exc:`ValueError` that is usually raised if a model is already
        registered can be suppressed by passing ``True`` to the *fail_silently*
        argument.
    '''
    from .compat import get_model

    if isinstance(model, string_types):
        model = get_model(*model.split('.', 1))
    if not overwrite and model in REGISTRY:
        if fail_silently:
            return
        raise ValueError(
            u'%s.%s is already registered. You can overwrite the registered '
            u'autofixture by providing the `overwrite` argument.' % (
                model._meta.app_label,
                model._meta.object_name,
            ))
    REGISTRY[model] = autofixture


def unregister(model_or_iterable, fail_silently=False):
    '''
    Remove one or more models from the autofixture registry.
    '''
    from django.db import models
    from .compat import get_model

    if issubclass(model_or_iterable, models.Model):
        model_or_iterable = [model_or_iterable]
    for model in model_or_iterable:
        if isinstance(model, string_types):
            model = get_model(*model.split('.', 1))
        try:
            del REGISTRY[model]
        except KeyError:
            if fail_silently:
                continue
            raise ValueError(
                u'The model %s.%s is not registered.' % (
                    model._meta.app_label,
                    model._meta.object_name,
                ))


def get(model, *args, **kwargs):
    '''
    Get an autofixture instance for the passed in *model* sing the either an
    appropiate autofixture that was :ref:`registry <registry>` or fall back
    to the default:class:`AutoFixture` class.  *model* can be a model class or
    its string representation (e.g.  ``"app.ModelClass"``).

    All positional and keyword arguments are passed to the autofixture
    constructor.
    '''
    from .compat import get_model

    if isinstance(model, string_types):
        model = get_model(*model.split('.', 1))
    if model in REGISTRY:
        return REGISTRY[model](model, *args, **kwargs)
    else:
        return AutoFixture(model, *args, **kwargs)


def create(model, count, *args, **kwargs):
    '''
    Create *count* instances of *model* using the either an appropiate
    autofixture that was :ref:`registry <registry>` or fall back to the
    default:class:`AutoFixture` class. *model* can be a model class or its
    string representation (e.g. ``"app.ModelClass"``).

    All positional and keyword arguments are passed to the autofixture
    constructor. It is demonstrated in the example below which will create ten
    superusers::

        import autofixture
        admins = autofixture.create('auth.User', 10, field_values={'is_superuser': True})

    .. note:: See :ref:`AutoFixture` for more information.

    :func:`create` will return a list of the created objects.
    '''
    from .compat import get_model

    if isinstance(model, string_types):
        model = get_model(*model.split('.', 1))
    if model in REGISTRY:
        autofixture_class = REGISTRY[model]
    else:
        autofixture_class = AutoFixture
    # Get keyword arguments that the create_one method accepts and pass them
    # into create_one instead of AutoFixture.__init__
    argnames = set(getargnames(autofixture_class.create_one))
    argnames -= set(['self'])
    create_kwargs = {}
    for argname in argnames:
        if argname in kwargs:
            create_kwargs[argname] = kwargs.pop(argname)
    autofixture = autofixture_class(model, *args, **kwargs)
    return autofixture.create(count, **create_kwargs)


def create_one(model, *args, **kwargs):
    '''
    :func:`create_one` is exactly the as the :func:`create` function but a
    shortcut if you only want to generate one model instance.

    The function returns the instanciated model.
    '''
    return create(model, 1, *args, **kwargs)[0]


LOADING = False

def autodiscover():
    '''
    Auto-discover INSTALLED_APPS autofixtures.py and tests.py modules and fail
    silently when not present. This forces an import on them to register any
    autofixture bits they may want.
    '''
    from .compat import importlib

    # Bail out if autodiscover didn't finish loading from a previous call so
    # that we avoid running autodiscover again when the URLconf is loaded by
    # the exception handler to resolve the handler500 view.  This prevents an
    # autofixtures.py module with errors from re-registering models and raising a
    # spurious AlreadyRegistered exception (see #8245).
    global LOADING
    if LOADING:
        return
    LOADING = True
    app_paths = {}

    # For each app, we need to look for an autofixture.py inside that app's
    # package. We can't use os.path here -- recall that modules may be
    # imported different ways (think zip files) -- so we need to get
    # the app's __path__ and look for autofixture.py on that path.

    # Step 1: find out the app's __path__ Import errors here will (and
    # should) bubble up, but a missing __path__ (which is legal, but weird)
    # fails silently -- apps that do weird things with __path__ might
    # need to roll their own autofixture registration.

    import imp
    try:
        from django.apps import apps

        for app_config in apps.get_app_configs():
            app_paths[app_config.name] = [app_config.path]

    except ImportError:
        # Django < 1.7
        from django.conf import settings

        for app in settings.INSTALLED_APPS:
            mod = importlib.import_module(app)
            try:
                app_paths[app] = mod.__path__
            except AttributeError:
                continue

    for app, app_path in app_paths.items():
        # Step 2: use imp.find_module to find the app's autofixtures.py. For some
        # reason imp.find_module raises ImportError if the app can't be found
        # but doesn't actually try to import the module. So skip this app if
        # its autofixtures.py doesn't exist
        try:
            file, _, _ = imp.find_module('autofixtures', app_path)
        except ImportError:
            continue
        else:
            if file:
                file.close()

        # Step 3: import the app's autofixtures file. If this has errors we want them
        # to bubble up.
        try:
            importlib.import_module("%s.autofixtures" % app)
        except Exception as e:
            warnings.warn(u'Error while importing %s.autofixtures: %r' %
                (app, e))

    for app, app_path in app_paths.items():
        try:
            file, _, _ = imp.find_module('tests', app_path)
        except ImportError:
            continue
        else:
            if file:
                file.close()

        try:
            importlib.import_module("%s.tests" % app)
        except Exception as e:
            warnings.warn(u'Error while importing %s.tests: %r' %
                (app, e))

    # autodiscover was successful, reset loading flag.
    LOADING = False
