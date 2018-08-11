# Command line interface for the executor package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: June 24, 2017
# URL: https://executor.readthedocs.io
#
# TODO Expose a clean way to interrupt the fudge factor of other processes.
# TODO Properly document command timeout / lock-timeout / TERM-timeout / KILL-timeout.
# TODO See if there's a way to move command timeout support out of the CLI?
# TODO Find ways to improve the coverage of this module! (multiprocessing?)

"""
Usage: executor [OPTIONS] COMMAND ...

Easy subprocess management on the command line based on the Python package with
the same name. The `executor' program runs external commands with support for
timeouts, dynamic startup delay (fudge factor) and exclusive locking.

You can think of `executor' as a combination of the `flock' and `timelimit'
programs with some additional niceties (namely the dynamic startup delay and
integrated system logging on UNIX platforms).

Supported options:

  -t, --timeout=LIMIT

    Set the time after which the given command will be aborted. By default
    LIMIT is counted in seconds. You can also use one of the suffixes `s'
    (seconds), `m' (minutes), `h' (hours) or `d' (days).

  -f, --fudge-factor=LIMIT

    This option controls the dynamic startup delay (fudge factor) which is
    useful when you want a periodic task to run once per given interval but the
    exact time is not important. Refer to the --timeout option for acceptable
    values of LIMIT, this number specifies the maximum amount of time to sleep
    before running the command (the minimum is zero, otherwise you could just
    include the command `sleep N && ...' in your command line :-).

  -e, --exclusive

    Use an interprocess lock file to guarantee that executor will never run
    the external command concurrently. Refer to the --lock-timeout option
    to customize blocking / non-blocking behavior. To customize the name
    of the lock file you can use the --lock-file option.

  -T, --lock-timeout=LIMIT

    By default executor tries to claim the lock and if it fails it will exit
    with a nonzero exit code. This option can be used to enable blocking
    behavior. Refer to the --timeout option for acceptable values of LIMIT.

  -l, --lock-file=NAME

    Customize the name of the lock file. By default this is the base name of
    the external command, so if you're running something generic like `bash'
    or `python' you might want to change this :-).

  -v, --verbose

    Increase logging verbosity (can be repeated).

  -q, --quiet

    Decrease logging verbosity (can be repeated).

  -h, --help

    Show this message and exit.
"""

# Standard library modules.
import getopt
import logging
import os
import random
import sys
import tempfile
import time

# External dependencies.
import coloredlogs
from fasteners.process_lock import InterProcessLock
from humanfriendly import Timer, format, format_timespan, parse_timespan
from humanfriendly.terminal import usage, warning
from six.moves.urllib.parse import quote as urlencode

# Modules included in our package.
from executor import ExternalCommandFailed, execute, quote, which

LOCKS_DIRECTORY = '/var/lock'
"""
The pathname of the preferred directory for lock files (a string).

Refer to :func:`get_lock_path()` for more details.
"""

INTERRUPT_FILE = 'executor-fudge-factor-interrupt'
"""The base name of the file used to interrupt the fudge factor (a string)."""

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def main():
    """Command line interface for the ``executor`` program."""
    # Enable logging to the terminal and system log.
    coloredlogs.install(syslog=True)
    # Command line option defaults.
    command_timeout = 0
    exclusive = False
    fudge_factor = 0
    lock_name = None
    lock_timeout = 0
    # Parse the command line options.
    try:
        options, arguments = getopt.getopt(sys.argv[1:], 'eT:l:t:f:vqh', [
            'exclusive', 'lock-timeout=', 'lock-file=', 'timeout=',
            'fudge-factor=', 'verbose', 'quiet', 'help',
        ])
        for option, value in options:
            if option in ('-e', '--exclusive'):
                exclusive = True
            elif option in ('-T', '--lock-timeout'):
                lock_timeout = parse_timespan(value)
            elif option in ('-l', '--lock-file'):
                lock_name = value
            elif option in ('-t', '--timeout'):
                command_timeout = parse_timespan(value)
            elif option in ('-f', '--fudge-factor'):
                fudge_factor = parse_timespan(value)
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-q', '--quiet'):
                coloredlogs.decrease_verbosity()
            elif option in ('-h', '--help'):
                usage(__doc__)
                sys.exit(0)
            else:
                assert False, "Unhandled option!"
        # Make sure the operator provided a program to execute.
        if not arguments:
            usage(__doc__)
            sys.exit(0)
        # Make sure the program actually exists.
        program_name = arguments[0]
        if not os.path.isfile(program_name):
            # Only search the $PATH if the given program name
            # doesn't already include one or more path segments.
            if program_name == os.path.basename(program_name):
                matching_programs = which(program_name)
                if matching_programs:
                    program_name = matching_programs[0]
        # The subprocess.Popen() call later on doesn't search the $PATH so we
        # make sure to give it the absolute pathname to the program.
        arguments[0] = program_name
    except Exception as e:
        warning("Failed to parse command line arguments: %s", e)
        sys.exit(1)
    # Apply the requested fudge factor.
    apply_fudge_factor(fudge_factor)
    # Run the requested command.
    try:
        if exclusive:
            # Select a default lock file name?
            if not lock_name:
                lock_name = os.path.basename(arguments[0])
                logger.debug("Using base name of command as lock file name (%s).", lock_name)
            lock_file = get_lock_path(lock_name)
            lock = InterProcessLock(path=lock_file, logger=logger)
            logger.debug("Trying to acquire exclusive lock: %s", lock_file)
            if lock.acquire(blocking=(lock_timeout > 0), max_delay=lock_timeout):
                logger.info("Successfully acquired exclusive lock: %s", lock_file)
                run_command(arguments, timeout=command_timeout)
            else:
                logger.error("Failed to acquire exclusive lock: %s", lock_file)
                sys.exit(1)
        else:
            run_command(arguments, timeout=command_timeout)
    except ExternalCommandFailed as e:
        logger.error("%s", e.error_message)
        sys.exit(e.command.returncode)


