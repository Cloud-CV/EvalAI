"""All pytest-django fixtures"""

from __future__ import with_statement

import os

import pytest

from . import live_server_helper

from .django_compat import is_django_unittest
from .pytest_compat import getfixturevalue

from .lazy_django import get_django_version, skip_if_no_django

__all__ = ['django_db_setup', 'db', 'transactional_db', 'admin_user',
           'django_user_model', 'django_username_field',
           'client', 'admin_client', 'rf', 'settings', 'live_server',
           '_live_server_helper']


@pytest.fixture(scope='session')
def django_db_modify_db_settings_xdist_suffix(request):
    skip_if_no_django()

    from django.conf import settings

    for db_settings in settings.DATABASES.values():

        try:
            test_name = db_settings['TEST']['NAME']
        except KeyError:
            test_name = None

        if not test_name:
            if db_settings['ENGINE'] == 'django.db.backends.sqlite3':
                return ':memory:'
            else:
                test_name = 'test_{}'.format(db_settings['NAME'])

        # Put a suffix like _gw0, _gw1 etc on xdist processes
        xdist_suffix = getattr(request.config, 'slaveinput', {}).get('slaveid')
        if test_name != ':memory:' and xdist_suffix is not None:
            test_name = '{}_{}'.format(test_name, xdist_suffix)

        db_settings.setdefault('TEST', {})
        db_settings['TEST']['NAME'] = test_name


@pytest.fixture(scope='session')
def django_db_modify_db_settings(django_db_modify_db_settings_xdist_suffix):
    skip_if_no_django()


@pytest.fixture(scope='session')
def django_db_use_migrations(request):
    return not request.config.getvalue('nomigrations')


@pytest.fixture(scope='session')
def django_db_keepdb(request):
    return (request.config.getvalue('reuse_db') and not
            request.config.getvalue('create_db'))


@pytest.fixture(scope='session')
def django_db_setup(
    request,
    django_test_environment,
    django_db_blocker,
    django_db_use_migrations,
    django_db_keepdb,
    django_db_modify_db_settings,
):
    """Top level fixture to ensure test databases are available"""
    from .compat import setup_databases, teardown_databases

    setup_databases_args = {}

    if not django_db_use_migrations:
        _disable_native_migrations()

    if django_db_keepdb:
        if get_django_version() >= (1, 8):
            setup_databases_args['keepdb'] = True
        else:
            # Django 1.7 compatibility
            from .db_reuse import monkey_patch_creation_for_db_reuse

            with django_db_blocker.unblock():
                monkey_patch_creation_for_db_reuse()

    with django_db_blocker.unblock():
        db_cfg = setup_databases(
            verbosity=pytest.config.option.verbose,
            interactive=False,
            **setup_databases_args
        )

    def teardown_database():
        with django_db_blocker.unblock():
            teardown_databases(
                db_cfg,
                verbosity=pytest.config.option.verbose,
            )

    if not django_db_keepdb:
        request.addfinalizer(teardown_database)


def _django_db_fixture_helper(transactional, request, django_db_blocker):
    if is_django_unittest(request):
        return

    if not transactional and 'live_server' in request.funcargnames:
        # Do nothing, we get called with transactional=True, too.
        return

    django_db_blocker.unblock()
    request.addfinalizer(django_db_blocker.restore)

    if transactional:
        from django.test import TransactionTestCase as django_case
    else:
        from django.test import TestCase as django_case

    test_case = django_case(methodName='__init__')
    test_case._pre_setup()
    request.addfinalizer(test_case._post_teardown)


def _disable_native_migrations():
    from django.conf import settings
    from .migrations import DisableMigrations

    settings.MIGRATION_MODULES = DisableMigrations()


# ############### User visible fixtures ################

@pytest.fixture(scope='function')
def db(request, django_db_setup, django_db_blocker):
    """Require a django test database

    This database will be setup with the default fixtures and will have
    the transaction management disabled. At the end of the test the outer
    transaction that wraps the test itself will be rolled back to undo any
    changes to the database (in case the backend supports transactions).
    This is more limited than the ``transactional_db`` resource but
    faster.

    If both this and ``transactional_db`` are requested then the
    database setup will behave as only ``transactional_db`` was
    requested.
    """
    if 'transactional_db' in request.funcargnames \
            or 'live_server' in request.funcargnames:
        getfixturevalue(request, 'transactional_db')
    else:
        _django_db_fixture_helper(False, request, django_db_blocker)


