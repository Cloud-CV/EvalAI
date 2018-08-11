# Programmer friendly subprocess wrapper.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 20, 2018
# URL: https://executor.readthedocs.io

"""
Simple command execution in chroot environments.

The :mod:`executor.chroot` module defines the :class:`ChangeRootCommand` class
which makes it easy to run commands inside chroots_. If this doesn't mean
anything to you, here's a primer:

- The word 'chroot' is an abbreviation of the phrase 'change root' which is
  Unix functionality that changes the 'root' directory (``/``) of a running
  process, so 'change root' describes an action.

- Even though the phrase 'change root' describes an action the word 'chroot'
  is also used to refer to the directory which serves as the new root directory
  (English is flexible like that :-). This is why it makes sense to say that
  "you're entering the chroot".

.. warning:: This is low level functionality. This module performs absolutely
             no chroot initialization, for example ``/etc/resolv.conf`` may be
             incorrect and there won't be any bind mounts available in the
             chroot (unless you've prepared them yourself).

If you need your chroot to be initialized for you then consider using the
:mod:`executor.schroot` module instead. It takes a bit of time to set up
schroot_ but it provides a more high level experience than chroot_.

.. _chroots: http://en.wikipedia.org/wiki/Chroot
.. _chroot: https://manpages.debian.org/8/chroot
.. _schroot: https://wiki.debian.org/Schroot
"""

# Standard library modules.
import logging

# External dependencies.
from property_manager import mutable_property, required_property

# Modules included in our package.
from executor import DEFAULT_SHELL, DEFAULT_WORKING_DIRECTORY, ExternalCommand, quote

# Initialize a logger.
logger = logging.getLogger(__name__)

CHROOT_PROGRAM_NAME = 'chroot'
"""The name of the chroot_ program (a string)."""


class ChangeRootCommand(ExternalCommand):

    """:class:`ChangeRootCommand` objects use the chroot_ program to execute commands inside chroots."""

    def __init__(self, *args, **options):
        """
        Initialize a :class:`ChangeRootCommand` object.

        :param args: Positional arguments are passed on to the initializer of
                     the :class:`.ExternalCommand` class.
        :param options: Any keyword arguments are passed on to the initializer
                        of the :class:`.ExternalCommand` class.

        If the keyword argument `chroot` isn't given but positional arguments
        are provided, the first positional argument is used to set the
        :attr:`chroot` property.

        The command is not started until you call
        :func:`~executor.ExternalCommand.start()` or
        :func:`~executor.ExternalCommand.wait()`.
        """
        # Enable modification of the positional arguments.
        args = list(args)
        # We allow `chroot_directory' to be passed as a keyword argument but
        # use the first positional argument when the keyword argument isn't
        # given.
        if options.get('chroot') is None and args:
            options['chroot'] = args.pop(0)
        # Inject our logger as a default.
        options.setdefault('logger', logger)
        # Initialize the superclass.
        super(ChangeRootCommand, self).__init__(*args, **options)

    @required_property
    def chroot(self):
        """The pathname of the root directory of the chroot (a string)."""

    @mutable_property
    def chroot_command(self):
        """
        The command used to run the ``chroot`` program.

        This is a list of strings, by default the list contains just
        :data:`CHROOT_PROGRAM_NAME`. The :attr:`chroot`, :attr:`chroot_group`
        and :attr:`chroot_user` properties also influence the `chroot` command
        line used.
        """
        return [CHROOT_PROGRAM_NAME]

    @mutable_property
    def chroot_directory(self):
        """The working directory _inside the chroot_ (a string, defaults to :data:`None`)."""

    @mutable_property
    def chroot_group(self):
        """The name or ID of the system group that runs the command (a string or number, defaults to 'root')."""
        return 'root'

    @mutable_property
    def chroot_user(self):
        """The name or ID of the system user that runs the command (a string or number, defaults to 'root')."""
        return 'root'

    @property
    def command_line(self):
        """
        The complete `chroot` command including the command to run inside the chroot.

        This is a list of strings with the `chroot` command line to enter
        the requested chroot and execute :attr:`~.ExternalCommand.command`.
        """
        chroot_command = list(self.chroot_command)
        # Check if we have superuser privileges on _the host system_ (via super()).
        if not super(ChangeRootCommand, self).have_superuser_privileges:
            # The chroot() system call requires superuser privileges on the host system.
            chroot_command.insert(0, 'sudo')
        chroot_command.append('--userspec=%s:%s' % (self.chroot_user, self.chroot_group))
        chroot_command.append(self.chroot)
        # Get the command to be executed inside the chroot.
        command_inside_chroot = list(super(ChangeRootCommand, self).command_line)
        # Check if we need to change the working directory inside the chroot.
        if self.chroot_directory and not command_inside_chroot:
            # We need to change the working directory but we don't have a
            # command to execute. In this case we assume that an interactive
            # shell was intended (inspired by how chroot, schroot and ssh work
            # when used interactively).
            command_inside_chroot = [DEFAULT_SHELL, '-i']
        if command_inside_chroot:
            # Check if we need to change the working directory inside the chroot.
            if self.chroot_directory:
                # The chroot program doesn't have an option to set the working
                # directory so as a workaround we use a shell to do this.
                cd_command = 'cd %s' % quote(self.chroot_directory)
                chroot_command.extend(self.prefix_shell_command(cd_command, command_inside_chroot))
            else:
                # If we don't need to change the working directory then
                # we don't need to quote the user's command any further.
                chroot_command.extend(command_inside_chroot)
        return chroot_command

    @property
    def directory(self):
        """
        Set the working directory inside the chroot.

        When you set this property you change :attr:`chroot_directory`, however
        reading back the property you'll just get :data:`.DEFAULT_WORKING_DIRECTORY`.
        This is because the superclass :class:`.ExternalCommand` uses
        :attr:`directory` as the working directory for the `chroot` command,
        and directories inside chroots aren't guaranteed to exist on the host
        system.
        """
        return DEFAULT_WORKING_DIRECTORY

    @directory.setter
    def directory(self, value):
        """Redirect assignment from `directory` to `chroot_directory`."""
        self.chroot_directory = value

    @property
    def have_superuser_privileges(self):
        """
        Whether the command inside the chroot will be running under `superuser privileges`_.

        This is :data:`True` when :attr:`chroot_user` is the number 0 or the
        string 'root', :data:`False` otherwise.

        This overrides :attr:`.ExternalCommand.have_superuser_privileges` to
        ensure that ``sudo`` isn't used inside the chroot unless it's really
        necessary. This is important because not all chroot environments have
        ``sudo`` installed and failing due to a lack of ``sudo`` when we're
        already running as ``root`` is just stupid :-).
        """
        return self.chroot_user in (0, '0', 'root')
