# proc: Simple interface to Linux process information.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 12, 2016
# URL: https://proc.readthedocs.io

"""
The :mod:`proc.cron` module implements graceful termination of cron_.

.. contents::
   :local:

Introduction to cron
====================

The cron_ daemon is ubiquitous on Linux (UNIX) systems. It's responsible for
executing user defined "jobs" at fixed times, dates or intervals. It's used for
system maintenance tasks, periodic monitoring, production job servers for IT
companies around the world, etc.

Problem statement
=================

One thing that has always bothered me about cron_ is that there is no simple
and robust way to stop cron and wait for all running cron jobs to finish what
they were doing. You might be wondering why that would be useful...

Imagine you have to perform disruptive system maintenance on a job server
that's responsible for running dozens or even hundreds of important cron jobs.
Of course you can just run ``sudo service cron stop`` to stop cron from
starting new cron jobs, but what do you do about cron jobs that have already
started and are still running? Some options:

1. You just don't care and start your disruptive maintenance. In this case you
   can stop reading because what I'm proposing won't interest you! :-)

2. You stare at an interactive process monitor like top_, htop_, etc. until
   everything that looks like a cron job has disappeared from the screen. Good
   for you for being diligent about your work, but this is not a nice task to
   perform! Imagine you have to do it on a handful of job servers before
   starting disruptive maintenance on shared infrastructure like a central
   database server...

3. You automate your work with shell scripts or one-liners_ that involve
   grepping_ the output of ps_ or similar gymnastics that work most of the time
   but not quite always... (hi me from a few years ago! :-)

Of course there are dozens (hundreds?) of alternative job schedulers that could
make things easier but the thing is that cron_ is already here and widely used,
so migrating a handful of job servers with hundreds of jobs could be way more
work than it's ever going to be worth...

A robust solution: ``cron-graceful``
====================================

The :mod:`proc.cron` module implements the command line program
``cron-graceful`` which gracefully stops cron daemons. This module builds on
top of the :mod:`proc.tree` module as a demonstration of the possibilities
of the `proc` package and as a practical tool that is ready to be used on any
Linux system that has Python and cron_ installed.

The following command prints a usage message:

.. code-block:: sh

   $ cron-graceful --help

To use the program you simply run it with super user privileges:

.. code-block:: sh

   $ sudo cron-graceful

Internal documentation of :mod:`proc.cron`
=============================================

.. _cron: http://en.wikipedia.org/wiki/Cron
.. _grepping: http://en.wikipedia.org/wiki/Grep#Usage_as_a_verb
.. _htop: http://en.wikipedia.org/wiki/Htop
.. _one-liners: http://en.wikipedia.org/wiki/One-liner_program
.. _ps: http://en.wikipedia.org/wiki/Ps_(Unix)
.. _top: http://en.wikipedia.org/wiki/Top_(software)
"""

# Standard library modules.
import functools
import getopt
import logging
import logging.handlers
import os
import sys

# External dependencies.
import coloredlogs
from executor import ExternalCommandFailed, execute, quote, which
from humanfriendly import concatenate, format_timespan, pluralize, Spinner, Timer
from humanfriendly.terminal import usage, warning

# Modules provided by our package.
from proc.core import sorted_by_pid
from proc.tree import get_process_tree

# Initialize a logger.
logger = logging.getLogger(__name__)

# Inject our logger into all execute() calls.
execute = functools.partial(execute, logger=logger)

ADDITIONS_SCRIPT_NAME = 'cron-graceful-additions'
"""
The name of the external command that's run by ``cron-graceful`` (a string).

Refer to :func:`run_additions()` for details about how
:data:`ADDITIONS_SCRIPT_NAME` is used.
"""

USAGE_TEXT = """
Usage: cron-graceful [OPTIONS]

Gracefully stop the cron job scheduler by waiting for all running cron
jobs to finish. The cron-graceful program works as follows:

1. Identify the cron daemon process and send it a SIGSTOP signal to
   prevent it from scheduling new cron jobs without killing it.

2. Identify the currently running cron jobs by navigating the process
   tree (if the cron daemon process had been killed in step one this
   wouldn't be possible) and wait for the cron jobs to finish.

4. Terminate the cron daemon process (because we've already identified
   the running cron jobs and no new cron jobs can be scheduled we no
   longer need the daemon).

If a command named `cron-graceful-additions' exists in the $PATH it
will be executed between steps one and two. This allows you to inject
custom logic into the graceful shutdown process. If the command fails a
warning will be logged but the cron-graceful program will continue.

Supported options:

  -n, --dry-run

    Don't make any changes (doesn't require root access).

  -v, --verbose

    Make more noise (increase verbosity).

  -q, --quiet

    Make less noise (decrease verbosity).

  -h, --help

    Show this message and exit.
"""


def main():
    """Wrapper for :func:`cron_graceful()` that feeds it :data:`sys.argv`."""
    coloredlogs.install(syslog=True)
    cron_graceful(sys.argv[1:])


