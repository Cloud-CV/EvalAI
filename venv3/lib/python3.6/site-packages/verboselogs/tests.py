# Verbose, notice, and spam log levels for Python's logging module.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: August 7, 2017
# URL: https://verboselogs.readthedocs.io

"""Test suite for the `verboselogs` package."""

# Standard library modules.
import logging
import random
import string
import sys
import unittest

# Test dependencies.
import mock

# The module we're testing.
import verboselogs


class VerboseLogsTestCase(unittest.TestCase):

    """Container for the `verboselogs` tests."""

    def test_install(self):
        """Test the :func:`verboselogs.install()` function."""
        default_logger = logging.getLogger(random_string())
        assert isinstance(default_logger, logging.Logger)
        verboselogs.install()
        custom_logger = logging.getLogger(random_string())
        assert isinstance(custom_logger, verboselogs.VerboseLogger)

    def test_notice_method(self):
        """Test the :func:`~verboselogs.VerboseLogger.notice()` method."""
        self.check_custom_level('notice')

    def test_spam_method(self):
        """Test the :func:`~verboselogs.VerboseLogger.spam()` method."""
        self.check_custom_level('spam')

    def test_success_method(self):
        """Test the :func:`~verboselogs.VerboseLogger.success()` method."""
        self.check_custom_level('success')

    def test_verbose_method(self):
        """Test the :func:`~verboselogs.VerboseLogger.verbose()` method."""
        self.check_custom_level('verbose')

    def check_custom_level(self, name):
        """Check a custom log method."""
        logger = verboselogs.VerboseLogger(random_string())
        # Gotcha: If we use NOTSET (0) here the level will be inherited from
        # the parent logger and our custom log level may be filtered out.
        logger.setLevel(1)
        logger._log = mock.MagicMock()
        level = getattr(verboselogs, name.upper())
        method = getattr(logger, name.lower())
        message = "Any random message"
        method(message)
        logger._log.assert_called_with(level, message, ())

    def test_pylint_plugin(self):
        """Test the :mod:`verboselogs.pylint` module."""
        saved_args = sys.argv
        try:
            sys.argv = ['pylint', '--load-plugins', 'verboselogs.pylint', '--errors-only', 'verboselogs']
            __import__('pylint').run_pylint()
        except SystemExit:
            pass
        finally:
            sys.argv = saved_args


def random_string(length=25):
    """Generate a random string."""
    return ''.join(random.choice(string.ascii_letters) for i in range(length))
