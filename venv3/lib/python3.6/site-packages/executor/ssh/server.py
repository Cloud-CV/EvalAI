# Programmer friendly subprocess wrapper.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 4, 2018
# URL: https://executor.readthedocs.io

"""
OpenSSH server automation for testing.

The :mod:`executor.ssh.server` module defines the :class:`SSHServer` class
which can be used to start temporary OpenSSH servers that are isolated enough
from the host system to make them usable in the :mod:`executor` test suite (to
test remote command execution).
"""

# Standard library modules.
import logging
import os
import shutil
import tempfile

# Modules included in our package.
from executor import execute, which
from executor.tcp import EphemeralTCPServer, TimeoutError

# External dependencies.
from humanfriendly import Timer

# Public identifiers that require documentation.
__all__ = (
    'SSHD_PROGRAM_NAME',
    'SSHServer',
    'logger',
    # Backwards compatibility.
    'EphemeralTCPServer',
    'TimeoutError',
)

# Initialize a logger.
logger = logging.getLogger(__name__)

SSHD_PROGRAM_NAME = 'sshd'
"""The name of the SSH server executable (a string)."""


class SSHServer(EphemeralTCPServer):

    """
    Subclass of :class:`.ExternalCommand` that manages a temporary SSH server.

    The OpenSSH server spawned by the :class:`SSHServer` class doesn't need
    `superuser privileges`_ and doesn't require any changes to ``/etc/passwd``
    or ``/etc/shadow``.
    """

    def __init__(self, **options):
        """
        Initialize an :class:`SSHServer` object.

        :param options: All keyword arguments are passed on to
                        :func:`executor.ExternalCommand.__init__()`.
        """
        self.temporary_directory = tempfile.mkdtemp(prefix='executor-', suffix='-ssh-server')
        """
        The pathname of the temporary directory used to store the files
        required to run the SSH server (a string).
        """
        self.client_key_file = os.path.join(self.temporary_directory, 'client-key')
        """The pathname of the generated OpenSSH client key file (a string)."""
        self.config_file = os.path.join(self.temporary_directory, 'config')
        """The pathname of the generated OpenSSH server configuration file (a string)."""
        self.host_key_file = os.path.join(self.temporary_directory, 'host-key')
        """The random port number on which the SSH server will listen (an integer)."""
        # Initialize the superclass.
        options.setdefault('scheme', 'ssh')
        options.setdefault('logger', logger)
        super(SSHServer, self).__init__(self.sshd_path, '-D', '-f', self.config_file, **options)

    @property
    def sshd_path(self):
        """The absolute pathname of :data:`SSHD_PROGRAM_NAME` (a string)."""
        executables = which(SSHD_PROGRAM_NAME)
        return executables[0] if executables else SSHD_PROGRAM_NAME

    @property
    def client_options(self):
        """
        The options for the OpenSSH client (required to connect with the server).

        This is a dictionary of keyword arguments for :class:`.RemoteCommand`
        to make it connect with the OpenSSH server (assuming the remote command
        connects to an IP address in the 127.0.0.0/24 range).
        """
        return dict(identity_file=self.client_key_file,
                    ignore_known_hosts=True,
                    port=self.port_number)

    def start(self, **options):
        """
        Start the SSH server and wait for it to start accepting connections.

        :param options: Any keyword arguments are passed to the
                        :func:`~EphemeralTCPServer.start()` method of the
                        superclass.
        :raises: Any exceptions raised by the
                 :func:`~EphemeralTCPServer.start()` method of the superclass.

        The :func:`start()` method automatically calls the
        :func:`generate_key_file()` and :func:`generate_config()` methods.
        """
        if not self.was_started:
            self.logger.debug("Preparing to start SSH server ..")
            for key_file in (self.host_key_file, self.client_key_file):
                self.generate_key_file(key_file)
            self.generate_config()
            super(SSHServer, self).start()

    def generate_key_file(self, filename):
        """
        Generate a temporary host or client key for the OpenSSH server.

        The :func:`start()` method automatically calls :func:`generate_key_file()`
        to generate :data:`host_key_file` and :attr:`client_key_file`. This
        method uses the ``ssh-keygen`` program to generate the keys.
        """
        if not os.path.isfile(filename):
            timer = Timer()
            self.logger.debug("Generating SSH key file (%s) ..", filename)
            execute('ssh-keygen', '-f', filename, '-N', '', '-t', 'rsa', silent=True, logger=self.logger)
            self.logger.debug("Generated key file %s in %s.", filename, timer)

    def generate_config(self):
        """
        Generate a configuration file for the OpenSSH server.

        The :func:`start()` method automatically calls
        :func:`generate_config()`.
        """
        if not os.path.isfile(self.config_file):
            self.logger.debug("Generating SSH server configuration (%s) ..", self.config_file)
            with open(self.config_file, 'w') as handle:
                handle.write("AllowUsers %s\n" % os.environ['USER'])
                handle.write("AuthorizedKeysFile %s.pub\n" % (self.client_key_file))
                handle.write("HostKey %s\n" % self.host_key_file)
                handle.write("LogLevel QUIET\n")
                handle.write("PasswordAuthentication no\n")
                handle.write("PidFile %s/sshd.pid\n" % self.temporary_directory)
                handle.write("Port %i\n" % self.port_number)
                handle.write("StrictModes no\n")
                handle.write("UsePAM no\n")
                handle.write("UsePrivilegeSeparation no\n")

    def cleanup(self):
        """Clean up :attr:`temporary_directory` after the test server finishes."""
        if self.temporary_directory:
            if os.path.isdir(self.temporary_directory):
                self.logger.debug("Cleaning up temporary directory %s ..", self.temporary_directory)
                shutil.rmtree(self.temporary_directory)
            self.temporary_directory = None
        super(SSHServer, self).cleanup()
