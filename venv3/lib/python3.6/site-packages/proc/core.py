# proc: Simple interface to Linux process information.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: June 13, 2016
# URL: https://proc.readthedocs.io

"""
The :mod:`proc.core` module contains the core functionality of the `proc` package.

This module provides a simple interface to the process information available in
``/proc``. It takes care of the text parsing that's necessary to gather process
information from ``/proc`` but it doesn't do much more than that. The functions
in this module produce :class:`Process` objects.

If you're just getting started with this module I suggest you jump to the
documentation of :func:`find_processes()` because this function provides the
"top level entry point" into most of the functionality provided by this
module.
"""

# Standard library modules.
import collections
import errno
import grp
import logging
import os
import pwd
import time

# External dependencies.
from executor import which
from proc.unix import UnixProcess
from property_manager import lazy_property

# Initialize a logger.
logger = logging.getLogger(__name__)

# Global counters to track the number of detected race conditions. This is only
# useful for the test suite, because I want the test suite to create race
# conditions and verify that they are properly handled.
num_race_conditions = dict(cmdline=0, environ=0, exe=0, stat=0, status=0)


class Process(UnixProcess):

    """
    Process information based on ``/proc/[pid]/stat`` and similar files.

    :class:`Process` objects are constructed using
    :func:`find_processes()` and :func:`Process.from_path()`. You
    shouldn't be using the :class:`Process` constructor directly unless you
    know what you're doing.

    The :class:`Process` class extends :class:`~proc.unix.UnixProcess` which means
    all of the process manipulation supported by :class:`~proc.unix.UnixProcess`
    is also supported by :class:`Process` objects.

    **Comparison to official /proc documentation**

    Quite a few of the instance properties of this class are based on (and
    named after) fields extracted from ``/proc/[pid]/stat``. The following
    table lists these properties and the *zero based index* of the
    corresponding field in ``/proc/[pid]/stat``:

    ====================  =====
    Property              Index
    ====================  =====
    :attr:`pid`            0
    :attr:`comm`           1
    :attr:`state`          2
    :attr:`ppid`           3
    :attr:`pgrp`           4
    :attr:`session`        5
    :attr:`starttime`     21
    :attr:`vsize`         22
    :attr:`rss`           23
    ====================  =====

    As you can see from the indexes in the table above quite a few fields from
    ``/proc/[pid]/stat`` are not currently exposed by :class:`Process`
    objects. In fact ``/proc/[pid]/stat`` contains 44 fields! Some of these
    fields are no longer maintained by the Linux kernel and remain only for
    backwards compatibility (so exposing them is not useful) while other fields
    are not exposed because I didn't consider them relevant to a Python API. If
    your use case requires fields that are not yet exposed, feel free to
    suggest additional fields to expose in the issue tracker.

    The documentation on the properties of this class quotes from and
    paraphrases the text in `man 5 proc`_ so if things are unclear and you're
    feeling up to it, dive into the huge manual page for clarifications :-).

    .. _man 5 proc: http://linux.die.net/man/5/proc
    """

    @classmethod
    def from_path(cls, directory):
        """
        Construct a process information object from a numerical subdirectory of ``/proc``.

        :param directory: The absolute pathname of the numerical subdirectory
                          of ``/proc`` to get process information from (a
                          string).
        :returns: A process information object or ``None`` (in case the process
                  ends before its information can be read).

        This class method is used by :func:`find_processes()` to construct
        :class:`Process` objects. It's exposed as a separate method because
        it may sometimes be useful to call directly. For example:

        >>> from proc.core import Process
        >>> Process.from_path('/proc/self')
        Process(pid=1468,
                comm='python',
                state='R',
                ppid=21982,
                pgrp=1468,
                session=21982,
                vsize=40431616,
                rss=8212480,
                cmdline=['python'],
                exe='/home/peter/.virtualenvs/proc/bin/python')
        """
        fields = parse_process_status(directory)
        if fields:
            return cls(directory, fields)

    @classmethod
    def from_pid(cls, pid):
        """
        Construct a process information object based on a process ID.

        :param pid: The process ID (an integer).
        :returns: A process information object or ``None`` (in case the process
                  ends before its information can be read).
        """
        return cls.from_path(os.path.join('/proc', str(pid)))

    def __init__(self, proc_tree, stat_fields):
        """
        Initialize a :class:`Process` object.

        :param proc_tree: The absolute pathname of the numerical subdirectory
                          of ``/proc`` on which the process information is
                          based (a string).
        :param stat_fields: The tokenized fields from ``/proc/[pid]/stat`` (a
                            list of strings).
        """
        # Initialize the superclass.
        super(Process, self).__init__()
        # Initialize instance variables.
        self.proc_tree = proc_tree
        self.stat_fields = stat_fields
        # Define aliases for two previously renamed methods.
        self.cont = self.resume
        self.stop = self.suspend

    def __repr__(self):
        """
        Create a human readable representation of a process information object.

        :returns: A string containing what looks like a :class:`Process`
                  constructor, but showing public properties instead of
                  internal properties.
        """
        fields = []
        for name, optional in (('pid', False),
                               ('comm', False),
                               ('state', False),
                               ('ppid', True),
                               ('pgrp', False),
                               ('session', False),
                               ('starttime', False),
                               ('vsize', False),
                               ('rss', False),
                               ('cmdline', True),
                               ('exe', True),
                               ('exe_path', True),
                               ('exe_name', False)):
            value = getattr(self, name)
            if not (optional and not value):
                fields.append("%s=%r" % (name, value))
        return "%s(%s)" % (self.__class__.__name__, ", ".join(fields))

    @lazy_property
    def cmdline(self):
        """
        The complete command line for the process (a list of strings).

        **Availability:**

        - This property is parsed from the contents of ``/proc/[pid]/cmdline``
          the first time it is referenced, after that its value is cached so it
          will always be available (although by then it may no longer be up to
          date because processes can change their command line at runtime on
          Linux).

        - If this property is first referenced after the process turns into a
          zombie_ or the process ends then it's too late to read the contents
          of ``/proc/[pid]/cmdline`` and an empty list is returned.

        .. note:: In Linux it is possible for a process to change its command
                  line after it has started. Modern daemons tend to do this in
                  order to communicate their status. Here's an example of how
                  the Nginx web server uses this feature:

                  >>> from proc.core import find_processes
                  >>> from pprint import pprint
                  >>> pprint([(p.pid, p.cmdline) for p in find_processes() if p.comm == 'nginx'])
                  [(2662, ['nginx: master process /usr/sbin/nginx']),
                   (25100, ['nginx: worker process']),
                   (25101, ['nginx: worker process']),
                   (25102, ['nginx: worker process']),
                   (25103, ['nginx: worker process'])]

                  What this means is that (depending on the behavior of the
                  process in question) it may be impossible to determine the
                  effective command line that was used to start a process. If
                  you're just interested in the pathname of the executable
                  consider using the :attr:`exe` property instead:

                  >>> from proc.core import find_processes
                  >>> from pprint import pprint
                  >>> pprint([(p.pid, p.exe) for p in find_processes() if p.comm == 'nginx'])
                  [(2662, '/usr/sbin/nginx'),
                   (25100, '/usr/sbin/nginx'),
                   (25101, '/usr/sbin/nginx'),
                   (25102, '/usr/sbin/nginx'),
                   (25103, '/usr/sbin/nginx')]
        """
        return parse_process_cmdline(self.proc_tree)

    @lazy_property
    def comm(self):
        """
        The filename of the executable.

        **Availability:** This property is parsed from the contents of
        ``/proc/[pid]/stat`` and is always available.

        The filename is not enclosed in parentheses like it is in
        ``/proc/[pid]/stat`` because the parentheses are an implementation
        detail of the encoding of ``/proc/[pid]/stat`` and the whole point of
        :mod:`proc.core` is to hide ugly encoding details like this :-).

        .. note:: This field can be truncated by the Linux kernel so strictly
                  speaking you can't rely on this field unless you know that
                  the executables you're interested in have short names. Here's
                  an example of what I'm talking about:

                  >>> from proc.core import find_processes
                  >>> next(p for p in find_processes() if p.comm.startswith('console'))
                  Process(pid=2753,
                          comm='console-kit-dae',
                          state='S',
                          ppid=1,
                          pgrp=1632,
                          session=1632,
                          vsize=2144198656,
                          rss=733184,
                          cmdline=['/usr/sbin/console-kit-daemon', '--no-daemon'])

                  As you can see in the example above the executable name
                  ``console-kit-daemon`` is truncated to ``console-kit-dae``.
                  If you need a reliable way to find the executable name
                  consider using the :attr:`cmdline` and/or :attr:`exe`
                  properties.
        """
        return self.stat_fields[1]

    @property
    def command_line(self):
        """
        An alias for the :attr:`cmdline` property.

        This alias exists so that :class:`~executor.process.ControllableProcess`
        can log process ids and command lines (this helps to make the log
        output more human friendly).
        """
        return self.cmdline

    @lazy_property
    def environ(self):
        """
        The environment of the process (a dictionary with string key/value pairs).

        **Availability:**

        - This property is parsed from the contents of ``/proc/[pid]/environ``
          the first time it is referenced, after that its value is cached so it
          will always be available.

        - If this property is first referenced after the process turns into a
          zombie_ or the process ends then it's too late to read the contents
          of ``/proc/[pid]/environ`` and an empty dictionary is returned.
        """
        variables = {}
        with ProtectedAccess('environ', "read process environment"):
            with open(os.path.join(self.proc_tree, 'environ')) as handle:
                contents = handle.read()
            if contents:
                for token in contents.split('\0'):
                    name, _, value = token.partition('=')
                    if name:
                        variables[name] = value
        return variables

    @lazy_property
    def exe(self):
        """
        The actual pathname of the executed command (a string).

        **Availability:**

        - This property is constructed by dereferencing the symbolic link
          ``/proc/[pid]/exe`` the first time the property is referenced, after
          that its value is cached so it will always be available.

        - If this property is referenced after the process has ended then it's
          too late to dereference the symbolic link and an empty string is
          returned.

        - If an exception is encountered while dereferencing the symbolic link
          (for example because you don't have permission to dereference the
          symbolic link) the exception is swallowed and an empty string is
          returned.
        """
        with ProtectedAccess('exe', "dereference executable path"):
            return os.readlink(os.path.join(self.proc_tree, 'exe'))
        return ''

    @lazy_property
    def exe_name(self):
        """
        The base name of the executable (a string).

        It can be tricky to reliably determine the name of the executable of an
        arbitrary process and this property tries to make it easier. Its value
        is based on the first of the following methods that works:

        1. If :attr:`exe_path` is available then the base name of this
           pathname is returned.

           - Pro: When the :attr:`exe_path` property is available it is
             fairly reliable.
           - Con: The :attr:`exe_path` property can be unavailable (refer to
             its documentation for details).

        2. If the first string in :attr:`cmdline` contains a name that is
           available on the executable search path (``$PATH``) then this name
           is returned.

           - Pro: As long as :attr:`cmdline` contains the name of an
             executable available on the ``$PATH`` this method works.
           - Con: This method can fail because a process has changed its own
             command line (after it was started).

        3. If both of the methods above fail :attr:`comm` is returned.

           - Pro: The :attr:`comm` field is always available.
           - Con: The :attr:`comm` field may be truncated.
        """
        if self.exe_path:
            return os.path.basename(self.exe_path)
        if self.cmdline:
            name = self.cmdline[0]
            if os.path.basename(name) == name and which(name):
                return name
        return self.comm

    @lazy_property
    def exe_path(self):
        """
        The absolute pathname of the executable (a string).

        It can be tricky to reliably determine the pathname of the executable
        of an arbitrary process and this property tries to make it easier. Its
        value is based on the first of the following methods that works:

        1. If :attr:`exe` is available then this pathname is returned.

           - Pro: This method provides the most reliable way to determine the
             absolute pathname of the executed command because (as far as I
             know) it always provides an absolute pathname.
           - Con: This method can fail because you don't have permission to
             dereference the ``/proc/[pid]/exe`` symbolic link.

        2. If the first string in :attr:`cmdline` contains the absolute
           pathname of an executable file then this pathname is returned.

           - Pro: This method doesn't require the same permissions that method
             one requires.
           - Con: This method can fail because a process has changed its own
             command line (after it was started) or because the first string in
             the command line isn't an absolute pathname.

        3. If both of the methods above fail an empty string is returned.
        """
        if self.exe:
            return self.exe
        if self.cmdline:
            name = self.cmdline[0]
            if os.path.isabs(name) and os.access(name, os.X_OK):
                return name
        return ''

    @lazy_property
    def group(self):
        """
        The name of the real group ID (a string).

        **Availability:** Refer to :attr:`group_ids`. :data:`None` is returned
        if :attr:`group_ids` is unavailable or :func:`gid_to_name()` fails.
        """
        return gid_to_name(self.group_ids.real) if self.group_ids else None

    @lazy_property
    def group_ids(self):
        """
        The real, effective, saved set, and filesystem GIDs of the process (an :class:`OwnerIDs` object).

        **Availability:** Refer to :attr:`status_fields`. :data:`None` is
        returned if :attr:`status_fields` is unavailable.
        """
        return self._parse_ids('Gid')

    @property
    def is_alive(self):
        """
        :data:`True` if the process is still alive, :data:`False` otherwise.

        This property reads the ``/proc/[pid]/stat`` file each time the
        property is referenced to make sure that the process still exists and
        has not turned into a zombie_ process.

        See also :func:`~proc.unix.UnixProcess.suspend()`,
        :func:`~proc.unix.UnixProcess.resume()`,
        :func:`~executor.process.ControllableProcess.terminate()` and
        :func:`~executor.process.ControllableProcess.kill()`.
        """
        stat_fields = parse_process_status(self.proc_tree, silent=True)
        return bool(stat_fields and stat_fields[2] != 'Z')

    @property
    def is_running(self):
        """
        An alias for :attr:`is_alive`.

        This alias makes :class:`~proc.unix.UnixProcess` objects aware of
        zombie_ processes so that e.g. killing of a zombie process doesn't hang
        indefinitely (waiting for a zombie that will never die).
        """
        return self.is_alive

    @lazy_property
    def pgrp(self):
        """
        The process group ID of the process (an integer).

        **Availability:** This property is parsed from the contents of
        ``/proc/[pid]/stat`` and is always available.
        """
        return int(self.stat_fields[4])

    @lazy_property
    def pid(self):
        """
        The process ID (an integer).

        **Availability:** This property is parsed from the contents of
        ``/proc/[pid]/stat`` and is always available.
        """
        return int(self.stat_fields[0])

    @lazy_property
    def ppid(self):
        """
        The process ID of the parent process (an integer).

        **Availability:** This property is parsed from the contents of
        ``/proc/[pid]/stat`` and is always available.

        This field is zero when the process doesn't have a parent process (same
        as in ``/proc/[pid]/stat``). Because Python treats the integer 0 as
        :data:`False` this field can be used as follows to find processes
        without a parent process:

        >>> from proc.core import find_processes
        >>> pprint([p for p in find_processes() if not p.ppid])
        [Process(pid=1, comm='init', state='S', pgrp=1, session=1, vsize=25174016, rss=1667072, cmdline=['/sbin/init']),
         Process(pid=2, comm='kthreadd', state='S', pgrp=0, session=0, vsize=0, rss=0)]
        """
        return int(self.stat_fields[3])

    @lazy_property
    def rss(self):
        """
        The resident set size of the process *in bytes* (an integer).

        Quoting from `man 5 proc`_:

         *Number of pages the process has in real memory. This is just the
         pages which count toward text, data, or stack space. This does not
         include pages which have not been demand-loaded in, or which are
         swapped out.*

        This property translates *pages* to *bytes* by multiplying the value
        extracted from ``/proc/[pid]/stat`` with the result of:

        .. code-block:: python

           os.sysconf('SC_PAGESIZE')

        **Availability:** This property is parsed from the contents of
        ``/proc/[pid]/stat`` and is always available.
        """
        return int(self.stat_fields[23]) * os.sysconf('SC_PAGESIZE')

    @property
    def runtime(self):
        """
        The time in seconds since the process started (a float).

        This property is calculated based on :attr:`starttime` every time
        it's requested (so it will always be up to date).

        .. warning:: The runtime will not stop growing when the process ends
                     because doing so would require a background thread just to
                     monitor when the process ends... This is an unfortunate
                     side effect of the architecture of ``/proc`` -- processes
                     disappear from ``/proc`` the moment they end so the
                     information about when the process ended is lost!
        """
        return max(0, time.time() - self.starttime)

    @lazy_property
    def session(self):
        """
        The session ID of the process (an integer).

        **Availability:** This property is parsed from the contents of
        ``/proc/[pid]/stat`` and is always available.
        """
        return int(self.stat_fields[5])

    @lazy_property
    def starttime(self):
        """
        The time at which the process was started (a float).

        Paraphrasing from `man 5 proc`_:

         *The time the process started after system boot. In kernels before
         Linux 2.6, this value was expressed in jiffies. Since Linux 2.6, the
         value is expressed in clock ticks.*

        This property translates *clock ticks* to *seconds* by dividing the
        value extracted from ``/proc/[pid]/stat`` with the result of:

        .. code-block:: python

           os.sysconf('SC_CLK_TCK')

        After the conversion to seconds the system's uptime is used to
        determine the absolute start time of the process (the number of seconds
        since the Unix epoch_).

        See also the :attr:`runtime` property.

        **Availability:** This property is calculated from the contents of
        ``/proc/[pid]/stat`` and ``/proc/uptime`` and is always available.

        .. _epoch: http://en.wikipedia.org/wiki/Unix_time
        """
        system_boot = time.time() - find_system_uptime()
        ticks_after_boot = int(self.stat_fields[21])
        seconds_after_boot = ticks_after_boot / float(os.sysconf('SC_CLK_TCK'))
        return system_boot + seconds_after_boot

    @lazy_property
    def state(self):
        """
        A single uppercase character describing the state of the process (a string).

        Quoting from `man 5 proc`_:

         *One character from the string "RSDZTW" where R is running, S is
         sleeping in an interruptible wait, D is waiting in uninterruptible
         disk sleep, Z is zombie_, T is traced or stopped (on a signal), and W
         is paging.*

        **Availability:** This property is parsed from the contents of
        ``/proc/[pid]/stat`` and is always available.

        .. _zombie: http://en.wikipedia.org/wiki/Zombie_process
        """
        return self.stat_fields[2]

    @lazy_property
    def status_fields(self):
        """
        Detailed process information (a dictionary with string key/value pairs).

        The dictionaries constructed by this property are based on the contents
        of ``/proc/[pid]/status``, which `man 5 proc`_ describes as follows:

         *Provides much of the information in /proc/[pid]/stat and
         /proc/[pid]/statm in a format that's easier for humans to parse.*

        While it's true that there is quite a lot of overlap between
        ``/proc/[pid]/stat`` and ``/proc/[pid]/status``, the latter also
        exposes important information that isn't available elsewhere (e.g.
        :attr:`user_ids` and :attr:`group_ids`).

        **Availability:**

        - This property is parsed from the contents of ``/proc/[pid]/status``
          the first time it is referenced, after that its value is cached so it
          will always be available.

        - If this property is first referenced after the process turns into a
          zombie_ or the process ends then it's too late to read the contents
          of ``/proc/[pid]/status`` and an empty dictionary is returned.
        """
        fields = {}
        with ProtectedAccess('status', "read detailed process status"):
            with open(os.path.join(self.proc_tree, 'status')) as handle:
                for line in handle:
                    name, _, value = line.partition(':')
                    fields[name] = value.strip()
        return fields

    @lazy_property
    def user(self):
        """
        The username of the real user ID (a string).

        **Availability:** Refer to :attr:`user_ids`. :data:`None` is returned
        if :attr:`user_ids` is unavailable or :func:`uid_to_name()` fails.
        """
        return uid_to_name(self.user_ids.real) if self.user_ids else None

    @lazy_property
    def user_ids(self):
        """
        The real, effective, saved set, and filesystem UIDs of the process (an :class:`OwnerIDs` object).

        **Availability:** Refer to :attr:`status_fields`. :data:`None` is
        returned if :attr:`status_fields` is unavailable.
        """
        return self._parse_ids('Uid')

    @lazy_property
    def vsize(self):
        """
        The virtual memory size of the process in bytes (an integer).

        **Availability:** This property is parsed from the contents of
        ``/proc/[pid]/stat`` and is always available.
        """
        return int(self.stat_fields[22])

    def _parse_ids(self, field_name):
        """Helper for :attr:`user_ids` and :attr:`group_ids`."""
        raw_value = self.status_fields.get(field_name, '')
        parsed_values = [int(n) for n in raw_value.split()]
        if len(parsed_values) >= 4:
            return OwnerIDs(*parsed_values[:4])


