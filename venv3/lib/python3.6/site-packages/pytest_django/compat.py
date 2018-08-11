# This file cannot be imported from until Django sets up

try:
    # Django 1.11
    from django.test.utils import setup_databases, teardown_databases  # noqa
except ImportError:
    # In Django prior to 1.11, teardown_databases is only available as a method on DiscoverRunner
    from django.test.runner import setup_databases, DiscoverRunner as _DiscoverRunner  # noqa

    def teardown_databases(db_cfg, verbosity):
        (_DiscoverRunner(verbosity=verbosity,
                         interactive=False)
         .teardown_databases(db_cfg))

try:
    from django.db.backends.base.base import BaseDatabaseWrapper  # noqa
except ImportError:
    # Django 1.7.
    from django.db.backends import BaseDatabaseWrapper  # noqa
