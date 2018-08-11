# Programmer friendly subprocess wrapper.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: January 10, 2017
# URL: https://executor.readthedocs.io

"""
Portable process control functionality for the `executor` package.

The :mod:`executor.process` module defines the :class:`ControllableProcess`
abstract base class which enables process control features like waiting for a
process to end, gracefully terminating it and forcefully killing it. The
process control functionality in :class:`ControllableProcess` is separated from
the command execution functionality in :class:`~executor.ExternalCommand` to
make it possible to re-use the process control functionality in other Python
packages, see for example the :class:`proc.core.Process` class.
"""

# Standard library modules.
import logging

# External dependencies.
from humanfriendly import Spinner, Timer
from property_manager import PropertyManager, mutable_property, required_property

# Initialize a logger for this module.
logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 10
"""The default timeout used to wait for process termination (number of seconds)."""


class ControllableProcess(PropertyManager):

    """
    Abstract, portable process control functionality.

    By defining a subclass of :class:`ControllableProcess` and implementing the
    :attr:`pid`, :attr:`command_line` and :attr:`is_running` properties and the
    :func:`terminate_helper()` and :func:`kill_helper()` methods you get the
    :func:`wait_for_process()`, :func:`terminate()` and :func:`kill()` methods
    for free. This decoupling has enabled me to share a lot of code between two
    Python projects of mine with similar goals but very different
    requirements:

    1. The `executor` package builds on top of the :mod:`subprocess` module
       in the Python standard library and strives to be as cross platform
       as possible. This means things like UNIX signals are not an option
       (although signals exist on Windows they are hardly usable). The package
       mostly deals with :class:`subprocess.Popen` objects internally (to hide
       platform specific details as much as possible).

    2. The proc_ package exposes process information available in the Linux
       process information pseudo-file system available at ``/proc``. The
       package mostly deals with process IDs internally. Because this is
       completely specialized to a UNIX environment the use of things
       like UNIX signals is not a problem at all.

    .. _proc: http://proc.readthedocs.org/en/latest/
    """

    @mutable_property
    def command_line(self):
        """
        A list of strings with the command line used to start the process.

        This property may be set or implemented by subclasses to enable
        :func:`__str__()` to render a human friendly representation of a
        :class:`ControllableProcess` object.
        """
        return []

    @property
    def is_running(self):
        """
        :data:`True` if the process is running, :data:`False` otherwise.

        This property must be implemented by subclasses to enable
        :func:`wait_for_process()`, :func:`terminate()` and :func:`kill()` to
        work properly.
        """
        raise NotImplementedError("You need to implement the `is_running' property!")

    @mutable_property
    def logger(self):
        """
        The :class:`logging.Logger` object to use (defaults to the :mod:`executor.process` logger).

        If you are using Python's :mod:`logging` module and you find it
        confusing that command manipulation is logged under the
        :mod:`executor.process` name space instead of the name space of the
        application or library using :mod:`executor` you can set this
        attribute to inject a custom (and more appropriate) logger.
        """
        return logger

    @mutable_property
    def pid(self):
        """
        The process ID (a number) or :data:`None`.

        This property must be set or implemented by subclasses:

        - It provides :func:`wait_for_process()` with a short and unique
          representation of a process that most users will understand.

        - It enables :func:`__str__()` to render a human friendly
          representation of a :class:`ControllableProcess` object.
        """

    def wait_for_process(self, timeout=0, use_spinner=None):
        """
        Wait until the process ends or the timeout expires.

        :param timeout: The number of seconds to wait for the process to
                        terminate after we've asked it nicely (defaults
                        to zero which means we wait indefinitely).
        :param use_spinner: Whether or not to display an interactive spinner
                            on the terminal (using :class:`~humanfriendly.Spinner`)
                            to explain to the user what they are waiting for:

                            - :data:`True` enables the spinner,
                            - :data:`False` disables the spinner,
                            - :data:`None` (the default) means the spinner is
                              enabled when the program is connected to an
                              interactive terminal, otherwise it's disabled.
        :returns: A :class:`~humanfriendly.Timer` object telling you how long
                  it took to wait for the process.
        """
        with Timer(resumable=True) as timer:
            with Spinner(interactive=use_spinner, timer=timer) as spinner:
                while self.is_running:
                    if timeout and timer.elapsed_time >= timeout:
                        break
                    spinner.step(label="Waiting for process %i to terminate" % self.pid)
                    spinner.sleep()
            return timer

    def terminate(self, wait=True, timeout=DEFAULT_TIMEOUT, use_spinner=None):
        """
        Gracefully terminate the process.

        :param wait: Whether to wait for the process to end (a boolean,
                     defaults to :data:`True`).
        :param timeout: The number of seconds to wait for the process to
                        terminate after we've signaled it (defaults to
                        :data:`DEFAULT_TIMEOUT`). Zero means to wait
                        indefinitely.
        :param use_spinner: See the :func:`wait_for_process()` documentation.
        :returns: :data:`True` if the process was terminated, :data:`False`
                  otherwise.
        :raises: Any exceptions raised by :func:`terminate_helper()`
                 implementations of subclasses or :func:`kill()`.

        This method works as follows:

        1. Signal the process to gracefully terminate itself. Processes can
           choose to intercept termination signals to allow for graceful
           termination (many UNIX daemons work like this) however the default
           action is to simply exit immediately.

        2. If `wait` is :data:`True` and we've signaled the process, we wait
           for it to terminate gracefully or `timeout` seconds have passed
           (whichever comes first).

        3. If `wait` is :data:`True` and the process is still running after
           `timeout` seconds have passed, it will be forcefully terminated
           using :func:`kill()` (the value of `timeout` that was given to
           :func:`terminate()` will be passed on to :func:`kill()`).

        This method does nothing when :attr:`is_running` is :data:`False`.
        """
        if self.is_running:
            self.logger.info("Gracefully terminating process %s ..", self)
            self.terminate_helper()
            if wait:
                timer = self.wait_for_process(timeout=timeout, use_spinner=use_spinner)
                if self.is_running:
                    self.logger.warning("Failed to gracefully terminate process! (waited %s)", timer)
                    return self.kill(wait=True, timeout=timeout)
                else:
                    self.logger.info("Successfully terminated process in %s.", timer)
                    return True
            return not self.is_running
        else:
            return False

    def terminate_helper(self):
        """Request the process to gracefully terminate itself (needs to be implemented by subclasses)."""
        raise NotImplementedError("You need to implement the terminate_helper() method!")

    def kill(self, wait=True, timeout=DEFAULT_TIMEOUT, use_spinner=None):
        """
        Forcefully kill the process.

        :param wait: Whether to wait for the process to end (a boolean,
                     defaults to :data:`True`).
        :param timeout: The number of seconds to wait for the process to
                        terminate after we've signaled it (defaults to
                        :data:`DEFAULT_TIMEOUT`). Zero means to wait
                        indefinitely.
        :param use_spinner: See the :func:`wait_for_process()` documentation.
        :returns: :data:`True` if the process was killed, :data:`False`
                  otherwise.
        :raises: - Any exceptions raised by :func:`kill_helper()`
                   implementations of subclasses.
                 - :exc:`ProcessTerminationFailed` if the process is still
                   running after :func:`kill_helper()` and
                   :func:`wait_for_process()` have been called.

        This method does nothing when :attr:`is_running` is :data:`False`.
        """
        if self.is_running:
            self.logger.info("Forcefully killing process %s ..", self)
            self.kill_helper()
            if wait:
                timer = self.wait_for_process(timeout=timeout, use_spinner=use_spinner)
                if self.is_running:
                    self.logger.warning("Failed to forcefully kill process! (waited %s)", timer)
                    raise ProcessTerminationFailed(process=self, message="Failed to kill process! (%s)" % self)
                else:
                    self.logger.info("Successfully killed process in %s.", timer)
                    return True
            return not self.is_running
        else:
            return False

    def kill_helper(self):
        """Forcefully kill the process (needs to be implemented by subclasses)."""
        raise NotImplementedError("You need to implement the kill_helper() method!")

    def __str__(self):
        """
        Render a human friendly representation of a :class:`ControllableProcess` object.

        :returns: A string describing the process. Includes the process ID and the
                  command line (when available).
        """
        text = []
        # Include the process ID? (only when it's available)
        if self.pid is not None:
            text.append(str(self.pid))
        # Include the command line? (again, only when it's available)
        if self.command_line:
            # We import here to avoid circular imports.
            from executor import quote
            text.append("(%s)" % quote(self.command_line))
        if not text:
            # If all else fails we fall back to the super class.
            text.append(object.__str__(self))
        return " ".join(text)


class ProcessTerminationFailed(PropertyManager, Exception):

    """Raised when process termination fails."""

    def __init__(self, *args, **kw):
        """
        Initialize a :class:`ProcessTerminationFailed` object.

        This method's signature is the same as the initializer of the
        :class:`~property_manager.PropertyManager` class.
        """
        PropertyManager.__init__(self, *args, **kw)
        Exception.__init__(self, self.message)

    @required_property(usage_notes=False)
    def process(self):
        """The :class:`ControllableProcess` object that triggered the exception."""

    @required_property(usage_notes=False)
    def message(self):
        """An error message that explains how the process termination failed."""
