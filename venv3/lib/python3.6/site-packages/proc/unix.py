# proc: Simple interface to Linux process information.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: June 1, 2016
# URL: https://proc.readthedocs.io

"""
The :mod:`proc.unix` module manipulates UNIX processes using signals.

This module contains no Linux-specific details, instead it relies only on
process IDs and common UNIX signal semantics to:

1. Determine whether a given process ID is still alive (signal 0);
2. gracefully (SIGTERM_) and forcefully (SIGKILL) terminate processes;
3. suspend (SIGSTOP_) and resume (SIGCONT_) processes.

.. _SIGTERM: http://en.wikipedia.org/wiki/Unix_signal#SIGTERM
.. _SIGKILL: http://en.wikipedia.org/wiki/Unix_signal#SIGKILL
.. _SIGSTOP: http://en.wikipedia.org/wiki/Unix_signal#SIGSTOP
.. _SIGCONT: http://en.wikipedia.org/wiki/Unix_signal#SIGCONT
"""

# Standard library modules.
import errno
import logging
import os
import signal

# External dependencies.
from executor.process import ControllableProcess
from property_manager import required_property

# Initialize a logger.
logger = logging.getLogger(__name__)


class UnixProcess(ControllableProcess):

    """
    Integration between :class:`executor.process.ControllableProcess` and common UNIX signals.

    :class:`UnixProcess` extends :class:`~executor.process.ControllableProcess` which means
    all of the process manipulation supported by :class:`~executor.process.ControllableProcess`
    is also supported by :class:`UnixProcess` objects.
    """

    @required_property
    def pid(self):
        """The process ID of the process (an integer)."""

    @property
    def is_running(self):
        """
        :data:`True` if the process is currently running, :data:`False` otherwise.

        This implementation sends the signal number zero to :attr:`pid` and
        uses the result to infer whether the process is alive or not (this
        technique is documented in `man kill`_):

        - If the sending of the signal doesn't raise an exception the process
          received the signal just fine and so must it exist.

        - If an :exc:`~exceptions.OSError` exception with error number
          :data:`~errno.EPERM` is raised we don't have permission to signal the
          process, which implies that the process is alive.

        - If an :exc:`~exceptions.OSError` exception with error number
          :data:`~errno.ESRCH` is raised we know that no process with the given
          id exists.

        An advantage of this approach (on UNIX systems) is that you don't need
        to be a parent of the process in question. A disadvantage of this
        approach is that it is never going to work on Windows (if you're
        serious about portability consider using a package like psutil_).

        .. warning:: After a process has been terminated but before the parent
                     process has reclaimed its child process this property
                     returns :data:`True`. Usually this is a small time window,
                     but when it isn't it can be really confusing.

        .. _man kill: http://linux.die.net/man/2/kill
        .. _psutil: https://pypi.python.org/pypi/psutil
        """
        # Querying in-use process IDs is a platform specific operation that
        # Python doesn't provide, however sending the signal number zero is
        # a platform specific trick that works on most UNIX systems.
        logger.debug("Polling process status using signal 0: %s", self)
        try:
            os.kill(self.pid, 0)
            # If no exception is raised we successfully sent a NOOP signal
            # to the process so we know the process is (still) alive.
            logger.debug("Successfully sent signal 0, process must be alive.")
            return True
        except OSError as e:
            if e.errno == errno.EPERM:
                # If we don't have permission this confirms that the
                # process ID is in use.
                logger.debug("Got EPERM, process must be alive.")
                return True
            elif e.errno == errno.ESRCH:
                # If we get this error we know the process doesn't exist.
                logger.debug("Got ESRCH, process can't be alive.")
                return False
            else:
                # Don't swallow exceptions we can't handle.
                raise

    def terminate_helper(self):
        """
        Gracefully terminate the process (by sending it a SIGTERM_ signal).

        :raises: :exc:`~exceptions.OSError` when the signal can't be delivered.

        Processes can choose to intercept SIGTERM_ to allow for graceful
        termination (many daemon processes work like this) however the default
        action is to simply exit immediately.
        """
        if self.is_running:
            logger.debug("Terminating process with SIGTERM: %s", self)
            os.kill(self.pid, signal.SIGTERM)

    def kill_helper(self):
        """
        Forcefully kill the process (by sending it a SIGKILL_ signal).

        :raises: :exc:`~exceptions.OSError` when the signal can't be delivered.

        The SIGKILL_ signal cannot be intercepted or ignored and causes the
        immediate termination of the process (under regular circumstances).
        Non-regular circumstances are things like blocking I/O calls on an NFS
        share while your file server is down (fun times!).
        """
        if self.is_running:
            logger.debug("Killing process with SIGKILL: %s", self)
            os.kill(self.pid, signal.SIGKILL)

    def suspend(self):
        """
        Suspend the process so that its execution can be resumed later.

        :raises: :exc:`~exceptions.OSError` when the signal can't be delivered.

        The :func:`suspend()` method sends a SIGSTOP_ signal to the process.
        This signal cannot be intercepted or ignored and has the effect of
        completely pausing the process until you call :func:`resume()`.

        .. _SIGSTOP: http://en.wikipedia.org/wiki/Unix_signal#SIGSTOP
        """
        if self.is_running:
            logger.info("Suspending process %s using SIGSTOP ..", self)
            os.kill(self.pid, signal.SIGSTOP)

    def resume(self):
        """
        Resume a process that was previously paused using :func:`suspend()`.

        :raises: :exc:`~exceptions.OSError` when the signal can't be delivered.

        The :func:`resume()` method sends a SIGCONT_ signal to the process.
        This signal resumes a process that was previously paused using SIGSTOP_
        (e.g. using :func:`suspend()`).

        .. _SIGCONT: http://en.wikipedia.org/wiki/Unix_signal#SIGCONT
        """
        if self.is_running:
            logger.info("Resuming process %s using SIGCONT ..", self)
            os.kill(self.pid, signal.SIGCONT)