class OwnerIDs(collections.namedtuple('OwnerIDs', 'real, effective, saved, fs')):

    """
    A set of user or group IDs found in ``/proc/[pid]/status``.

    :class:`OwnerIDs` objects are named tuples containing four integer numbers
    called `real`, `effective`, `saved` and `fs`.
    """


def find_processes(obj_type=Process):
    """
    Scan the numerical subdirectories of ``/proc`` for process information.

    :param obj_type: The type of process objects to construct (expected to be
                     :class:`Process` or a subclass of :class:`Process`).
    :returns: A generator of :class:`Process` objects.
    """
    if not issubclass(obj_type, Process):
        raise TypeError("Custom process types should inherit from proc.core.Process!")
    root = '/proc'
    num_processes = 0
    logger.debug("Scanning for process information in %r ..", root)
    for entry in os.listdir(root):
        if entry.isdigit():
            process = obj_type.from_path(os.path.join(root, entry))
            if process:
                num_processes += 1
                yield process
    logger.debug("Finished scanning %r, found %i processes.", root, num_processes)


def find_system_uptime():
    """
    Find the system's uptime.

    :returns: The uptime in seconds (a float).

    This function returns the first number found in ``/proc/uptime``.
    """
    with open('/proc/uptime') as handle:
        contents = handle.read()
        fields = contents.split()
        return float(fields[0])


