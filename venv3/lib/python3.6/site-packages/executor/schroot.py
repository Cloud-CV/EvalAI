# Programmer friendly subprocess wrapper.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: June 10, 2017
# URL: https://executor.readthedocs.io

"""
Secure command execution in chroot environments.

The :mod:`executor.schroot` module defines the :class:`SecureChangeRootCommand`
class which makes it easy to run commands inside chroots_ that are managed
using the schroot_ program.

.. _chroots: http://en.wikipedia.org/wiki/Chroot
.. _schroot: https://wiki.debian.org/Schroot
"""

# Standard library modules.
import logging

# External dependencies.
from property_manager import mutable_property, required_property

# Modules included in our package.
from executor import DEFAULT_WORKING_DIRECTORY, ExternalCommand

# Initialize a logger.
logger = logging.getLogger(__name__)

SCHROOT_PROGRAM_NAME = 'schroot'
"""The name of the ``schroot`` program (a string)."""

DEFAULT_NAMESPACE = 'chroot'
"""
The default chroot namespace (a string).

Refer to the schroot_ documentation for more information about chroot
namespaces.
"""


class SecureChangeRootCommand(ExternalCommand):

    """:class:`SecureChangeRootCommand` objects use the schroot_ program to execute commands inside chroots."""

    def __init__(self, *args, **options):
        """
        Initialize a :class:`SecureChangeRootCommand` object.

        :param args: Positional arguments are passed on to the initializer of
                     the :class:`.ExternalCommand` class.
        :param options: Any keyword arguments are passed on to the initializer
                        of the :class:`.ExternalCommand` class.

        If the keyword argument `chroot_name` isn't given but positional
        arguments are provided, the first positional argument is used to set
        the :attr:`chroot_name` property.

        The command is not started until you call
        :func:`~executor.ExternalCommand.start()` or
        :func:`~executor.ExternalCommand.wait()`.
        """
        # Enable modification of the positional arguments.
        args = list(args)
        # We allow `chroot_name' to be passed as a keyword argument but use the
        # first positional argument when the keyword argument isn't given.
        if options.get('chroot_name') is None and args:
            options['chroot_name'] = args.pop(0)
        # Inject our logger as a default.
        options.setdefault('logger', logger)
        # Initialize the superclass.
        super(SecureChangeRootCommand, self).__init__(*args, **options)

    @mutable_property
    def chroot_directory(self):
        """
        The working directory _inside the chroot_ (a string or :data:`None`, defaults to ``/``).

        When :attr:`chroot_directory` is :data:`None` the schroot_ program gets
        to pick the working directory inside the chroot (refer to the schroot
        documentation for the complete details).

        For non-interactive usage (which I anticipate to be the default usage
        of :class:`SecureChangeRootCommand`) the schroot program simply assumes
        that the working directory outside of the chroot also exists inside the
        chroot, then fails with an error message when this is not the case.

        Because this isn't a very robust default, :attr:`chroot_directory`
        defaults to ``/`` instead.
        """
        return '/'

    @required_property
    def chroot_name(self):
        """
        The name of a chroot managed by schroot_ (a string).

        This is expected to match one of the names configured in the directory
        ``/etc/schroot/chroot.d``.
        """

    @mutable_property
    def chroot_user(self):
        """
        The name of the user inside the chroot to run the command as (a string or :data:`None`).

        This defaults to :data:`None` which means to run as the current user.
        """

    @property
    def command_line(self):
        """
        The complete `schroot` command including the command to run inside the chroot.

        This is a list of strings with the `schroot` command line to enter
        the requested chroot and execute :attr:`~.ExternalCommand.command`.
        """
        schroot_command = list(self.schroot_command)
        schroot_command.append('--chroot=%s' % self.chroot_name)
        if self.chroot_user:
            schroot_command.append('--user=%s' % self.chroot_user)
        if self.chroot_directory:
            schroot_command.append('--directory=%s' % self.chroot_directory)
        # We only add the `--' to the command line when it will be followed by
        # a command to execute inside the chroot. Emitting a trailing `--' that
        # isn't followed by anything doesn't appear to bother schroot, but it
        # does look a bit weird and may cause unnecessary confusion.
        super_cmdline = list(super(SecureChangeRootCommand, self).command_line)
        if super_cmdline:
            schroot_command.append('--')
            schroot_command.extend(super_cmdline)
        return schroot_command

    @property
    def directory(self):
        """
        Set the working directory inside the chroot.

        When you set this property you change :attr:`chroot_directory`, however
        reading back the property you'll just get :data:`.DEFAULT_WORKING_DIRECTORY`.
        This is because the superclass :class:`.ExternalCommand` uses
        :attr:`directory` as the working directory for the `schroot` command,
        and directories inside chroots aren't guaranteed to exist on the host
        system.
        """
        return DEFAULT_WORKING_DIRECTORY

    @directory.setter
    def directory(self, value):
        """Redirect assignment from `directory` to `chroot_directory`."""
        self.chroot_directory = value

    @mutable_property
    def schroot_command(self):
        """
        The command used to run the `schroot` program.

        This is a list of strings, by default the list contains just
        :data:`SCHROOT_PROGRAM_NAME`. The :attr:`chroot_directory`,
        :attr:`chroot_name` and :attr:`chroot_user` properties also
        influence the `schroot` command line used.
        """
        return [SCHROOT_PROGRAM_NAME]
