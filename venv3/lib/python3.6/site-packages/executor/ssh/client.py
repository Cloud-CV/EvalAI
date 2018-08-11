# Programmer friendly subprocess wrapper.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 4, 2018
# URL: https://executor.readthedocs.io

"""
Remote command execution using SSH.

The :mod:`executor.ssh.client` module defines the :class:`RemoteCommand` class
and the :func:`foreach()` function which make it easy to run a remote command
in parallel on multiple remote hosts using SSH.

The :func:`foreach()` function also serves as a simple example of how to use
:class:`~executor.concurrent.CommandPool` and :class:`RemoteCommand` objects
(it's just 16 lines of code if you squint in the right way and that includes
logging :-).

The :class:`SecureTunnel` class makes it easy to use "tunnel only"
SSH connections by waiting until the tunnel becomes connected and
automatically selecting a free ephemeral port number if a
local port number isn't provided by the caller.
"""

# Standard library modules.
import logging
import os

# External dependencies.
from humanfriendly import Timer, concatenate, pluralize
from property_manager import (
    PropertyManager,
    mutable_property,
    required_property,
    set_property,
)

# Modules included in our package.
from executor import (
    COMMAND_NOT_FOUND_STATUS,
    DEFAULT_WORKING_DIRECTORY,
    CommandNotFound,
    ExternalCommand,
    ExternalCommandFailed,
    execute_prepared,
    quote,
)
from executor.concurrent import CommandPool
from executor.tcp import (
    EphemeralPortAllocator,
    WaitUntilConnected,
)

# Initialize a logger.
logger = logging.getLogger(__name__)

DEFAULT_CONCURRENCY = 10
"""
The default :attr:`~.CommandPool.concurrency` value to use for
:class:`.CommandPool` objects created by :func:`foreach()`.
"""

DEFAULT_CONNECT_TIMEOUT = 10
"""
The default :attr:`~.RemoteCommand.connect_timeout` value to use for
:class:`RemoteCommand` objects.
"""

SSH_PROGRAM_NAME = 'ssh'
"""The name of the SSH client executable (a string)."""

SSH_ERROR_STATUS = 255
"""
The exit status used by the ``ssh`` program if an error occurred (an integer).

Used by :attr:`RemoteCommand.error_message` and
:attr:`RemoteCommand.error_type` to distinguish when the ``ssh`` program itself
fails and when a remote command fails.
"""


def foreach(hosts, *command, **options):
    """
    Execute a command simultaneously on a group of remote hosts using SSH.

    :param hosts: An iterable of strings with SSH host aliases.
    :param command: Any positional arguments are converted to a list and used
                    to set the :attr:`~.ExternalCommand.command` property of
                    the :class:`RemoteCommand` objects constructed by
                    :func:`foreach()`.
    :param concurrency: The value of :attr:`.concurrency` to use
                        (defaults to :data:`DEFAULT_CONCURRENCY`).
    :param delay_checks: The value of :attr:`.delay_checks` to use
                         (defaults to :data:`True`).
    :param logs_directory: The value of :attr:`.logs_directory` to
                           use (defaults to :data:`None`).
    :param options: Additional keyword arguments can be used to conveniently
                    override the default values of the writable properties of
                    the :class:`RemoteCommand` objects constructed by
                    :func:`foreach()` (see :func:`RemoteCommand.__init__()` for
                    details).
    :returns: The list of :class:`RemoteCommand` objects constructed by
              :func:`foreach()`.
    :raises: Any of the following exceptions can be raised:

             - :exc:`.CommandPoolFailed` if :attr:`.delay_checks` is enabled
               (the default) and a command in the pool that has :attr:`.check`
               enabled (the default) fails.
             - :exc:`RemoteCommandFailed` if :attr:`.delay_checks` is disabled
               (not the default) and an SSH connection was successful but the
               remote command failed (the exit code of the ``ssh`` command was
               neither zero nor 255). Use the keyword argument ``check=False``
               to disable raising of this exception.
             - :exc:`RemoteConnectFailed` if :attr:`.delay_checks` is disabled
               (not the default) and an SSH connection failed (the exit code of
               the ``ssh`` command is 255). Use the keyword argument
               ``check=False`` to disable raising of this exception.

    .. note:: The :func:`foreach()` function enables the :attr:`.check` and
              :attr:`.delay_checks` options by default in an attempt to make it
              easy to do "the right thing". My assumption here is that if you
              are running *the same command* on multiple remote hosts:

              - You definitely want to know when a remote command has failed,
                ideally without manually checking the :attr:`.succeeded`
                property of each command.

              - Regardless of whether some remote commands fail you want to
                know that the command was at least executed on all hosts,
                otherwise your cluster of hosts will end up in a very
                inconsistent state.

              - If remote commands fail and an exception is raised the
                exception message should explain *which* remote commands
                failed.

              If these assumptions are incorrect then you can use the keyword
              arguments ``check=False`` and/or ``delay_checks=False`` to opt
              out of "doing the right thing" ;-)
    """
    hosts = list(hosts)
    # Separate command pool options from command options.
    concurrency = options.pop('concurrency', DEFAULT_CONCURRENCY)
    delay_checks = options.pop('delay_checks', True)
    logs_directory = options.pop('logs_directory', None)
    # Capture the output of remote commands by default
    # (unless the caller requested capture=False).
    if options.get('capture') is not False:
        options['capture'] = True
    # Enable error checking of remote commands by default
    # (unless the caller requested check=False).
    if options.get('check') is not False:
        options['check'] = True
    # Create a command pool.
    timer = Timer()
    pool = RemoteCommandPool(concurrency=concurrency,
                             delay_checks=delay_checks,
                             logs_directory=logs_directory)
    hosts_pluralized = pluralize(len(hosts), "host")
    logger.debug("Preparing to run remote command on %s (%s) with a concurrency of %i: %s",
                 hosts_pluralized, concatenate(hosts), concurrency, quote(command))
    # Populate the pool with remote commands to execute.
    for ssh_alias in hosts:
        pool.add(identifier=ssh_alias,
                 command=RemoteCommand(ssh_alias, *command, **options))
    # Run all commands in the pool.
    pool.run()
    # Report the results to the caller.
    logger.debug("Finished running remote command on %s in %s.", hosts_pluralized, timer)
    return dict(pool.commands).values()