def sorted_by_pid(processes):
    """
    Sort the given processes by their process ID.

    :param processes: An iterable of :class:`Process` objects.
    :returns: A list of :class:`Process` objects sorted by their process ID.
    """
    return sorted(processes, key=lambda p: p.pid)


def parse_process_status(directory, silent=False):
    """
    Read and tokenize a ``/proc/[pid]/stat`` file.

    :param directory: The absolute pathname of the numerical subdirectory of
                      ``/proc`` to get process information from (a string).
    :returns: A list of strings containing the tokenized fields or ``None`` if
              the ``/proc/[pid]/stat`` file disappears before it can be read
              (in this case a warning is logged).
    """
    with ProtectedAccess('stat', "read process status"):
        with open(os.path.join(directory, 'stat')) as handle:
            contents = handle.read()
        # If a process ends after we've successfully opened the corresponding
        # /proc/[pid]/stat file but before we've read the file contents I'm not
        # 100% sure if a nonempty read is guaranteed, so we'll just make sure
        # we actually got a nonempty read (I'd rather err on the side of
        # caution :-).
        if contents:
            # This comment is here to justify the gymnastics with
            # str.partition() and str.rpartition() below:
            #
            # The second field in /proc/[pid]/stat (called `comm' in `man 5
            # proc') is the executable name. It's enclosed in parentheses and
            # may contain spaces. Due to the very sparse documentation about
            # this _obscure_ encoding I got curious and experimented a bit:
            #
            # Nothing prevents an executable name from containing parentheses
            # and because these are just arbitrary characters without any
            # meaning they don't need to be balanced. When such an executable
            # name is embedded in /proc/[pid]/stat no further encoding is
            # applied, you'll just get something like '((python))'.
            #
            # Fortunately the `comm' field is the only field that can contain
            # arbitrary text, so if you take the text between the left most and
            # right most parenthesis in /proc/[pid]/stat you'll end up with the
            # correct answer!
            before_comm, _, remainder = contents.partition('(')
            comm, _, after_comm = remainder.rpartition(')')
            # Combine the tokenized fields into a list of strings. All of the
            # fields except `comm' are integers or a single alphabetic
            # character (the state field) so using str.split() is okay here.
            fields = before_comm.split()
            fields.append(comm)
            fields.extend(after_comm.split())
            return fields


