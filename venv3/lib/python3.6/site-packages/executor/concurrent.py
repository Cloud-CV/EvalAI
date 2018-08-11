# Programmer friendly subprocess wrapper.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 20, 2018
# URL: https://executor.readthedocs.io

"""
Support for concurrent external command execution.

The :mod:`executor.concurrent` module defines the :class:`CommandPool` class
which makes it easy to prepare a large number of external commands, group them
together in a pool, start executing a configurable number of external commands
simultaneously and wait for all external commands to finish. For fine grained
concurrency control please refer to the :attr:`~.ExternalCommand.dependencies`
and :attr:`~.ExternalCommand.group_by` properties of the
:class:`.ExternalCommand` class.
"""

# Standard library modules.
import logging
import multiprocessing
import os

# External dependencies.
from executor import ExternalCommandFailed
from executor import logger as parent_logger
from humanfriendly import format, pluralize, Spinner, Timer
from property_manager import PropertyManager, mutable_property

# Initialize a logger.
logger = logging.getLogger(__name__)


class CommandPool(PropertyManager):

    """
    Execute multiple external commands concurrently.

    After constructing a :class:`CommandPool` instance you add commands to it
    using :func:`add()` and when you're ready to run the commands you call
    :func:`run()`.
    """

    def __init__(self, concurrency=None, **options):
        """
        Initialize a :class:`CommandPool` object.

        :param concurrency: Override the value of :attr:`concurrency`.
        :param logs_directory: Override the value of :attr:`logs_directory`.
        """
        # Initialize instance variables.
        self.collected = set()
        self.commands = []
        # Transform `concurrency' from a positional into a keyword argument.
        if concurrency:
            options['concurrency'] = concurrency
        # Set writable properties based on keyword arguments.
        super(CommandPool, self).__init__(**options)

    @mutable_property
    def concurrency(self):
        """
        The number of external commands that the pool is allowed to run simultaneously.

        This is a positive integer number. It defaults to the return value of
        :func:`multiprocessing.cpu_count()` (which may not make much sense if
        your commands are I/O bound instead of CPU bound).

        Setting :attr:`concurrency` to one is a supported use case intended to
        make it easier for users of the :mod:`executor.concurrent` module to
        reuse the code they've built on top of command pools (if only for
        debugging, but there are lots of use cases :-).
        """
        return multiprocessing.cpu_count()

    @mutable_property
    def delay_checks(self):
        """
        Whether to postpone raising an exception until all commands have run (a boolean).

        If this option is :data:`True` (not the default) and a command with
        :attr:`.check` set to :data:`True` fails the command pool's execution
        is not aborted, instead all commands will be allowed to run. After all
        commands have finished a :exc:`CommandPoolFailed` exception will be
        raised that tells you which command(s) failed.
        """
        return False

    @mutable_property
    def logger(self):
        """
        The :class:`logging.Logger` object to use.

        If you are using Python's :mod:`logging` module and you find it
        confusing that command pool execution is logged under the
        :mod:`executor.concurrent` name space instead of the name space of the
        application or library using :mod:`executor` you can set this attribute
        to inject a custom (and more appropriate) logger.
        """
        return logger

    @mutable_property
    def logs_directory(self):
        """
        The pathname of a directory where captured output is stored (a string).

        If this property is set to the pathname of a directory (before any
        external commands have been started) the merged output of each external
        command is captured and stored in a log file in this directory. The
        directory will be created if it doesn't exist yet.

        Output will start appearing in the log files before the external
        commands are finished, this enables `tail -f`_ to inspect the progress
        of commands that are still running and emitting output.

        .. _tail -f: https://en.wikipedia.org/wiki/Tail_(Unix)#File_monitoring
        """

    @property
    def is_finished(self):
        """:data:`True` if all commands in the pool have finished (including retries), :data:`False` otherwise."""
        return self.num_finished == self.num_commands

    @property
    def num_commands(self):
        """The number of commands in the pool (an integer)."""
        return len(self.commands)

    @property
    def num_finished(self):
        """The number of commands in the pool that have already finished, including retries (an integer)."""
        return sum(cmd.is_finished_with_retries for id, cmd in self.commands)

    @property
    def num_failed(self):
        """The number of commands in the pool that failed (an integer)."""
        return sum(cmd.failed for id, cmd in self.commands)

    @property
    def num_running(self):
        """The number of currently running commands in the pool (an integer)."""
        return sum(cmd.is_running for id, cmd in self.commands)

    @property
    def running_groups(self):
        """
        A set of running command groups.

        The value of :attr:`running_groups` is a :class:`set` with the
        :attr:`~.ExternalCommand.group_by` values of all currently running
        commands (:data:`None` is never included in the set).
        """
        return set(
            cmd.group_by for id, cmd in self.commands
            if cmd.is_running and cmd.group_by is not None
        )

    @property
    def results(self):
        """
        A mapping of identifiers to external command objects.

        This is a dictionary with external command identifiers as keys (refer
        to :func:`add()`) and :class:`.ExternalCommand` objects as values. The
        :class:`.ExternalCommand` objects provide access to the return codes
        and/or output of the finished commands.
        """
        return dict(self.commands)

    @mutable_property
    def spinner(self):
        """
        Whether to show an animated spinner or not (a boolean or :data:`None`).

        The value of :attr:`spinner` defaults to :data:`None` which means a
        spinner is shown when we're connected to a terminal but hidden when
        we're not connected to a terminal.
        """
        return None

    @property
    def unexpected_failures(self):
        """
        A list of :class:`~executor.ExternalCommand` objects that *failed unexpectedly*.

        The resulting list includes only commands where :attr:`.check` and
        :attr:`.failed` are both :data:`True`.
        """
        return [cmd for id, cmd in self.commands if cmd.check and cmd.failed]

    def add(self, command, identifier=None, log_file=None):
        """
        Add an external command to the pool of commands.

        :param command: The external command to add to the pool (an
                        :class:`.ExternalCommand` object).
        :param identifier: A unique identifier for the external command (any
                           value). When this parameter is not provided the
                           identifier is set to the number of commands in the
                           pool plus one (i.e. the first command gets id 1).
        :param log_file: Override the default log file name for the command
                         (the identifier with ``.log`` appended) in case
                         :attr:`logs_directory` is set.

        When a command is added to a command pool the following options are
        changed automatically:

        - The :attr:`~executor.ExternalCommand.async` property is set to
          :data:`True`. If you want the commands to execute with a concurrency
          of one then you should set :attr:`concurrency` to one.

        - The :attr:`~executor.ExternalCommand.tty` property is set to
          :data:`False` when :attr:`concurrency` is higher than one because
          interaction with multiple concurrent subprocesses in a single
          terminal is prone to serious miscommunication (when multiple
          subprocesses present an interactive prompt at the same time and the
          user tries to answer one of the prompts it will be impossible to tell
          which of the subprocesses will receive the user's reply).
        """
        # Configure the command to run asynchronously.
        command.async = True
        # Configure the command to run without a controlling terminal?
        if self.concurrency > 1:
            command.tty = False
        # Override the command's default logger?
        if command.logger == parent_logger:
            command.logger = self.logger
        # Pick a default identifier for the command?
        if identifier is None:
            identifier = len(self.commands) + 1
        # Configure logging of command output?
        if self.logs_directory:
            if log_file is None:
                log_file = '%s.log' % identifier
            pathname = os.path.join(self.logs_directory, log_file)
            directory = os.path.dirname(pathname)
            if not os.path.isdir(directory):
                os.makedirs(directory)
            handle = open(pathname, 'ab')
            command.stdout_file = handle
            command.stderr_file = handle
        # Add the command to the pool.
        self.commands.append((identifier, command))

    def run(self):
        """
        Keep spawning commands and collecting results until all commands have run.

        :returns: The value of :attr:`results`.
        :raises: Any exceptions raised by :func:`collect()`.

        This method calls :func:`spawn()` and :func:`collect()` in a loop until
        all commands registered using :func:`add()` have run and finished. If
        :func:`collect()` raises an exception any running commands are
        terminated before the exception is propagated to the caller.

        If you're writing code where you want to own the main loop then
        consider calling :func:`spawn()` and :func:`collect()` directly instead
        of using :func:`run()`.

        When :attr:`concurrency` is set to one, specific care is taken to make
        sure that the callbacks configured by :attr:`.start_event` and
        :attr:`.finish_event` are called in the expected (intuitive) order.
        """
        # Start spawning processes to execute the commands.
        timer = Timer()
        logger.debug("Preparing to run %s with a concurrency of %i ..",
                     pluralize(self.num_commands, "command"),
                     self.concurrency)
        try:
            with Spinner(interactive=self.spinner, timer=timer) as spinner:
                num_started = 0
                num_collected = 0
                while not self.is_finished:
                    # When concurrency is set to one (I know, initially it
                    # sounds like a silly use case, bear with me) I want the
                    # start_event and finish_event callbacks of external
                    # commands to fire in the right order. The following
                    # conditional is intended to accomplish this goal.
                    if self.concurrency > (num_started - num_collected):
                        num_started += self.spawn()
                    num_collected += self.collect()
                    spinner.step(label=format(
                        "Waiting for %i/%i %s",
                        self.num_commands - self.num_finished, self.num_commands,
                        "command" if self.num_commands == 1 else "commands",
                    ))
                    spinner.sleep()
        except Exception:
            if self.num_running > 0:
                logger.warning("Command pool raised exception, terminating running commands!")
            # Terminate commands that are still running.
            self.terminate()
            # Re-raise the exception to the caller.
            raise
        # Collect the output and return code of any commands not yet collected.
        self.collect()
        logger.debug("Finished running %s in %s.",
                     pluralize(self.num_commands, "command"),
                     timer)
        # Report the results to the caller.
        return self.results

    def spawn(self):
        """
        Spawn additional external commands up to the :attr:`concurrency` level.

        :returns: The number of external commands that were spawned by this
                  invocation of :func:`spawn()` (an integer).

        The commands to start are picked according to three criteria:

        1. The command's :attr:`~.ExternalCommand.was_started` property is
           :data:`False`.
        2. The command's :attr:`~.ExternalCommand.group_by` value is not
           present in :attr:`running_groups`.
        3. The :attr:`~.ExternalCommand.is_finished_with_retries`
           properties of all of the command's :attr:`~.ExternalCommand.dependencies`
           are :data:`True`.
        """
        num_started = 0
        limit = self.concurrency - self.num_running
        if limit > 0:
            running_groups = self.running_groups
            for id, cmd in self.commands:
                # Skip commands that have already been started and cannot be retried.
                if (not cmd.was_started) or (cmd.retry_allowed and not cmd.is_running):
                    # If command groups are being used we'll only
                    # allow one running command per command group.
                    if cmd.group_by not in running_groups:
                        # If a command has any dependencies we won't allow it
                        # to start until all of its dependencies have finished.
                        if all(d.is_finished_with_retries for d in cmd.dependencies):
                            cmd.start()
                            num_started += 1
                            if cmd.group_by is not None:
                                running_groups.add(cmd.group_by)
                            if num_started == limit:
                                break
        if num_started > 0:
            logger.debug("Spawned %s ..", pluralize(num_started, "external command"))
        return num_started

    def collect(self):
        """
        Collect the exit codes and output of finished commands.

        :returns: The number of external commands that were collected by this
                  invocation of :func:`collect()` (an integer).
        :raises: If :attr:`delay_checks` is :data:`True`:
                  After all external commands have started and finished, if any
                  commands that have :attr:`~.ExternalCommand.check` set to
                  :data:`True` failed :exc:`CommandPoolFailed` is raised.
                 If :attr:`delay_checks` is :data:`False`:
                  The exceptions :exc:`.ExternalCommandFailed`,
                  :exc:`.RemoteCommandFailed` and :exc:`.RemoteConnectFailed`
                  can be raised if a command in the pool that has
                  :attr:`~.ExternalCommand.check` set to :data:`True` fails.
                  The :attr:`~.ExternalCommandFailed.pool` attribute of the
                  exception will be set to the pool.

        .. warning:: If an exception is raised, commands that are still running
                     will not be terminated! If this concerns you then consider
                     calling :func:`terminate()` from a :keyword:`finally`
                     block (this is what :func:`run()` does).
        """
        num_collected = 0
        for identifier, command in self.commands:
            if identifier not in self.collected and command.is_finished:
                try:
                    command.wait(check=False if self.delay_checks else None)
                except ExternalCommandFailed as e:
                    if not command.retry_allowed:
                        # Propagate exceptions that can't be retried.
                        e.pool = self
                        raise
                finally:
                    # Update our bookkeeping even if wait() raised an exception.
                    if not command.retry_allowed:
                        self.collected.add(identifier)
                # We count retries as collected commands in order to
                # preserve the symmetry between the return values of
                # spawn() and collect() because run() depends on it.
                num_collected += 1
        if num_collected > 0:
            logger.debug("Collected %s ..", pluralize(num_collected, "external command"))
        # Check if delayed error checking was requested and is applicable.
        if self.delay_checks and self.is_finished and self.unexpected_failures:
            raise CommandPoolFailed(pool=self)
        return num_collected

    def terminate(self):
        """
        Terminate any commands that are currently running.

        :returns: The number of commands that were terminated (an integer).

        If :func:`terminate()` successfully terminates commands, you then call
        :func:`collect()` and the :attr:`.check` property of a terminated
        command is :data:`True` you will get an exception because terminated
        commands (by definition) report a nonzero
        :attr:`~executor.ExternalCommand.returncode`.
        """
        num_terminated = 0
        for identifier, command in self.commands:
            if command.terminate():
                num_terminated += 1
        if num_terminated > 0:
            logger.warning("Terminated %s ..", pluralize(num_terminated, "external command"))
        return num_terminated


class CommandPoolFailed(Exception):

    """
    Raised by :func:`~CommandPool.collect()` when not all commands succeeded.

    This exception is only raised when :attr:`~CommandPool.delay_checks` is
    :data:`True`.
    """

    def __init__(self, pool):
        """
        Initialize a :class:`CommandPoolFailed` object.

        :param pool: The :class:`CommandPool` object that triggered the
                     exception.
        """
        self.pool = pool
        super(CommandPoolFailed, self).__init__(self.error_message)

    @property
    def commands(self):
        """A shortcut for :attr:`.unexpected_failures`."""
        return self.pool.unexpected_failures

    @property
    def error_message(self):
        """An error message that explains which commands *failed unexpectedly* (a string)."""
        summary = format("%i out of %s failed unexpectedly:",
                         self.pool.num_failed,
                         pluralize(self.pool.num_commands, "command"))
        details = "\n".join(" - %s" % cmd.error_message for cmd in self.commands)
        return summary + "\n\n" + details