def remote(ssh_alias, *command, **options):
    """
    Execute a remote command (similar to :func:`.execute()`).

    :param ssh_alias: Used to set :attr:`RemoteAccount.ssh_alias`.
    :param command: All positional arguments are passed to
                    :func:`RemoteCommand.__init__()`.
    :param options: All keyword arguments are passed to
                    :func:`RemoteCommand.__init__()`.
    :returns: Refer to :func:`.execute_prepared()`.
    :raises: :exc:`RemoteCommandFailed` when the command exits with a
             nonzero exit code (and :attr:`~.ExternalCommand.check` is
             :data:`True`).
    """
    return execute_prepared(RemoteCommand(ssh_alias, *command, **options))


class RemoteAccount(PropertyManager):

    """
    Trivial SSH alias parser.

    This class acts as a base class for :class:`RemoteCommand` and
    :class:`.RemoteContext` that provides three simple features:

    - It defines the :attr:`ssh_alias` and :attr:`ssh_user` properties.

    - When :attr:`ssh_alias` is set to a string that contains an ``@`` token it
      parses the string and sets both :attr:`ssh_alias` and :attr:`ssh_user` [#]_.

    - It allows for :attr:`ssh_alias` to be passed as the first positional
      argument [#]_ or as a keyword argument [#]_.

    .. [#] This enables :attr:`RemoteCommand.have_superuser_privileges` to know
           that superuser privileges are available when the caller sets
           :attr:`ssh_alias` to a value like ``root@host``. Of course the SSH
           client configuration can also override the remote username without
           the `executor` package knowing about it, but at least `executor`
           will be able to use the information that it does have.

    .. [#] This calling convention enables backwards compatibility with
           `executor` versions 14 and below which required :attr:`ssh_alias` to
           be set using the first positional argument to the initializer of the
           :class:`RemoteCommand` class.

    .. [#] This new calling convention provides a uniform calling convention
           for the initializers of the local/remote command/context classes.
    """

    def __init__(self, *args, **options):
        """
        Initialize a :class:`RemoteAccount` object.

        :param args: Positional arguments are passed on to the initializer of
                     the :class:`~property_manager.PropertyManager` class
                     (for future extensibility).
        :param options: Any keyword arguments are passed on to the initializer
                        of the :class:`~property_manager.PropertyManager`
                        class.

        If the keyword argument `ssh_alias` isn't given but positional
        arguments are provided, the first positional argument is used to set
        the :attr:`ssh_alias` property.
        """
        # Enable modification of the positional arguments.
        args = list(args)
        # We allow `ssh_alias' to be passed as a keyword argument but use the
        # first positional argument when the keyword argument isn't given.
        if options.get('ssh_alias') is None and args:
            options['ssh_alias'] = args.pop(0)
        # Initialize the superclass.
        super(RemoteAccount, self).__init__(*args, **options)

    @required_property
    def ssh_alias(self):
        """
        The SSH alias of the remote host (a string).

        If you set this property to a string that contains two nonempty tokens
        delimited by an ``@`` character, the first token is used to set
        :attr:`ssh_user` and the second token is used to set
        :attr:`ssh_alias`. Here's an example:

        >>> from executor.ssh.client import RemoteAccount
        >>> RemoteAccount('root@server')
        RemoteAccount(ssh_alias='server', ssh_user='root')
        >>> RemoteAccount(ssh_alias='server', ssh_user='root')
        RemoteAccount(ssh_alias='server', ssh_user='root')
        >>> RemoteAccount('server')
        RemoteAccount(ssh_alias='server', ssh_user=None)
        """

    @ssh_alias.setter
    def ssh_alias(self, value):
        """Set the value of :attr:`ssh_alias` and optionally :attr:`ssh_user`."""
        user, _, host = value.partition('@')
        if user and host:
            set_property(self, 'ssh_alias', host)
            set_property(self, 'ssh_user', user)
        else:
            set_property(self, 'ssh_alias', value)

    @mutable_property
    def ssh_user(self):
        """
        The username on the remote system (a string or :data:`None`).

        If the value of :attr:`ssh_user` is :data:`None` the SSH client program
        gets to decide about the remote username.
        """


