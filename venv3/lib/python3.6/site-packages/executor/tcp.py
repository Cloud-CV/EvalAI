# Programmer friendly subprocess wrapper.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 20, 2018
# URL: https://executor.readthedocs.io

"""
Miscellaneous TCP networking functionality.

The functionality in this module originated in the :class:`executor.ssh.server`
module with the purpose of facilitating a robust automated test suite for the
:class:`executor.ssh.client` module. While working on SSH tunnel support I
needed similar logic again and I decided to extract this code from the
:class:`executor.ssh.server` module.
"""

# Standard library modules.
import itertools
import logging
import random
import socket

# Modules included in our package.
from executor import ExternalCommand

# External dependencies.
from humanfriendly import (
    Spinner,
    Timer,
    format,
    format_timespan,
    pluralize,
)
from property_manager import (
    PropertyManager,
    lazy_property,
    mutable_property,
    required_property,
    set_property,
)

# Public identifiers that require documentation.
__all__ = (
    'EphemeralPortAllocator',
    'EphemeralTCPServer',
    'TimeoutError',
    'WaitUntilConnected',
    'logger',
)

# Initialize a logger.
logger = logging.getLogger(__name__)


class WaitUntilConnected(PropertyManager):

    """Wait for a TCP endpoint to start accepting connections."""

    @mutable_property
    def connect_timeout(self):
        """The timeout in seconds for individual connection attempts (a number, defaults to 2)."""
        return 2

    @mutable_property
    def hostname(self):
        """The host name or IP address to connect to (a string, defaults to ``localhost``)."""
        return 'localhost'

    @property
    def is_connected(self):
        """:data:`True` if a connection was accepted, :data:`False` otherwise."""
        timer = Timer()
        logger.debug("Checking whether %s is accepting connections ..", self)
        try:
            socket.create_connection((self.hostname, self.port_number), self.connect_timeout)
            logger.debug("Yes %s is accepting connections (took %s).", self, timer)
            return True
        except Exception:
            logger.debug("No %s isn't accepting connections (took %s).", self, timer)
            return False

    @required_property
    def port_number(self):
        """The port number to connect to (an integer)."""

    @mutable_property
    def scheme(self):
        """A URL scheme that indicates the purpose of the ephemeral port (a string, defaults to 'tcp')."""
        return 'tcp'

    @mutable_property
    def wait_timeout(self):
        """The timeout in seconds for :func:`wait_until_connected()` (a number, defaults to 30)."""
        return 30

    def wait_until_connected(self):
        """
        Wait until connections are being accepted.

        :raises: :exc:`TimeoutError` when the SSH server isn't fast enough to
                 initialize.
        """
        timer = Timer()
        with Spinner(timer=timer) as spinner:
            while not self.is_connected:
                if timer.elapsed_time > self.wait_timeout:
                    raise TimeoutError(format(
                        "Failed to establish connection to %s within configured timeout of %s!",
                        self, format_timespan(self.wait_timeout),
                    ))
                spinner.step(label="Waiting for %s to accept connections" % self)
                spinner.sleep()
        logger.debug("Waited %s for %s to accept connections.", timer, self)

    def __str__(self):
        """Render a human friendly representation."""
        return format("%s://%s:%i", self.scheme, self.hostname, self.port_number)


class EphemeralPortAllocator(WaitUntilConnected):

    """
    Allocate a free `ephemeral port number`_.

    .. _ephemeral port number: \
        http://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers#Dynamic.2C_private_or_ephemeral_ports
    """

    @lazy_property
    def port_number(self):
        """A dynamically selected free ephemeral port number (an integer between 49152 and 65535)."""
        timer = Timer()
        logger.debug("Looking for free ephemeral port number ..")
        for i in itertools.count(1):
            value = self.ephemeral_port_number
            set_property(self, 'port_number', value)
            if not self.is_connected:
                logger.debug("Found free ephemeral port number %s after %s (took %s).",
                             self, pluralize(i, "attempt"), timer)
                return value

    @property
    def ephemeral_port_number(self):
        """A random ephemeral port number (an integer between 49152 and 65535)."""
        return random.randint(49152, 65535)


class EphemeralTCPServer(ExternalCommand, EphemeralPortAllocator):

    """
    Make it easy to launch ephemeral TCP servers.

    The :class:`EphemeralTCPServer` class makes it easy to allocate an
    `ephemeral port number`_ that is not (yet) in use.

    .. _ephemeral port number: \
        http://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers#Dynamic.2C_private_or_ephemeral_ports
    """

    @property
    def async(self):
        """Ephemeral TCP servers always set :attr:`.ExternalCommand.async` to :data:`True`."""
        return True

    def start(self, **options):
        """
        Start the TCP server and wait for it to start accepting connections.

        :param options: Any keyword arguments are passed to the
                        :func:`~executor.ExternalCommand.start()` method of the
                        superclass.
        :raises: Any exceptions raised by :func:`~executor.ExternalCommand.start()`
                 and :func:`~executor.tcp.WaitUntilConnected.wait_until_connected()`.

        If the TCP server doesn't start accepting connections within the
        configured timeout (see :attr:`~executor.tcp.WaitUntilConnected.wait_timeout`)
        the process will be terminated and the timeout exception is propagated.
        """
        if not self.was_started:
            logger.debug("Preparing to start %s server ..", self.scheme.upper())
            super(EphemeralTCPServer, self).start(**options)
            try:
                self.wait_until_connected()
            except TimeoutError:
                self.terminate()
                raise


class TimeoutError(Exception):

    """
    Raised when a TCP server doesn't start accepting connections quickly enough.

    This exception is raised by :func:`~executor.tcp.WaitUntilConnected.wait_until_connected()`
    when the TCP server doesn't start accepting connections within a reasonable time.
    """