def parse_process_cmdline(directory):
    """
    Read and tokenize a ``/proc/[pid]/cmdline`` file.

    :param directory: The absolute pathname of the numerical subdirectory of
                      ``/proc`` to get process information from (a string).
    :returns: A list of strings containing the tokenized command line. If the
              ``/proc/[pid]/cmdline`` file disappears before it can be read an
              empty list is returned (in this case a warning is logged).
    """
    contents = ''
    with ProtectedAccess('cmdline', "read process command line"):
        with open(os.path.join(directory, 'cmdline')) as handle:
            contents = handle.read()
    # Strip the trailing null byte so we don't report every command line with a
    # trailing empty string (our callers should not be bothered with obscure
    # details about the encoding of /proc/[pid]/cmdline).
    if contents.endswith('\0'):
        contents = contents[:-1]
    # Python's str.split() implementation splits empty strings into a list
    # containing a single empty string. This is an incorrect representation of
    # a parsed command line so we explicitly guard against this.
    return contents.split('\0') if contents else []


def uid_to_name(uid):
    """
    Find the username associated with a user ID.

    :param uid: The user ID (an integer).
    :returns: The username (a string) or :data:`None` if :func:`pwd.getpwuid()`
              fails to locate a user for the given ID.
    """
    try:
        return pwd.getpwuid(uid).pw_name
    except Exception:
        return None