class RemoteCommand(RemoteAccount, ExternalCommand):

    """:class:`RemoteCommand` objects use the SSH client program to execute remote commands."""

    def __init__(self, *args, **options):
        """
        Initialize a :class:`RemoteCommand` object.

        :param args: Refer to the initializers of the :class:`RemoteAccount`
                     and :class:`.ExternalCommand` classes.
        :param options: Keyword arguments can be used to conveniently override
                        the values of :attr:`batch_mode`,
                        :attr:`connect_timeout`, :attr:`identity_file`,
                        :attr:`ignore_known_hosts`, :attr:`log_level`,
                        :attr:`port`, :attr:`strict_host_key_checking`,
                        :attr:`known_hosts_file`, :attr:`ssh_command` and the
                        writable properties of the base classes
                        :class:`RemoteAccount` and :class:`.ExternalCommand`.
                        Any other keyword argument will raise :exc:`TypeError`
                        as usual.

        The remote command is not started until you call
        :func:`~executor.ExternalCommand.start()` or
        :func:`~executor.ExternalCommand.wait()`.
        """
        # Inject our logger as a default.
        options.setdefault('logger', logger)
        # Set the default remote working directory.
        self.remote_directory = DEFAULT_WORKING_DIRECTORY
        # Initialize the super class.
        super(RemoteCommand, self).__init__(*args, **options)

    @mutable_property
    def batch_mode(self):
        """
        Control the SSH client option ``BatchMode`` (a boolean, defaults to :data:`True`).

        The following description is quoted from `man ssh_config`_:

          If set to "yes", passphrase/password querying will be disabled. In
          addition, the ``ServerAliveInterval`` option will be set to 300
          seconds by default. This option is useful in scripts and other batch
          jobs where no user is present to supply the password, and where it is
          desirable to detect a broken network swiftly. The argument must be
          "yes" or "no". The default is "no".

        This property defaults to :data:`True` because it can get really
        awkward when a batch of SSH clients query for a passphrase/password on
        standard input at the same time.

        .. _man ssh_config: http://www.openbsd.org/cgi-bin/man.cgi/OpenBSD-current/man5/ssh_config.5
        """
        return True

    @mutable_property
    def command(self):
        """
        A list of strings with the command to execute (optional).

        The value of :attr:`command` is optional for :class:`RemoteCommand`
        objects (as opposed to :class:`.ExternalCommand` objects) because the
        use of SSH implies a remote (interactive) shell that usually also
        accepts (interactive) commands as input. This means it is valid to
        create a remote command object without an actual remote command to
        execute, but with input that provides commands to execute instead.

        This "feature" can be useful to control non-UNIX systems that do accept
        SSH connections but don't support a conventional UNIX shell. For
        example, I added support for this "feature" so that I was able to send
        commands to Juniper routers and switches over SSH with the purpose of
        automating the failover of a connection between two datacenters (the
        resulting Python program works great and it's much faster than I am,
        making all of the required changes in a couple of seconds :-).
        """
        return []

    @property
    def command_line(self):
        """
        The complete SSH client command including the remote command.

        This is a list of strings with the SSH client command to connect to the
        remote host and execute :attr:`~.ExternalCommand.command`.
        """
        ssh_command = list(self.ssh_command)
        if self.identity_file:
            ssh_command.extend(('-i', self.identity_file))
        if self.ssh_user:
            ssh_command.extend(('-l', self.ssh_user))
        if self.port:
            ssh_command.extend(('-p', '%i' % self.port))
        ssh_command.extend(('-o', 'BatchMode=%s' % ('yes' if self.batch_mode else 'no')))
        ssh_command.extend(('-o', 'ConnectTimeout=%i' % self.connect_timeout))
        ssh_command.extend(('-o', 'LogLevel=%s' % self.log_level))
        if self.strict_host_key_checking in ('yes', 'no', 'ask'):
            ssh_command.extend(('-o', 'StrictHostKeyChecking=%s' % self.strict_host_key_checking))
        else:
            ssh_command.extend(('-o', 'StrictHostKeyChecking=%s' % ('yes' if self.strict_host_key_checking else 'no')))
        ssh_command.extend(('-o', 'UserKnownHostsFile=%s' % self.known_hosts_file))
        if self.compression:
            ssh_command.append('-C')
        if self.tty:
            ssh_command.append('-t')
        ssh_command.append(self.ssh_alias)
        remote_command = quote(super(RemoteCommand, self).command_line)
        if remote_command:
            if self.remote_directory != DEFAULT_WORKING_DIRECTORY:
                cd_command = 'cd %s' % quote(self.remote_directory)
                remote_command = quote(self.prefix_shell_command(cd_command, remote_command))
            ssh_command.append(remote_command)
        return ssh_command

    @mutable_property
    def compression(self):
        """Whether compression is enabled (a boolean, defaults to :data:`False`)."""
        return False

    @mutable_property
    def connect_timeout(self):
        """
        Control the SSH client option ``ConnectTimeout`` (an integer).

        The following description is quoted from `man ssh_config`_:

          Specifies the timeout (in seconds) used when connecting to the SSH
          server, instead of using the default system TCP timeout. This value
          is used only when the target is down or really unreachable, not when
          it refuses the connection.

        Defaults to :data:`DEFAULT_CONNECT_TIMEOUT` so that non-interactive SSH
        connections created by :class:`RemoteCommand` don't hang indefinitely
        when the remote system doesn't respond properly.
        """
        return DEFAULT_CONNECT_TIMEOUT

    @property
    def directory(self):
        """
        Set the remote working directory.

        When you set this property you change the remote working directory,
        however reading back the property you'll just get
        :data:`.DEFAULT_WORKING_DIRECTORY`. This is because the superclass
        :class:`.ExternalCommand` uses :attr:`directory` as the local working
        directory for the ``ssh`` command, and a remote working directory isn't
        guaranteed to also exist on the local system.
        """
        return DEFAULT_WORKING_DIRECTORY

    @directory.setter
    def directory(self, value):
        """Redirect assignment from `directory` to `remote_directory`."""
        self.remote_directory = value

    @mutable_property
    def error_message(self):
        """A user friendly explanation of how the remote command failed (a string or :data:`None`)."""
        messages = {
            RemoteCommandFailed: "External command on {a} failed with exit code {n}!",
            RemoteCommandNotFound: "External command on {a} isn't available!",
            RemoteConnectFailed: "SSH connection to {a} failed!",
        }
        if self.error_type in messages:
            return self.format_error_message("\n\n".join([
                messages[self.error_type], "SSH command:\n{c}",
            ]), a=self.ssh_alias, n=self.returncode, c=quote(self.command_line))

    @mutable_property
    def error_type(self):
        """
        An exception class applicable to the kind of failure detected or :data:`None`.

        :class:`RemoteConnectFailed` when :attr:`~.ExternalCommand.returncode`
        is set and matches :data:`SSH_ERROR_STATUS`, :class:`RemoteCommandFailed`
        when :attr:`~.ExternalCommand.returncode` is set and not zero,
        :data:`None` otherwise.
        """
        if self.returncode == SSH_ERROR_STATUS:
            return RemoteConnectFailed
        elif self.returncode == COMMAND_NOT_FOUND_STATUS:
            return RemoteCommandNotFound
        elif self.returncode not in (None, 0):
            return RemoteCommandFailed

    @property
    def have_superuser_privileges(self):
        """
        :data:`True` if :attr:`.ssh_user` is set to 'root', :data:`False` otherwise.

        There's no easy way for :class:`RemoteCommand` to determine whether any
        given SSH alias logs into a remote system with `superuser privileges`_
        so unless :attr:`.ssh_user` is set to 'root' this is always
        :data:`False`.

        .. _superuser privileges: http://en.wikipedia.org/wiki/Superuser#Unix_and_Unix-like
        """
        return self.ssh_user == 'root'

    @mutable_property
    def identity_file(self):
        """The pathname of the identity file used to connect to the remote host (a string or :data:`None`)."""

    @property
    def ignore_known_hosts(self):
        """
        Whether host key checking is disabled.

        This is :data:`True` if host key checking is completely disabled:

        - :attr:`known_hosts_file` is set to :data:`os.devnull`
        - :attr:`strict_host_key_checking` is set to :data:`False`

        If you set this to :data:`True` host key checking is disabled and
        :attr:`log_level` is set to 'error' to silence warnings about
        automatically accepting host keys.

        If you set this to :data:`False` then :attr:`known_hosts_file`,
        :attr:`log_level` and :attr:`strict_host_key_checking` are reset to
        their default values.
        """
        return self.known_hosts_file == os.devnull and self.strict_host_key_checking in (False, 'no')

    @ignore_known_hosts.setter
    def ignore_known_hosts(self, value):
        if value:
            self.known_hosts_file = os.devnull
            self.log_level = 'error'
            self.strict_host_key_checking = False
        else:
            del self.known_hosts_file
            del self.log_level
            del self.strict_host_key_checking

    @mutable_property
    def log_level(self):
        """
        Control the SSH client option ``LogLevel`` (a string, defaults to 'info').

        The following description is quoted from `man ssh_config`_:

          Gives the verbosity level that is used when logging messages from
          ``ssh``. The possible values are: QUIET, FATAL, ERROR, INFO, VERBOSE,
          DEBUG, DEBUG1, DEBUG2, and DEBUG3. The default is INFO. DEBUG and
          DEBUG1 are equivalent. DEBUG2 and DEBUG3 each specify higher levels
          of verbose output.
        """
        return 'info'

    @mutable_property
    def ssh_command(self):
        """
        The command used to run the SSH client program.

        This is a list of strings, by default the list contains just
        :data:`SSH_PROGRAM_NAME`. The :attr:`batch_mode`, :attr:`connect_timeout`,
        :attr:`log_level`, :attr:`.ssh_alias` and :attr:`strict_host_key_checking`
        properties also influence the SSH client command line used.
        """
        return [SSH_PROGRAM_NAME]

    @mutable_property
    def port(self):
        """The port number of the SSH server (defaults to :data:`None` which means the SSH client program decides)."""

    @mutable_property
    def strict_host_key_checking(self):
        """
        Control the SSH client option ``StrictHostKeyChecking``.

        This property accepts the values :data:`True` and :data:`False` and the
        strings 'yes', 'no' and 'ask'. The following description is quoted from
        `man ssh_config`_:

          If this flag is set to "yes", ``ssh`` will never automatically add
          host keys to the ``~/.ssh/known_hosts`` file, and refuses to connect
          to hosts whose host key has changed. This provides maximum protection
          against trojan horse attacks, though it can be annoying when the
          ``/etc/ssh/ssh_known_hosts`` file is poorly maintained or when
          connections to new hosts are frequently made. This option forces the
          user to manually add all new hosts. If this flag is set to "no", ssh
          will automatically add new host keys to the user known hosts files.
          If this flag is set to "ask", new host keys will be added to the user
          known host files only after the user has confirmed that is what they
          really want to do, and ssh will refuse to connect to hosts whose host
          key has changed. The host keys of known hosts will be verified
          automatically in all cases. The argument must be "yes", "no", or
          "ask". The default is "ask".

        This property defaults to :data:`False` so that when you connect to a
        remote system over SSH for the first time the host key is automatically
        added to the user known hosts file (instead of requiring interaction).
        As mentioned in the quote above the host keys of known hosts are always
        verified (but see :attr:`ignore_known_hosts`).
        """
        return False

    @mutable_property
    def known_hosts_file(self, value=None):
        """
        Control the SSH client option ``UserKnownHostsFile`` (a string).

        The following description is quoted from `man ssh_config`_:

          Specifies one or more files to use for the user host key database,
          separated by whitespace. The default is ``~/.ssh/known_hosts``,
          ``~/.ssh/known_hosts2``.
        """
        if value is None:
            value = ' '.join([
                os.path.expanduser('~/.ssh/known_hosts'),
                os.path.expanduser('~/.ssh/known_hosts2'),
            ])
        return value


