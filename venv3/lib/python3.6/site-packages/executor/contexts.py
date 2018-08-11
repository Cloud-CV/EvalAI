# Programmer friendly subprocess wrapper.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 20, 2018
# URL: https://executor.readthedocs.io

r"""
Dependency injection for command execution contexts.

The :mod:`~executor.contexts` module defines the :class:`LocalContext`,
:class:`RemoteContext` and :class:`SecureChangeRootContext` classes. All of
these classes support the same API for executing external commands, they are
simple wrappers for :class:`.ExternalCommand`, :class:`.RemoteCommand` and
:class:`.SecureChangeRootCommand`.

This allows you to script interaction with external commands in Python and
perform that interaction on your local system, on remote systems over SSH_ or
inside chroots_ using the exact same Python code. `Dependency injection`_ on
steroids anyone? :-)

Here's a simple example:

.. code-block:: python

   from executor.contexts import LocalContext, RemoteContext
   from humanfriendly import format_timespan

   def details_about_system(context):
       return "\n".join([
           "Information about %s:" % context,
           " - Host name: %s" % context.capture('hostname', '--fqdn'),
           " - Uptime: %s" % format_timespan(float(context.capture('cat', '/proc/uptime').split()[0])),
       ])

   print(details_about_system(LocalContext()))

   # Information about local system (peter-macbook):
   #  - Host name: peter-macbook
   #  - Uptime: 1 week, 3 days and 10 hours

   print(details_about_system(RemoteContext('file-server')))

   # Information about remote system (file-server):
   #  - Host name: file-server
   #  - Uptime: 18 weeks, 3 days and 4 hours

Whether this functionality looks exciting or horrible I'll leave up to your
judgment. I created it because I'm always building "tools that help me build
tools" and this functionality enables me to *very rapidly* prototype system
integration tools developed using Python:

**During development:**
 I *write* code on my workstation which I prefer because of the "rich editing
 environment" but I *run* the code against a remote system over SSH (a backup
 server, database server, hypervisor, mail server, etc.).

**In production:**
 I change one line of code to inject a :class:`LocalContext` object instead of
 a :class:`RemoteContext` object, I install the `executor` package and the code
 I wrote on the remote system and I'm done!

.. _SSH: https://en.wikipedia.org/wiki/Secure_Shell
.. _chroots: http://en.wikipedia.org/wiki/Chroot
.. _Dependency injection: http://en.wikipedia.org/wiki/Dependency_injection
"""

# Standard library modules.
import contextlib
import glob
import logging
import multiprocessing
import os
import random
import socket

# External dependencies.
from humanfriendly.text import dedent, split
from property_manager import (
    PropertyManager,
    lazy_property,
    mutable_property,
    required_property,
    writable_property,
)

# Modules included in our package.
from executor import DEFAULT_SHELL, ExternalCommand, quote
from executor.chroot import ChangeRootCommand
from executor.schroot import DEFAULT_NAMESPACE, SCHROOT_PROGRAM_NAME, SecureChangeRootCommand
from executor.ssh.client import RemoteAccount, RemoteCommand

# Initialize a logger.
logger = logging.getLogger(__name__)


def create_context(**options):
    """
    Create an execution context.

    :param options: Any keyword arguments are passed on to the context's initializer.
    :returns: A :class:`LocalContext`, :class:`SecureChangeRootContext` or
              :class:`RemoteContext` object.

    This function provides an easy to use shortcut for constructing context
    objects:

    - If the keyword argument ``chroot_name`` is given (and not :data:`None`)
      then a :class:`SecureChangeRootContext` object will be created.

    - If the keyword argument ``ssh_alias`` is given (and not :data:`None`)
      then a :class:`RemoteContext` object will be created.

    - Otherwise a :class:`LocalContext` object is created.
    """
    # Remove the `chroot_name' and `ssh_alias' keyword arguments from the
    # options dictionary to make sure these keyword arguments are only ever
    # passed to a constructor that supports them.
    chroot_name = options.pop('chroot_name', None)
    ssh_alias = options.pop('ssh_alias', None)
    if chroot_name is not None:
        return SecureChangeRootContext(chroot_name, **options)
    elif ssh_alias is not None:
        return RemoteContext(ssh_alias, **options)
    else:
        return LocalContext(**options)