def gid_to_name(gid):
    """
    Find the group name associated with a group ID.

    :param gid: The group ID (an integer).
    :returns: The group name (a string) or :data:`None` if :func:`grp.getgrgid()`
              fails to locate a group for the given ID.
    """
    try:
        return grp.getgrgid(gid).gr_name
    except Exception:
        return None


class ProtectedAccess(object):

    """Context manager that deals with permission errors and race conditions."""

    def __init__(self, key, action):
        """
        Initialize a :class:`ProtectedAccess` object.

        :param key: The key in :data:`num_race_conditions` (a string).
        :param action: A verb followed by a noun describing what kind of access
                       is being protected (a string)
        """
        self.key = key
        self.action = action

    def __enter__(self):
        """Enter the context (does nothing)."""

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Log and swallow exceptions and count race conditions."""
        if exc_type is not None:
            # Gotcha: On Python 2.6 when exc_type is IOError exc_value is
            # an actual tuple instead of an exception object, hence
            # the issubclass() and exc_value[0] gymnastics.
            filename = getattr(exc_value, 'filename', 'filename unknown')
            if issubclass(exc_type, EnvironmentError):
                error_code = getattr(exc_value, 'errno', None) or exc_value[0]
                if error_code == errno.EACCES:
                    # Permission errors are silently swallowed.
                    return True
                if error_code in (errno.ENOENT, errno.ESRCH):
                    # If the file has gone missing we consider it a race condition:
                    #  - ENOENT is reported when /proc/[pid] disappears.
                    #  - ESRCH is reported when /proc/[pid]/stat disappears.
                    logger.debug("Failed to %s due to race condition! (%s)",
                                 self.action, filename)
                    num_race_conditions[self.key] += 1
                    return True
            # Other exceptions are logged and swallowed.
            logger.warning("Failed to %s because of unexpected exception! (%s)",
                           self.action, filename, exc_info=(exc_type, exc_value, traceback))
        return True