class RemoteCommandPool(CommandPool):

    """
    Execute multiple remote commands concurrently.

    After constructing a :class:`RemoteCommandPool` instance you add commands
    to it using :func:`~executor.concurrent.CommandPool.add()` and when you're
    ready to run the commands you call :func:`~executor.concurrent.CommandPool.run()`.

    .. note:: The only difference between :class:`.CommandPool` and
              :class:`RemoteCommandPool` is the default concurrency. This may
              of course change in the future.
    """

    def __init__(self, concurrency=DEFAULT_CONCURRENCY, **options):
        """
        Initialize a :class:`RemoteCommandPool` object.

        :param concurrency: Override the value of :attr:`~.CommandPool.concurrency`
                            (an integer, defaults to :data:`DEFAULT_CONCURRENCY`
                            for remote command pools).
        :param options: Any additional keyword arguments are passed on
                        to the :class:`.CommandPool` constructor.
        """
        super(RemoteCommandPool, self).__init__(concurrency, **options)


class SecureTunnel(RemoteCommand):

    """
    Easy to use SSH tunnels.

    The :class:`SecureTunnel` class combines :class:`RemoteCommand` with
    :class:`.EphemeralPortAllocator` and :class:`.WaitUntilConnected` to
    implement easy to use SSH tunnel support.

    The ``-L`` option of the SSH client program is used to open a tunnel
    between the local system and a remote system that persists until the
    command is terminated (tip: use a :keyword:`with` statement).

    Additionally the ``-N`` option is used to prevent the client from executing
    a remote command, this enables compatibility with "tunnel only" SSH
    accounts that have their shell set to something like ``/usr/sbin/nologin``.

    The :func:`start()` method waits for the tunnel to become available before
    returning control to the caller.
    """

    @mutable_property
    def async(self):
        """Whether to enable asynchronous command execution (a boolean, defaults to :data:`True`)."""
        return True

    @property
    def command_line(self):
        """
        The complete SSH client command to open the tunnel (a list of strings).

        This property overrides :attr:`RemoteCommand.command_line`
        to inject the command line options ``-L`` and ``-N``.
        """
        command_line = super(SecureTunnel, self).command_line
        command_line.append('-N')
        command_line.append('-L')
        command_line.append('%i:%s:%i' % (self.local_port, self.remote_host, self.remote_port))
        return command_line

    @mutable_property
    def compression(self):
        """Whether to enable compression (a boolean, defaults to :data:`True`)."""
        return True

    @mutable_property(cached=True)
    def local_port(self):
        """
        The port number on the side of the SSH client (an integer).

        When the value of :attr:`local_port` isn't specified a free
        ephemeral port number is automatically selected using
        :class:`~executor.tcp.EphemeralPortAllocator`.
        """
        allocator = EphemeralPortAllocator()
        return allocator.port_number

    @mutable_property
    def remote_host(self):
        """The remote host name to connect to (a string, defaults to 'localhost')."""
        return 'localhost'

    @required_property
    def remote_port(self):
        """The remote port number to connect to (an integer)."""

    @property
    def tty(self):
        """Override :attr:`~executor.ExternalCommand.tty` to :data:`False`."""
        return False

    def start(self, **options):
        """
        Start the SSH client and wait for the tunnel to become available.

        :param options: Any keyword arguments are passed to the
                        :func:`~executor.ExternalCommand.start()`
                        method of the superclass.
        :raises: Any exceptions raised by the following methods:

                 - :func:`executor.ExternalCommand.start()`
                 - :func:`executor.tcp.WaitUntilConnected.wait_until_connected()`
        """
        super(SecureTunnel, self).start(**options)
        WaitUntilConnected(
            port_number=self.local_port,
        ).wait_until_connected()


class RemoteConnectFailed(ExternalCommandFailed):

    """Raised by :class:`RemoteCommand` when an SSH connection itself fails (not the remote command)."""


class RemoteCommandFailed(ExternalCommandFailed):

    """Raised by :class:`RemoteCommand` when a remote command executed over SSH fails."""


class RemoteCommandNotFound(RemoteCommandFailed, CommandNotFound):

    """Raised by :class:`RemoteCommand` when a remote command returns :data:`.COMMAND_NOT_FOUND_STATUS`."""