class AbstractContext(PropertyManager):

    """Abstract base class for shared logic of all context classes."""

    def __init__(self, *args, **options):
        """
        Initialize an :class:`AbstractContext` object.

        :param args: Any positional arguments are passed on to the initializer
                     of the :class:`~property_manager.PropertyManager` class
                     (for future extensibility).
        :param options: The keyword arguments are handled as follows:

                        - Keyword arguments whose name matches a property of
                          the context object are used to set that property
                          (by passing them to the initializer of the
                          :class:`~property_manager.PropertyManager` class).

                        - Any other keyword arguments are collected into the
                          :attr:`options` dictionary.
        """
        # Separate the command and context options.
        context_opts = {}
        command_opts = options.pop('options', {})
        for name, value in options.items():
            if self.have_property(name):
                context_opts[name] = value
            else:
                command_opts[name] = value
        # Embed the command options in the context options.
        context_opts['options'] = command_opts
        # Initialize the superclass.
        super(AbstractContext, self).__init__(*args, **context_opts)
        # Initialize instance variables.
        self.undo_stack = []

    @required_property
    def command_type(self):
        """The type of command objects created by this context (:class:`.ExternalCommand` or a subclass)."""

    @property
    def cpu_count(self):
        """
        The number of CPUs in the system (an integer).

        .. note:: This is an abstract property that must be implemented by subclasses.
        """
        raise NotImplementedError()

    @lazy_property
    def distribution_codename(self):
        """
        The code name of the system's distribution (a lowercased string like ``precise`` or ``trusty``).

        This is the lowercased output of ``lsb_release --short --codename``.
        """
        return self.capture('lsb_release', '--short', '--codename', check=False, silent=True).lower()

    @lazy_property
    def distributor_id(self):
        """
        The distributor ID of the system (a lowercased string like ``debian`` or ``ubuntu``).

        This is the lowercased output of ``lsb_release --short --id``.
        """
        return self.capture('lsb_release', '--short', '--id', check=False, silent=True).lower()

    @lazy_property
    def have_ionice(self):
        """:data:`True` when ionice_ is installed, :data:`False` otherwise."""
        return bool(self.find_program('ionice'))

    @property
    def have_superuser_privileges(self):
        """:data:`True` if the context has superuser privileges, :data:`False` otherwise."""
        prototype = self.prepare('true')
        return prototype.have_superuser_privileges or prototype.sudo

    @writable_property
    def options(self):
        """The options that are passed to commands created by the context (a dictionary)."""

    @mutable_property
    def parent(self):
        """
        The parent context (a context object or :data:`None`).

        The :attr:`parent` property (and the code in :func:`prepare_command()`
        that uses the :attr:`parent` property) enables the use of "nested
        contexts".

        For example :func:`find_chroots()` creates :class:`SecureChangeRootContext`
        objects whose :attr:`parent` is set to the context that found the
        chroots. Because of this the :class:`SecureChangeRootContext` objects can be
        used to create commands without knowing or caring whether the chroots
        reside on the local system or on a remote system accessed via SSH.

        .. warning:: Support for parent contexts was introduced in `executor`
                     version 15 and for now this feature is considered
                     experimental and subject to change. While I'm definitely
                     convinced of the usefulness of nested contexts I'm not
                     happy with the current implementation at all. The most
                     important reason for this is that it's *very surprising*
                     (and not in a good way) that a context with a
                     :attr:`parent` will create commands with the parent's
                     :attr:`command_type` instead of the expected type.
        """

    def __enter__(self):
        """Initialize a new "undo stack" (refer to :func:`cleanup()`)."""
        self.undo_stack.append([])
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Execute any commands on the "undo stack" (refer to :func:`cleanup()`)."""
        old_scope = self.undo_stack.pop()
        while old_scope:
            args, kw = old_scope.pop()
            if args and callable(args[0]):
                args = list(args)
                function = args.pop(0)
                function(*args, **kw)
            else:
                self.execute(*args, **kw)

    @contextlib.contextmanager
    def atomic_write(self, filename):
        """
        Create or update the contents of a file atomically.

        :param filename: The pathname of the file to create/update (a string).
        :returns: A context manager (see the :keyword:`with` keyword) that
                  returns a single string which is the pathname of the
                  temporary file where the contents should be written to
                  initially.

        If an exception is raised from the :keyword:`with` block and the
        temporary file exists, an attempt will be made to remove it but failure
        to do so will be silenced instead of propagated (to avoid obscuring the
        original exception).

        The temporary file is created in the same directory as the real file,
        but a dot is prefixed to the name (making it a hidden file) and the
        suffix '.tmp-' followed by a random integer number is used.
        """
        directory, entry = os.path.split(filename)
        temporary_file = os.path.join(directory, '.%s.tmp-%i' % (entry, random.randint(1, 100000)))
        try:
            yield temporary_file
        except Exception:
            self.execute('rm', '-f', temporary_file, check=False)
        else:
            self.execute('mv', temporary_file, filename)

    def capture(self, *command, **options):
        """
        Execute an external command in the current context and capture its output.

        :param command: All positional arguments are passed on to the
                        initializer of the :attr:`command_type` class.
        :param options: All keyword arguments are passed on to the
                        initializer of the :attr:`command_type` class.
        :returns: The value of :attr:`.ExternalCommand.output`.
        """
        options['capture'] = True
        cmd = self.prepare_command(command, options)
        cmd.start()
        return cmd.output

    def cleanup(self, *args, **kw):
        """
        Register an action to be performed before the context ends.

        :param args: The external command to execute or callable to invoke.
        :param kw: Options to the command or keyword arguments to the callable.
        :raises: :exc:`~exceptions.ValueError` when :func:`cleanup()` is called
                 outside a :keyword:`with` statement.

        This method registers *the intent* to perform an action just before the
        context ends. To actually perform the action(s) you need to use (the
        subclass of) the :class:`AbstractContext` object as a context manager
        using the :keyword:`with` statement.

        The last action that is registered is the first one to be
        performed. This gives the equivalent functionality of a
        deeply nested :keyword:`try` / :keyword:`finally` structure
        without actually having to write such ugly code :-).

        The handling of arguments in :func:`cleanup()` depends on the type of
        the first positional argument:

        - If the first positional argument is a string, the positional
          arguments and keyword arguments are passed on to the initializer
          of the :attr:`command_type` class to execute an external command
          just before the context ends.

        - If the first positional argument is a callable, it is called with any
          remaining positional arguments and keyword arguments before the
          context ends.

        .. warning:: If a cleanup command fails and raises an exception no
                     further cleanup commands are executed. If you don't care
                     if a specific cleanup command reports an error, set its
                     :attr:`~.ExternalCommand.check` property to
                     :data:`False`.
        """
        if not self.undo_stack:
            raise ValueError("Cleanup stack can only be used inside with statements!")
        self.undo_stack[-1].append((args, kw))

    def execute(self, *command, **options):
        """
        Execute an external command in the current context.

        :param command: All positional arguments are passed on to the
                        initializer of the :attr:`command_type` class.
        :param options: All keyword arguments are passed on to the
                        initializer of the :attr:`command_type` class.
        :returns: The :attr:`command_type` object.

        .. note:: After constructing a :attr:`command_type` object this method
                  calls :func:`~executor.ExternalCommand.start()` on the
                  command before returning it to the caller, so by the time the
                  caller gets the command object a synchronous command will
                  have already ended. Asynchronous commands don't have this
                  limitation of course.
        """
        cmd = self.prepare_command(command, options)
        cmd.start()
        return cmd

    def exists(self, pathname):
        """
        Check whether the given pathname exists.

        :param pathname: The pathname to check (a string).
        :returns: :data:`True` if the pathname exists,
                  :data:`False` otherwise.

        This is a shortcut for the ``test -e ...`` command.
        """
        return self.test('test', '-e', pathname)

    def find_chroots(self, namespace=DEFAULT_NAMESPACE):
        """
        Find the chroots available in the current context.

        :param namespace: The chroot namespace to look for (a string, defaults
                          to :data:`~executor.schroot.DEFAULT_NAMESPACE`).
                          Refer to the schroot_ documentation for more
                          information about chroot namespaces.
        :returns: A generator of :class:`SecureChangeRootContext` objects whose
                  :attr:`~AbstractContext.parent` is set to the context where
                  the chroots were found.
        :raises: :exc:`~executor.ExternalCommandFailed` (or a subclass) when
                 the ``schroot`` program isn't installed or the ``schroot
                 --list`` command fails.
        """
        for entry in self.capture(SCHROOT_PROGRAM_NAME, '--list').splitlines():
            entry_ns, _, entry_name = entry.rpartition(':')
            if not entry_ns:
                entry_ns = DEFAULT_NAMESPACE
            if entry_ns == namespace:
                short_name = entry_name if entry_ns == DEFAULT_NAMESPACE else entry
                yield SecureChangeRootContext(chroot_name=short_name, parent=self)

    def find_program(self, program_name, *args):
        """
        Find the absolute pathname(s) of one or more programs.

        :param program_name: Each of the positional arguments is expected to
                             be a string containing the name of a program to
                             search for in the ``$PATH``. At least one is
                             required.
        :returns: A list of strings with absolute pathnames.

        This method is a simple wrapper around ``which``.
        """
        return self.capture('which', program_name, *args, check=False).splitlines()

    def get_options(self):
        """
        Get the options that are passed to commands created by the context.

        :returns: A dictionary of command options.

        By default this method simply returns the :attr:`options` dictionary,
        however the purpose of :func:`get_options()` is to enable subclasses to
        customize the options passed to commands on the fly.
        """
        return self.options

    def glob(self, pattern):
        """
        Find matches for a given filename pattern.

        :param pattern: A filename pattern (a string).
        :returns: A list of strings with matches.

        Some implementation notes:

        - This method *emulates* filename globbing as supported by system
          shells like Bash and ZSH. It works by forking a Python interpreter
          and using that to call the :func:`glob.glob()` function. This
          approach is of course rather heavyweight.

        - Initially this method used Bash for filename matching (similar to
          `this StackOverflow answer <https://unix.stackexchange.com/a/34012/44309>`_)
          but I found it impossible to make this work well for patterns
          containing whitespace.

        - I took the whitespace issue as a sign that I was heading down the
          wrong path (trying to add robustness to a fragile solution) and so
          the new implementation was born (which prioritizes robustness over
          performance).
        """
        listing = self.capture(
            'python',
            input=dedent(
                r'''
                import glob
                matches = glob.glob({pattern})
                print('\x00'.join(matches))
                ''',
                pattern=repr(pattern),
            ),
        )
        return split(listing, '\x00')

    def is_directory(self, pathname):
        """
        Check whether the given pathname points to an existing directory.

        :param pathname: The pathname to check (a string).
        :returns: :data:`True` if the pathname points to an existing directory,
                  :data:`False` otherwise.

        This is a shortcut for the ``test -d ...`` command.
        """
        return self.test('test', '-d', pathname)

    def is_executable(self, pathname):
        """
        Check whether the given pathname points to an executable file.

        :param pathname: The pathname to check (a string).
        :returns: :data:`True` if the pathname points to an executable file,
                  :data:`False` otherwise.

        This is a shortcut for the ``test -x ...`` command.
        """
        return self.test('test', '-x', pathname)

    def is_file(self, pathname):
        """
        Check whether the given pathname points to an existing file.

        :param pathname: The pathname to check (a string).
        :returns: :data:`True` if the pathname points to an existing file,
                  :data:`False` otherwise.

        This is a shortcut for the ``test -f ...`` command.
        """
        return self.test('test', '-f', pathname)

    def is_readable(self, pathname):
        """
        Check whether the given pathname exists and is readable.

        :param pathname: The pathname to check (a string).
        :returns: :data:`True` if the pathname exists and is readable,
                  :data:`False` otherwise.

        This is a shortcut for the ``test -r ...`` command.
        """
        return self.test('test', '-r', pathname)

    def is_writable(self, pathname):
        """
        Check whether the given pathname exists and is writable.

        :param pathname: The pathname to check (a string).
        :returns: :data:`True` if the pathname exists and is writable,
                  :data:`False` otherwise.

        This is a shortcut for the ``test -w ...`` command.
        """
        return self.test('test', '-w', pathname)

    def list_entries(self, directory):
        """
        List the entries in a directory.

        :param directory: The pathname of the directory (a string).
        :returns: A list of strings with the names of the directory entries.

        This method uses ``find -mindepth 1 -maxdepth 1 -print0`` to list
        directory entries instead of going for the more obvious choice ``ls
        -A1`` because ``find`` enables more reliable parsing of command output
        (with regards to whitespace).
        """
        listing = self.capture('find', directory, '-mindepth', '1', '-maxdepth', '1', '-print0')
        return [os.path.basename(fn) for fn in listing.split('\0') if fn]

    def merge_options(self, overrides):
        """
        Merge default options and overrides into a single dictionary.

        :param overrides: A dictionary with any keyword arguments given to
                          :func:`execute()` or :func:`start_interactive_shell()`.
        :returns: The dictionary with overrides, but any keyword arguments
                  given to the initializer of :class:`AbstractContext` that are
                  not set in the overrides are set to the value of the
                  initializer argument.

        The :attr:`~executor.ExternalCommand.ionice` option is automatically
        unset when :attr:`have_ionice` is :data:`False`, regardless of whether
        the option was set from defaults or overrides.
        """
        defaults = self.get_options()
        for name, value in defaults.items():
            overrides.setdefault(name, value)
        if overrides.get('ionice') and not self.have_ionice:
            logger.debug("Ignoring `ionice' option because required program isn't installed.")
            overrides.pop('ionice')
        return overrides

    def prepare(self, *command, **options):
        """
        Prepare to execute an external command in the current context.

        :param command: All positional arguments are passed on to the
                        initializer of the :attr:`command_type` class.
        :param options: All keyword arguments are passed on to the
                        initializer of the :attr:`command_type` class.
        :returns: The :attr:`command_type` object.

        .. note:: After constructing a :attr:`command_type` object this method
                  doesn't call :func:`~executor.ExternalCommand.start()` which
                  means you control if and when the command is started. This
                  can be useful to prepare a large batch of commands and
                  execute them concurrently using a :class:`.CommandPool`.
        """
        return self.prepare_command(command, options)

    def prepare_command(self, command, options):
        """
        Create a :attr:`command_type` object based on :attr:`options`.

        :param command: A tuple of strings (the positional arguments to the
                        initializer of the :attr:`command_type` class).
        :param options: A dictionary (the keyword arguments to the initializer
                        of the :attr:`command_type` class).
        :returns: A :attr:`command_type` object *that hasn't been started yet*.
        """
        # Prepare our command.
        options = self.merge_options(options)
        cmd = self.command_type(*command, **options)
        # Prepare the command of the parent context?
        if self.parent:
            # Figure out if any of our command options are unknown to the
            # parent context because we need to avoid passing any of these
            # options to the parent's prepare_command() method.
            nested_opts = set(dir(self.command_type))
            parent_opts = set(dir(self.parent.command_type))
            for name in nested_opts - parent_opts:
                if options.pop(name, None) is not None:
                    logger.debug("Swallowing %r option! (parent context won't understand)", name)
            # Prepare the command of the parent context.
            cmd = self.parent.prepare_command(cmd.command_line, options)
        return cmd

    def prepare_interactive_shell(self, options):
        """
        Create a :attr:`command_type` object that starts an interactive shell.

        :param options: A dictionary (the keyword arguments to the initializer
                        of the :attr:`command_type` class).
        :returns: A :attr:`command_type` object *that hasn't been started yet*.
        """
        options = self.merge_options(options)
        options.update(shell=False, tty=True)
        return self.prepare(DEFAULT_SHELL, **options)

    def read_file(self, filename):
        """
        Read the contents of a file.

        :param filename: The pathname of the file to read (a string).
        :returns: The contents of the file (a byte string).

        This method uses cat_ to read the contents of files so that options
        like :attr:`~.ExternalCommand.sudo` are respected (regardless of
        whether we're dealing with a :class:`LocalContext` or
        :class:`RemoteContext`).

        .. _cat: http://linux.die.net/man/1/cat
        """
        return self.execute('cat', filename, capture=True).stdout

    def start_interactive_shell(self, **options):
        """
        Start an interactive shell in the current context.

        :param options: All keyword arguments are passed on to the
                        initializer of the :attr:`command_type` class.
        :returns: The :attr:`command_type` object.

        .. note:: After constructing a :attr:`command_type` object this method
                  calls :func:`~executor.ExternalCommand.start()` on the
                  command before returning it to the caller, so by the time the
                  caller gets the command object a synchronous command will
                  have already ended. Asynchronous commands don't have this
                  limitation of course.
        """
        cmd = self.prepare_interactive_shell(options)
        cmd.start()
        return cmd

    def test(self, *command, **options):
        """
        Execute an external command in the current context and get its status.

        :param command: All positional arguments are passed on to the
                        initializer of the :attr:`command_type` class.
        :param options: All keyword arguments are passed on to the
                        initializer of the :attr:`command_type` class.
        :returns: The value of :attr:`.ExternalCommand.succeeded`.

        This method automatically sets :attr:`~.ExternalCommand.check` to
        :data:`False` and :attr:`~.ExternalCommand.silent` to :data:`True`.
        """
        options.update(check=False, silent=True)
        cmd = self.prepare_command(command, options)
        cmd.start()
        return cmd.succeeded

    def write_file(self, filename, contents):
        """
        Change the contents of a file.

        :param filename: The pathname of the file to write (a string).
        :param contents: The contents to write to the file (a byte string).

        This method uses a combination of cat_ and `output redirection`_ to
        change the contents of files so that options like
        :attr:`~.ExternalCommand.sudo` are respected (regardless of whether
        we're dealing with a :class:`LocalContext` or :class:`RemoteContext`).
        Due to the use of cat_ this method will create files that don't exist
        yet, assuming the directory containing the file already exists and the
        context provides permission to write to the directory.

        .. _output redirection: https://en.wikipedia.org/wiki/Redirection_(computing)
        """
        return self.execute('cat > %s' % quote(filename), shell=True, input=contents)


class LocalContext(AbstractContext):

    """Context for executing commands on the local system."""

    @property
    def command_type(self):
        """The type of command objects created by this context (:class:`.ExternalCommand`)."""
        return ExternalCommand

    @lazy_property
    def cpu_count(self):
        """
        The number of CPUs in the system (an integer).

        This property's value is computed using :func:`multiprocessing.cpu_count()`.
        """
        return multiprocessing.cpu_count()

    def glob(self, pattern):
        """
        Find matches for a given filename pattern.

        :param pattern: A filename pattern (a string).
        :returns: A list of strings with matches.

        This method overrides :func:`AbstractContext.glob()` to call
        :func:`glob.glob()` directly instead of forking a new Python
        interpreter.

        This optimization is skipped when :attr:`~AbstractContext.options`
        contains :attr:`~executor.ExternalCommand.sudo`,
        :attr:`~executor.ExternalCommand.uid` or
        :attr:`~executor.ExternalCommand.user` to avoid reporting wrong matches
        due to insufficient filesystem permissions.
        """
        if any(map(self.options.get, ('sudo', 'uid', 'user'))):
            return super(LocalContext, self).glob(pattern)
        else:
            return glob.glob(pattern)

    def __str__(self):
        """Render a human friendly string representation of the context."""
        return "local system (%s)" % socket.gethostname()


class ChangeRootContext(AbstractContext):

    """Context for executing commands in change roots using chroot_."""

    def __init__(self, *args, **options):
        """
        Initialize a :class:`ChangeRootContext` object.

        :param args: Positional arguments are passed on to the initializer of
                     the :class:`AbstractContext` class (for future
                     extensibility).
        :param options: Any keyword arguments are passed on to the initializer
                        of the :class:`AbstractContext` class.

        If the keyword argument `chroot` isn't given but positional arguments
        are provided, the first positional argument is used to set the
        :attr:`chroot` property.
        """
        # Enable modification of the positional arguments.
        args = list(args)
        # We allow `chroot_name' to be passed as a keyword argument but use the
        # first positional argument when the keyword argument isn't given.
        if options.get('chroot') is None and args:
            options['chroot'] = args.pop(0)
        # Initialize the superclass.
        super(ChangeRootContext, self).__init__(*args, **options)

    @required_property
    def chroot(self):
        """The pathname of the root directory of the chroot (a string)."""

    @property
    def command_type(self):
        """The type of command objects created by this context (:class:`.ChangeRootCommand`)."""
        return ChangeRootCommand

    @lazy_property
    def cpu_count(self):
        """
        The number of CPUs in the system (an integer).

        This property's value is computed using :func:`multiprocessing.cpu_count()`.
        """
        return multiprocessing.cpu_count()

    def get_options(self):
        """The :attr:`~AbstractContext.options` including :attr:`chroot`."""
        options = dict(self.options)
        options.update(chroot=self.chroot)
        return options

    def __str__(self):
        """Render a human friendly string representation of the context."""
        return "chroot (%s)" % self.chroot


class SecureChangeRootContext(AbstractContext):

    """Context for executing commands in change roots using schroot_."""

    def __init__(self, *args, **options):
        """
        Initialize a :class:`SecureChangeRootContext` object.

        :param args: Positional arguments are passed on to the initializer of
                     the :class:`AbstractContext` class (for future
                     extensibility).
        :param options: Any keyword arguments are passed on to the initializer
                        of the :class:`AbstractContext` class.

        If the keyword argument `chroot_name` isn't given but positional
        arguments are provided, the first positional argument is used to set
        the :attr:`chroot_name` property.
        """
        # Enable modification of the positional arguments.
        args = list(args)
        # We allow `chroot_name' to be passed as a keyword argument but use the
        # first positional argument when the keyword argument isn't given.
        if options.get('chroot_name') is None and args:
            options['chroot_name'] = args.pop(0)
        # Initialize the superclass.
        super(SecureChangeRootContext, self).__init__(*args, **options)

    @required_property
    def chroot_name(self):
        """The name of a chroot managed by schroot_ (a string)."""

    @property
    def command_type(self):
        """The type of command objects created by this context (:class:`.SecureChangeRootCommand`)."""
        return SecureChangeRootCommand

    @lazy_property
    def cpu_count(self):
        """
        The number of CPUs in the system (an integer).

        This property's value is computed using :func:`multiprocessing.cpu_count()`.
        """
        return multiprocessing.cpu_count()

    def get_options(self):
        """The :attr:`~AbstractContext.options` including :attr:`chroot_name`."""
        options = dict(self.options)
        options.update(chroot_name=self.chroot_name)
        return options

    def __str__(self):
        """Render a human friendly string representation of the context."""
        return "secure chroot (%s)" % self.chroot_name


class RemoteContext(RemoteAccount, AbstractContext):

    """Context for executing commands on a remote system over SSH."""

    @property
    def command_type(self):
        """The type of command objects created by this context (:class:`.RemoteCommand`)."""
        return RemoteCommand

    @lazy_property
    def cpu_count(self):
        """
        The number of CPUs in the system (an integer).

        This property's value is computed by executing the remote command
        nproc_. If that command fails :attr:`cpu_count` falls back to the
        command ``grep -ci '^processor\s*:' /proc/cpuinfo``.

        .. _nproc: http://linux.die.net/man/1/nproc
        """
        try:
            return int(self.capture('nproc', shell=False, silent=True))
        except Exception:
            return int(self.capture('grep', '-ci', '^processor\s*:', '/proc/cpuinfo'))

    def get_options(self):
        """The :attr:`~AbstractContext.options` including the SSH alias and remote user."""
        options = dict(self.options)
        options.update(ssh_alias=self.ssh_alias, ssh_user=self.ssh_user)
        return options

    def __str__(self):
        """Render a human friendly string representation of the context."""
        return "remote system (%s)" % self.ssh_alias
