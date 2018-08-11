"""Functions to aid in creating, reusing and destroying Django test databases
"""
import os.path
import sys
import types


def test_database_exists_from_previous_run(connection):
    # Try to open a cursor to the test database
    test_db_name = connection.creation._get_test_db_name()

    # When using a real SQLite backend (via TEST_NAME), check if the file
    # exists, because it gets created automatically.
    if connection.settings_dict['ENGINE'] == 'django.db.backends.sqlite3':
        if not os.path.exists(test_db_name):
            return False

    orig_db_name = connection.settings_dict['NAME']
    connection.settings_dict['NAME'] = test_db_name

    # With SQLite memory databases the db never exists.
    if connection.settings_dict['NAME'] == ':memory:':
        return False

    try:
        connection.cursor()
        return True
    except Exception:  # TODO: Be more discerning but still DB agnostic.
        return False
    finally:
        connection.close()
        connection.settings_dict['NAME'] = orig_db_name


def _monkeypatch(obj, method_name, new_method):
    assert hasattr(obj, method_name), method_name

    if sys.version_info < (3, 0):
        wrapped_method = types.MethodType(new_method, obj, obj.__class__)
    else:
        wrapped_method = types.MethodType(new_method, obj)

    setattr(obj, method_name, wrapped_method)


def create_test_db_with_reuse(self, verbosity=1, autoclobber=False,
                              keepdb=False, serialize=False):
    """
    This method is a monkey patched version of create_test_db that
    will not actually create a new database, but just reuse the
    existing.

    This is only used with Django < 1.8.
    """
    test_database_name = self._get_test_db_name()
    self.connection.settings_dict['NAME'] = test_database_name

    if verbosity >= 1:
        test_db_repr = ''
        if verbosity >= 2:
            test_db_repr = " ('%s')" % test_database_name
        print("Re-using existing test database for alias '%s'%s..." % (
            self.connection.alias, test_db_repr))

    return test_database_name


def monkey_patch_creation_for_db_reuse():
    from django.db import connections

    for connection in connections.all():
        if test_database_exists_from_previous_run(connection):
            _monkeypatch(connection.creation, 'create_test_db',
                         create_test_db_with_reuse)