def apply_fudge_factor(fudge_factor):
    """
    Apply the requested scheduling fudge factor.

    :param fudge_factor: The maximum number of seconds to sleep (a number).

    Previous implementations of the fudge factor interrupt used UNIX signals
    (specifically ``SIGUSR1``) but the use of this signal turned out to be
    sensitive to awkward race conditions and it wasn't very cross platform, so
    now the creation of a regular file is used to interrupt the fudge factor.
    """
    if fudge_factor:
        timer = Timer()
        logger.debug("Calculating fudge factor based on user defined maximum (%s) ..",
                     format_timespan(fudge_factor))
        fudged_sleep_time = fudge_factor * random.random()
        logger.info("Sleeping for %s because of user defined fudge factor ..",
                    format_timespan(fudged_sleep_time))
        interrupt_file = get_lock_path(INTERRUPT_FILE)
        while timer.elapsed_time < fudged_sleep_time:
            if os.path.isfile(interrupt_file):
                logger.info("Fudge factor sleep was interrupted! (%s exists)",
                            interrupt_file)
                break
            time_to_sleep = min(1, fudged_sleep_time - timer.elapsed_time)
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)
        else:
            logger.info("Finished sleeping because of fudge factor (took %s).", timer)


def get_lock_path(lock_name):
    """
    Get a pathname that can be used for an interprocess lock.

    :param lock_name: The base name for the lock file (a string).
    :returns: An absolute pathname (a string).
    """
    lock_file = '%s.lock' % urlencode(lock_name, safe='')
    if os.path.isdir(LOCKS_DIRECTORY) and os.access(LOCKS_DIRECTORY, os.W_OK):
        return os.path.join(LOCKS_DIRECTORY, lock_file)
    else:
        return os.path.join(tempfile.gettempdir(), lock_file)


def run_command(arguments, timeout=None):
    """
    Run the specified command (with an optional timeout).

    :param arguments: The command line for the external command (a list of
                      strings).
    :param timeout: The optional command timeout (a number or :data:`None`).
    :raises: :exc:`CommandTimedOut` if the command times out.
    """
    timer = Timer()
    logger.info("Running command: %s", quote(arguments))
    with execute(*arguments, async=True) as command:
        # Wait for the command to finish or exceed the given timeout.
        while command.is_running:
            if timeout and timer.elapsed_time > timeout:
                raise CommandTimedOut(command, timeout)
            # Sleep between 0.1 and 1 second, waiting for
            # the external command to finish its execution.
            time_to_sleep = min(1, max(0.1, timeout - timer.elapsed_time))
            if time_to_sleep > 0:
                time.sleep(time_to_sleep)
        if command.succeeded:
            logger.info("Command completed successfully in %s.", timer)


class CommandTimedOut(ExternalCommandFailed):

    """Raised when a command exceeds the given timeout."""

    def __init__(self, command, timeout):
        """
        Initialize a :class:`CommandTimedOut` object.

        :param command: The command that timed out (an
                        :class:`~executor.ExternalCommand` object).
        :param timeout: The timeout that was exceeded (a number).
        """
        super(CommandTimedOut, self).__init__(
            command=command,
            error_message=format(
                "External command exceeded timeout of %s: %s",
                format_timespan(timeout),
                quote(command.command_line),
            ),
        )