@pytest.fixture(scope='function')
def transactional_db(request, django_db_setup, django_db_blocker):
    """Require a django test database with transaction support

    This will re-initialise the django database for each test and is
    thus slower than the normal ``db`` fixture.

    If you want to use the database with transactions you must request
    this resource.  If both this and ``db`` are requested then the
    database setup will behave as only ``transactional_db`` was
    requested.
    """
    _django_db_fixture_helper(True, request, django_db_blocker)


@pytest.fixture()
def client():
    """A Django test client instance."""
    skip_if_no_django()

    from django.test.client import Client

    return Client()


@pytest.fixture()
def django_user_model(db):
    """The class of Django's user model."""
    from django.contrib.auth import get_user_model
    return get_user_model()


@pytest.fixture()
def django_username_field(django_user_model):
    """The fieldname for the username used with Django's user model."""
    return django_user_model.USERNAME_FIELD


@pytest.fixture()
def admin_user(db, django_user_model, django_username_field):
    """A Django admin user.

    This uses an existing user with username "admin", or creates a new one with
    password "password".
    """
    UserModel = django_user_model
    username_field = django_username_field

    try:
        user = UserModel._default_manager.get(**{username_field: 'admin'})
    except UserModel.DoesNotExist:
        extra_fields = {}
        if username_field != 'username':
            extra_fields[username_field] = 'admin'
        user = UserModel._default_manager.create_superuser(
            'admin', 'admin@example.com', 'password', **extra_fields)
    return user


@pytest.fixture()
def admin_client(db, admin_user):
    """A Django test client logged in as an admin user."""
    from django.test.client import Client

    client = Client()
    client.login(username=admin_user.username, password='password')
    return client


@pytest.fixture()
def rf():
    """RequestFactory instance"""
    skip_if_no_django()

    from django.test.client import RequestFactory

    return RequestFactory()


class SettingsWrapper(object):
    _to_restore = []

    def __delattr__(self, attr):
        from django.test import override_settings
        override = override_settings()
        override.enable()
        from django.conf import settings
        delattr(settings, attr)

        self._to_restore.append(override)

    def __setattr__(self, attr, value):
        from django.test import override_settings
        override = override_settings(**{
            attr: value
        })
        override.enable()
        self._to_restore.append(override)

    def __getattr__(self, item):
        from django.conf import settings
        return getattr(settings, item)

    def finalize(self):
        for override in reversed(self._to_restore):
            override.disable()

        del self._to_restore[:]


@pytest.yield_fixture()
def settings():
    """A Django settings object which restores changes after the testrun"""
    skip_if_no_django()

    wrapper = SettingsWrapper()
    yield wrapper
    wrapper.finalize()


@pytest.fixture(scope='session')
def live_server(request):
    """Run a live Django server in the background during tests

    The address the server is started from is taken from the
    --liveserver command line option or if this is not provided from
    the DJANGO_LIVE_TEST_SERVER_ADDRESS environment variable.  If
    neither is provided ``localhost:8081,8100-8200`` is used.  See the
    Django documentation for it's full syntax.

    NOTE: If the live server needs database access to handle a request
          your test will have to request database access.  Furthermore
          when the tests want to see data added by the live-server (or
          the other way around) transactional database access will be
          needed as data inside a transaction is not shared between
          the live server and test code.

          Static assets will be automatically served when
          ``django.contrib.staticfiles`` is available in INSTALLED_APPS.
    """
    skip_if_no_django()

    import django

    addr = (request.config.getvalue('liveserver') or
            os.getenv('DJANGO_LIVE_TEST_SERVER_ADDRESS'))

    if addr and django.VERSION >= (1, 11) and ':' in addr:
        request.config.warn('D001', 'Specifying a live server port is not supported '
                            'in Django 1.11. This will be an error in a future '
                            'pytest-django release.')

    if not addr:
        if django.VERSION < (1, 11):
            addr = 'localhost:8081,8100-8200'
        else:
            addr = 'localhost'

    server = live_server_helper.LiveServer(addr)
    request.addfinalizer(server.stop)
    return server


@pytest.fixture(autouse=True, scope='function')
def _live_server_helper(request):
    """Helper to make live_server work, internal to pytest-django.

    This helper will dynamically request the transactional_db fixture
    for a test which uses the live_server fixture.  This allows the
    server and test to access the database without having to mark
    this explicitly which is handy since it is usually required and
    matches the Django behaviour.

    The separate helper is required since live_server can not request
    transactional_db directly since it is session scoped instead of
    function-scoped.
    """
    if 'live_server' in request.funcargnames:
        getfixturevalue(request, 'transactional_db')