def cron_graceful(arguments):
    """Command line interface for the ``cron-graceful`` program."""
    runtime_timer = Timer()
    # Initialize logging to the terminal.
    dry_run = parse_arguments(arguments)
    if not dry_run:
        ensure_root_privileges()
    try:
        cron_daemon = find_cron_daemon()
    except CronDaemonNotRunning:
        logger.info("No running cron daemon found, assuming it was previously stopped ..")
    else:
        if not dry_run:
            # Prevent the cron daemon from starting new cron jobs.
            cron_daemon.suspend()
            # Enable user defined additional logic.
            run_additions()
        # Identify the running cron jobs based on the process tree _after_ the
        # cron daemon has been paused (assuming we're not performing a dry run)
        # so we know for sure that we see all running cron jobs (also we're not
        # interested in any processes that have already been stopped by
        # cron-graceful-additions).
        cron_daemon = find_cron_daemon()
        cron_jobs = sorted_by_pid(cron_daemon.grandchildren)
        if cron_jobs:
            logger.info("Found %s: %s",
                        pluralize(len(cron_jobs), "running cron job"),
                        concatenate(str(j.pid) for j in cron_jobs))
            # Wait for the running cron jobs to finish.
            wait_for_processes(cron_jobs)
        else:
            logger.info("No running cron jobs found.")
        # Terminate the cron daemon.
        if dry_run:
            logger.info("Stopping cron daemon with process id %i ..", cron_daemon.pid)
        else:
            terminate_cron_daemon(cron_daemon)
        logger.info("Done! Took %s to gracefully terminate cron.", runtime_timer.rounded)


def parse_arguments(arguments):
    """
    Parse the command line arguments.

    :param arguments: A list of strings with command line arguments.
    :returns: ``True`` if a dry run was requested, ``False`` otherwise.
    """
    dry_run = False
    try:
        options, arguments = getopt.gnu_getopt(arguments, 'nvqh', [
            'dry-run', 'verbose', 'quiet', 'help'
        ])
        for option, value in options:
            if option in ('-n', '--dry-run'):
                dry_run = True
            elif option in ('-v', '--verbose'):
                coloredlogs.increase_verbosity()
            elif option in ('-q', '--quiet'):
                coloredlogs.decrease_verbosity()
            elif option in ('-h', '--help'):
                usage(USAGE_TEXT)
                sys.exit(0)
            else:
                assert False, "Unhandled option!"
        return dry_run
    except Exception as e:
        warning("Error: Failed to parse command line arguments! (%s)", e)
        sys.exit(1)


def ensure_root_privileges():
    """
    Make sure we have root privileges.
    """
    if os.getuid() != 0:
        warning("Error: Please run this command as root!")
        sys.exit(1)


def find_cron_daemon():
    """
    Find the cron daemon process.

    :returns: A :class:`~proc.tree.ProcessNode` object.
    :raises: :exc:`CronDaemonNotRunning` when the cron daemon process cannot
             be located.
    """
    init = get_process_tree()
    cron = init.find(exe_name='cron')
    if not cron:
        raise CronDaemonNotRunning("Failed to determine process id of cron daemon process! Is it running?")
    return cron


def run_additions():
    """
    Allow local additions to the behavior of ``cron-graceful``.

    If a command with the name of :data:`ADDITIONS_SCRIPT_NAME` exists in the
    ``$PATH`` it will be executed directly after the cron daemon is paused by
    :func:`cron_graceful()`. This allows you to inject custom logic into the
    graceful shutdown process. If the command fails a warning will be logged
    but the ``cron-graceful`` program will continue.
    """
    matching_programs = which(ADDITIONS_SCRIPT_NAME)
    if matching_programs:
        logger.info("Running command %s ..", matching_programs[0])
        try:
            execute(matching_programs[0], shell=False)
        except ExternalCommandFailed as e:
            logger.warning("Command failed with exit status %i!", e.returncode)


def wait_for_processes(processes):
    """
    Wait for the given processes to end.

    Prints an overview of running processes to the terminal once a second so
    the user knows what they are waiting for.

    This function is not specific to :mod:`proc.cron` at all (it doesn't
    even need to know what cron jobs are), it just waits until all of the given
    processes have ended.

    :param processes: A list of :class:`~proc.tree.ProcessNode` objects.
    """
    wait_timer = Timer()
    running_processes = list(processes)
    for process in running_processes:
        logger.info("Waiting for process %i: %s (runtime is %s)",
                    process.pid, quote(process.cmdline), format_timespan(round(process.runtime)))
    with Spinner(timer=wait_timer) as spinner:
        while True:
            for process in list(running_processes):
                if not process.is_alive:
                    running_processes.remove(process)
            if not running_processes:
                break
            num_processes = pluralize(len(running_processes), "process", "processes")
            process_ids = concatenate(str(p.pid) for p in running_processes)
            spinner.step(label="Waiting for %s: %s" % (num_processes, process_ids))
            spinner.sleep()
    logger.info("All processes have finished, we're done waiting (took %s).", wait_timer.rounded)


def terminate_cron_daemon(cron_daemon):
    """
    Terminate the cron daemon.

    :param cron_daemon: The :class:`~proc.tree.ProcessNode` of the cron
                        daemon process.
    """
    # We'll first try to terminate the cron daemon using whatever daemon
    # supervision system is in place (e.g. upstart or systemd) instead of
    # simply killing the cron process, as a signal that we don't want the cron
    # daemon to be restarted.
    logger.info("Stopping cron daemon (service cron stop) ..")
    if not execute('service', 'cron', 'stop', check=False):
        logger.warning("The 'service cron stop' command reported an error!")
    # If the service command failed to terminate the cron daemon we will
    # terminate cron explicitly, in the assumption that we're dealing with a
    # naive /etc/init.d/cron script that doesn't use SIGKILL when SIGTERM fails
    # (due to our earlier SIGSTOP).
    if cron_daemon.is_alive:
        cron_daemon.kill()


class CronDaemonNotRunning(Exception):

    """Exception raised by :func:`find_cron_daemon()` when it cannot locate the cron daemon process."""
