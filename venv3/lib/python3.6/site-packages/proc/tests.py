# Automated tests for the `proc' package.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 12, 2016
# URL: https://proc.readthedocs.io

"""Test suite for the `proc` package."""

# Standard library modules.
import getpass
import logging
import multiprocessing
import operator
import os
import pipes
import random
import shutil
import subprocess
import sys
import tempfile
import time
import unittest

from pprint import pformat

# External dependencies.
import coloredlogs
from executor import ExternalCommand, get_search_path, which
from executor.contexts import AbstractContext
from humanfriendly import parse_size, Timer
from humanfriendly.compat import basestring
from humanfriendly.text import compact

# Modules included in our package.
from proc.apache import find_apache_memory_usage, StatsList
from proc.core import Process, find_processes, gid_to_name, num_race_conditions, uid_to_name
from proc.cron import ADDITIONS_SCRIPT_NAME, cron_graceful, ensure_root_privileges, run_additions, wait_for_processes
from proc.notify import REQUIRED_VARIABLES, find_graphical_context, notify_desktop
from proc.tree import get_process_tree
from proc.unix import UnixProcess

# Initialize a logger.
logger = logging.getLogger(__name__)


def setUpModule():
    """
    Prepare the test suite.

    Sets up verbose logging to the terminal. When a test fails the logging
    output can help to perform a post-mortem analysis of the failure in
    question (even when its hard to reproduce locally). This is especially
    useful when debugging remote test failures, whether they happened on Travis
    CI or a user's local system.
    """
    coloredlogs.install(level='DEBUG')


class ProcTestCase(unittest.TestCase):

    """
    :mod:`unittest` compatible container for the test suite of `proc`.
    """

    def setUp(self):
        """Reset the logging level before every test runs."""
        coloredlogs.set_level('DEBUG')
        # Separate the name of the test method (printed by the superclass
        # and/or py.test without a newline at the end) from the first line of
        # logging output that the test method is likely going to generate.
        sys.stderr.write("\n")

    def skipTest(self, text, *args, **kw):
        """
        Enable backwards compatible "marking of tests to skip".

        By calling this method from a return statement in the test to be
        skipped the test can be marked as skipped when possible, without
        breaking the test suite when unittest.TestCase.skipTest() isn't
        available.
        """
        reason = compact(text, *args, **kw)
        try:
            super(ProcTestCase, self).skipTest(reason)
        except AttributeError:
            # unittest.TestCase.skipTest() isn't available in Python 2.6.
            logger.warning("%s", reason)

    def test_uid_to_name(self):
        """Make sure :func:`uid_to_name()` never raises exceptions."""
        self.check_id_to_name(uid_to_name)

    def test_gid_to_name(self):
        """Make sure :func:`gid_to_name()` never raises exceptions."""
        self.check_id_to_name(gid_to_name)

    def check_id_to_name(self, fun, limit=10000):
        """Helper for :func:`test_uid_to_name()` and :func:`test_gid_to_name()`."""
        for i in range(limit):
            result = fun(random.randint(0, limit))
            if result is None:
                # Found a missing entry without raising an exception.
                return
        assert False, "Failed to find unknown UID or GID?!"

    def test_process_from_path(self):
        """Test the :func:`proc.core.Process.from_path()` constructor."""
        process = Process.from_path('/proc/self')
        # The following tests verify properties based on information available
        # from the Python standard library.
        assert process.pid == os.getpid(), "Unexpected process ID!"
        assert process.ppid == os.getppid(), "Unexpected parent process ID!"
        assert process.pgrp == os.getpgrp(), "Unexpected process group ID!"
        assert process.user_ids.real == os.getuid(), "Unexpected real user ID!"
        assert process.group_ids.real == os.getgid(), "Unexpected real group ID!"
        # The following assertion may fail at some point, but I chose it above
        # using uid_to_name(os.getuid()) because the latter isn't testing
        # anything useful at all ...
        assert process.user == getpass.getuser(), "Unexpected username based on real user ID!"
        # We really can't make much assumptions about the name of the real
        # group ID so we'll just check whether it's available.
        assert process.group, "Expected process to have real group ID with group name!"
        # The following tests are based on common sense, here's hoping they
        # don't bite me in the ass later on :-).
        assert process.state == 'R', "Unexpected process state!"
        assert process.runtime < 600, "Test process running for >= 10 minutes?!"
        assert process.rss > parse_size('10 MB'), "Resident set size (RSS) less than 10 MB?!"
        assert process.vsize > process.rss, "Virtual memory usage less than its resident set size (RSS)?!"
        assert executable(process.cmdline[0]) or which(process.cmdline[0]), \
            "First token in process command line isn't executable?!"
        assert executable(process.exe), "Process executable pathname (based on /proc/[pid]/stat) invalid?!"
        assert executable(process.exe_path), "Process executable pathname (fall back option) invalid?!"
        assert which(process.exe_name), "Process executable base name (fall back option) not available on $PATH?!"
        assert process.is_alive, "The current process is not running?! :-P"
        # Python's standard library doesn't seem to expose process session IDs
        # so all I can test reliably is that the session ID is an integer...
        assert isinstance(process.session, int), "Process session ID not available!"

    def test_find_processes(self):
        """Test the :func:`proc.core.find_processes()` function."""
        # Test argument validation. Obscure Python implementation detail:
        # Because find_processes() returns a generator we need to actually ask
        # for the first value to be produced in order to invoke the argument
        # validation.
        self.assertRaises(TypeError, next, find_processes(obj_type=object))
        # Test some basic assumptions about the result of find_processes().
        processes = dict((p.pid, p) for p in find_processes())
        assert 1 in processes, "init process not found in output of find_processes()!"
        assert processes[1].comm == 'init', "init isn't called init?!"
        assert os.getpid() in processes, "Current process not found in output of find_processes()!"

    def test_is_alive(self):
        """Test the :func:`proc.core.Process.is_alive` property."""
        # Spawn a child that will live for a minute.
        with ExternalCommand('sleep', '60', check=False) as child:
            # Construct a process object for the child.
            process = Process.from_pid(child.pid)
            # Make sure the process object agrees the child is alive.
            assert process.is_alive, "Child died before Process.is_alive was called?!"
            # Kill the child process and give it a moment to terminate
            # (significantly less time then the process is normally expected to
            # run, otherwise there's no point in the test below).
            child.terminate(timeout=10)
            # Make sure the process object agrees the child is dead.
            assert not process.is_alive, "Child is still alive even though we killed it?!"

    def test_environ(self):
        """Test that parsing of process environments works as expected."""
        unique_value = str(random.random())
        with ExternalCommand('sleep', '30', environment=dict(unique_value=unique_value)) as sleep_cmd:
            sleep_proc = Process.from_pid(sleep_cmd.pid)
            assert sleep_proc.environ['unique_value'] == unique_value

    def test_find_graphical_context(self):
        """Test that :func:`proc.notify.find_graphical_context()` works."""
        context = find_graphical_context()
        assert isinstance(context, AbstractContext)
        assert context.execute('true', check=False)

    def test_notify_desktop(self):
        """Test that :func:`proc.notify.notify_desktop()` works."""
        env = dict((name, 'value') for name in REQUIRED_VARIABLES)
        with ExternalCommand('sleep 60', environment=env):
            with MockProgram('notify-send'):
                notify_desktop(
                    summary="Headless notifications",
                    body="They actually work! (this message brought to you by the 'proc' test suite :-)",
                    urgency='low',
                )

    def test_exe_path_fallback(self):
        """Test the fall back method of :attr:`proc.core.Process.exe_path`."""
        candidates = [p for p in find_processes() if p.exe_path and not p.exe]
        logger.debug("Candidates for Process.exe_path fall back test:\n%s", pformat(candidates))
        if not candidates:
            return self.skipTest("No processes available on which Process.exe_path fall back can be tested!")
        assert executable(candidates[0].exe_path), \
            "Fall back method of Process.exe_path reported invalid executable pathname!"

    def test_exe_name_fallback(self):
        """Test the fall back method of :attr:`proc.core.Process.exe_name`."""
        if os.getuid() == 0:
            # Given root privileges all /proc/[pid]/exe symbolic links can be
            # successfully resolved so we can't test the fall back method.
            return self.skipTest("Fall back method of Process.exe_name is useless with root privileges!")
        candidates = [p for p in find_processes() if p.exe_name and not p.exe_path]
        logger.debug("Candidates for Process.exe_name fall back test:\n %s", pformat(candidates))
        if not candidates:
            return self.skipTest("No processes available on which Process.exe_name fall back can be tested!")
        assert any(which(p.exe_name) for p in candidates), \
            "Fall back method of Process.exe_name reported executable base name not available on $PATH?!"

    def test_tree_construction(self, timeout=60):
        """Test the functionality of the :mod:`proc.tree` module."""
        # Test argument validation.
        self.assertRaises(TypeError, get_process_tree, obj_type=object)
        # Spawn a child and grandchild (because of shell=True) that will live for a minute.
        child = subprocess.Popen(['sleep 60'], shell=True)
        # Use a try / finally block to make sure we kill our child before returning.
        try:
            # This test used to fail intermittently on Travis CI because the child
            # and grandchild need a moment to initialize and the test wasn't giving
            # the two processes the time they needed to initialize. However any
            # given time.sleep(N) value is completely arbitrary (if a computer can
            # be slow it can also be really slow :-) so instead I've decided to
            # repeat the test until it succeeds, with a timeout in case it actually
            # does fail and won't succeed despite waiting.
            timer = Timer()
            while True:
                # Use a try / except block (in a while loop) to retry as long
                # as the timeout hasn't been hit and bubble the exception when
                # once we hit the timeout.
                try:
                    # Construct a process tree.
                    init = get_process_tree()
                    # Locate our own process in the tree.
                    self = init.find(pid=os.getpid(), recursive=True)
                    # Verify that the child is visible in the process tree.
                    logger.debug("Children in process tree: %s", list(self.children))
                    assert child.pid in [c.pid for c in self.children], \
                        "Child process not visible in process tree reported by get_process_tree()!"
                    # Verify that the grandchild is visible in the process tree.
                    logger.debug("Grandchildren in process tree: %s", list(self.grandchildren))
                    assert any(gc.exe_name == 'sleep' for gc in self.grandchildren), \
                        "Grandchild process not visible in process tree reported by get_process_tree()!"
                    # Once both assertions have succeeded the test has also
                    # succeeded and we return (break out of the while loop).
                    return
                except AssertionError:
                    if timer.elapsed_time >= timeout:
                        # Stop swallowing assertions once we hit the timeout.
                        raise
                    else:
                        # Don't burn CPU cycles too much.
                        time.sleep(0.1)
        finally:
            # Make sure we always kill our child.
            child.terminate()

    def test_wait_for_processes(self):
        """Test the :func:`proc.cron.wait_for_processes()` function."""
        children = [subprocess.Popen(['sleep', str(int(5 + random.random() * 5))]) for i in range(5)]
        wait_for_processes([Process.from_pid(c.pid) for c in children])
        assert sum(c.poll() is None for c in children) == 0, \
            "wait_for_processes() returned before all processes ended!"

    def test_cron_graceful_dry_run(self):
        """Test a dry run of the ``cron-graceful`` program."""
        # Test that `cron-graceful -h' / `cron-graceful --help' works.
        self.assertRaises(SystemExit, cron_graceful, ['-h'])
        self.assertRaises(SystemExit, cron_graceful, ['--help'])
        # Test that invalid command line options raise an error.
        self.assertRaises(SystemExit, cron_graceful, ['--whatever'])
        # Test that root privileges are ensured.
        if os.getuid() == 0:
            # This shouldn't do anything.
            ensure_root_privileges()
        else:
            # This is expected to use sys.exit(1).
            self.assertRaises(SystemExit, ensure_root_privileges)
        # Test that command line options for verbosity control are accepted and
        # that a dry run of cron-graceful runs successfully.
        cron_graceful(['-q', '--quiet', '-v', '--verbose', '-n', '--dry-run'])

    def test_cron_graceful_additions(self):
        """Test :func:`proc.cron.run_additions()`."""
        # If no program with the name cron-graceful-additions is available
        # on the $PATH we expect this to be handled ... gracefully :-).
        with CustomSearchPath():
            run_additions()
        # If a program with the name cron-graceful-additions is available
        # on the $PATH we expect it to be executed successfully.
        with MockProgram(ADDITIONS_SCRIPT_NAME):
            run_additions()
        # If the cron-graceful-additions program fails we also expect this
        # to be handled gracefully (i.e. a message is logged but the error
        # isn't propagated).
        with MockProgram(ADDITIONS_SCRIPT_NAME, returncode=1):
            run_additions()

    def test_race_conditions(self, timeout=60):
        """
        Test the handling of race conditions in :mod:`proc.core`.

        Scanning ``/proc`` is inherently vulnerable to race conditions, for
        example:

        1. A listing of available processes in ``/proc`` confirms a process
           exists, but by the time ``/proc/[pid]/stat`` is read the process has
           ended and ``/proc/[pid]`` no longer exists.

        2. A :class:`proc.core.Process` object is constructed from the
           information available in ``/proc/[pid]/stat``, but by the time
           ``/proc/[pid]/cmdline`` is read the process has ended and
           ``/proc/[pid]`` no longer exists.

        This test intentionally creates race conditions in the reading of
        ``/proc/[pid]/stat``, ``/proc/[pid]/cmdline`` and
        ``/proc/[pid]/environ`` files, to verify that the :mod:`proc.core`
        module never breaks on a race condition.

        It works by using the :mod:`multiprocessing` module to quickly spawn
        and reclaim subprocesses while at the same time scanning through
        ``/proc`` continuously. The test times out after 60 seconds but in all
        of the runs I've tried so far it never needs more than 10 seconds to
        encounter a handful of race conditions.
        """
        # Copy the race condition counters so we can verify all counters have
        # increased before we consider this test to have passed.
        logger.info("Testing handling of race conditions, please be patient :-) ..")
        timer = Timer()
        at_start = dict(num_race_conditions)
        shutdown_event = multiprocessing.Event()
        manager = multiprocessing.Process(target=race_condition_manager,
                                          args=(shutdown_event,))
        manager.start()
        try:
            while True:
                # Scan the process tree with the knowledge that subprocesses could
                # be disappearing any second now :-).
                for process in find_processes():
                    if process.ppid == manager.pid:
                        # Force a time window between when /proc/[pid]/stat was
                        # read and when /proc/[pid]/cmdline will be read.
                        time.sleep(0.1)
                        # Read /proc/[pid]/cmdline, /proc/[pid]/environ and
                        # /proc/[pid]/exe even though they may no longer exist.
                        assert isinstance(process.cmdline, list)
                        assert isinstance(process.environ, dict)
                        assert isinstance(process.exe, basestring)
                        assert isinstance(process.status_fields, dict)
                # Check whether race conditions have been handled.
                if all(num_race_conditions[k] > at_start[k] for k in at_start):
                    # The test has passed: We were able to simulate at least
                    # one race condition of every type within the timeout.
                    logger.info("Successfully finished race condition test in %s.", timer)
                    return
                assert timer.elapsed_time < timeout, "Timeout elapsed before race conditions could be simulated!"
                # Don't burn CPU cycles too much.
                time.sleep(0.1)
        finally:
            shutdown_event.set()
            manager.join()

    def test_stats_list(self):
        """Test the :class:`proc.apache.StatsList` class."""
        # Test argument validation.
        self.assertRaises(ValueError, operator.attrgetter('average'), StatsList())
        self.assertRaises(ValueError, operator.attrgetter('median'), StatsList())
        # Test the actual calculations (specifically average and median).
        sample = StatsList([0, 1, 1, 2, 3, 5, 8, 13, 21, 34])
        assert sample.min == 0
        assert sample.max == 34
        assert sample.average == 8.8
        assert sample.median == 4
        # Also test the if block in the median property (the above tests the else block).
        assert StatsList([0, 1, 1, 2, 3, 5, 8, 13, 21]).median == 3

    def test_apache_worker_monitoring(self):
        """Test the :mod:`proc.apache` module."""
        if not os.path.exists('/etc/apache2/sites-enabled/proc-test-vhost'):
            return self.skipTest("Apache worker monitoring test disabled except on Travis CI!")
        worker_rss, wsgi_rss = find_apache_memory_usage()
        # Make sure some regular Apache workers were identified.
        assert len(worker_rss) > 0, "No regular Apache workers found?!"
        assert worker_rss.average > 0
        # Make sure at least one group of WSGI workers was identified. The
        # identification of WSGI workers requires root privileges, so
        # without that there's no point in running the test (we know it
        # will fail).
        if os.getuid() != 0:
            return self.skipTest("Apache WSGI worker monitoring test requires root privileges!")
        assert 'proc-test' in wsgi_rss
        assert wsgi_rss['proc-test'].average > 0

    def test_graceful_termination(self):
        """Test graceful process termination."""
        self.check_process_termination(method='terminate')

    def test_forceful_termination(self):
        """Test forceful process termination."""
        self.check_process_termination(method='kill')

    def check_process_termination(self, method):
        """Helper method for process termination tests."""
        timer = Timer()
        # We use Executor to launch an external process.
        with ExternalCommand('sleep', '60', check=False) as cmd:
            # Verify that proc.unix.UnixProcess.is_running (which is normally
            # overridden by proc.core.Process.is_running) works as expected,
            # even though this property isn't actively used in the `proc'
            # package because we want to deal with not-yet-reclaimed
            # processes and zombie processes which is very much a Linux
            # specific thing (hence the override).
            unix_process = UnixProcess(pid=cmd.pid)
            assert unix_process.is_running, "UnixProcess.is_running is broken!"
            # We don't use Executor to control the process, instead we take the
            # process ID and use it to create a Process object that doesn't
            # know about Python's subprocess module.
            linux_process = Process.from_pid(cmd.pid)
            # We terminate the process using a positive but very low timeout so
            # that all of the code involved gets a chance to run, but without
            # significantly slowing down the test suite.
            getattr(linux_process, method)(timeout=0.1)
            # Now we can verify our assertions.
            assert not linux_process.is_running, "Child still running despite graceful termination request!"
            assert timer.elapsed_time < 10, "It look too long to terminate the child!"
            # Now comes a hairy bit of Linux implementation details that most
            # people can thankfully ignore (blissful ignorance :-). Parent
            # processes are responsible for reclaiming child processes and
            # until this happens the /proc/[pid] entry remains, which means
            # the `kill -0' trick used by UnixProcess to detect running
            # processes doesn't work as expected. Basically this means we
            # _must_ make sure that waitpid() is called before we can expect
            # UnixProcess.is_running to behave as expected.
            cmd.wait()
            # Now that we've called waitpid() things should work as expected.
            assert not unix_process.is_running, "UnixProcess.is_running is broken!"

    def test_is_running(self):
        """Test that UnixProcess.is_running gracefully handles processes it doesn't have permission to query."""
        init = UnixProcess(pid=1)
        assert init.is_running

    def test_suspend_and_resume_signals(self):
        """Test the sending of ``SIGSTOP``, ``SIGCONT`` and ``SIGTERM`` signals."""
        # Spawn a child that will live for a minute.
        with ExternalCommand('sleep', '60', check=False) as cmd:
            process = Process.from_pid(cmd.pid)
            # Suspend the execution of the child process using SIGSTOP.
            process.suspend()
            # Test that the child process doesn't respond to SIGTERM once suspended.
            process.terminate(wait=False)
            assert process.is_running, "Child responded to signal even though it was suspended?!"
            # Resume the execution of the child process using SIGCONT.
            process.resume()
            # Test that the child process responds to signals again after
            # having been resumed, but give it a moment to terminate
            # (significantly less time then the process is normally expected
            # to run, otherwise there's no point in the test below).
            process.kill(wait=True, timeout=5)
            assert not process.is_running, "Child didn't respond to signal even though it was resumed?!"


def executable(pathname):
    """Check whether a pathname is executable."""
    return pathname and os.access(pathname, os.X_OK)


def race_condition_manager(shutdown_event):
    """Quickly spawn and reclaim subprocesses to cause race conditions."""
    num_spawned = 0
    subprocesses = []
    while not shutdown_event.is_set():
        # Spawn some new subprocesses.
        while len(subprocesses) < 25:
            helper = RaceConditionHelper()
            subprocesses.append(helper)
            helper.start()
            num_spawned += 1
        # Reclaim dead subprocesses.
        for helper in list(subprocesses):
            if not helper.is_alive():
                helper.join()
                subprocesses.remove(helper)
        # Don't burn unnecessary CPU cycles.
        time.sleep(0.1)
    logger.info("Shutdown event was set, terminating %i remaining helpers ..", len(subprocesses))
    for helper in subprocesses:
        helper.terminate()
        helper.join()
    logger.info("Spawned a total of %i subprocesses.", num_spawned)


class RaceConditionHelper(multiprocessing.Process):

    """Simple subprocess that helps to cause race conditions ..."""

    def run(self):
        """Sleep for a couple of seconds before terminating."""
        timeout = random.random() * 5
        logger.debug("Race condition helper %i sleeping for %.2f seconds ..", os.getpid(), timeout)
        time.sleep(timeout)
        logger.debug("Race condition helper %i terminating ..", os.getpid())


class TemporaryDirectory(object):

    """
    Easy temporary directory creation & cleanup using the :keyword:`with` statement.

    Here's an example of how to use this:

    .. code-block:: python

       with TemporaryDirectory() as directory:
           # Do something useful here.
           assert os.path.isdir(directory)
    """

    def __init__(self, **options):
        """
        Initialize context manager that manages creation & cleanup of temporary directory.

        :param options: Any keyword arguments are passed on to
                        :func:`tempfile.mkdtemp()`.
        """
        self.options = options
        self.temporary_directory = None

    def __enter__(self):
        """Create the temporary directory."""
        if self.temporary_directory is None:
            self.temporary_directory = tempfile.mkdtemp(**self.options)
            logger.debug("Created temporary directory: %s", self.temporary_directory)
        return self.temporary_directory

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Destroy the temporary directory."""
        if self.temporary_directory is not None:
            logger.debug("Cleaning up temporary directory: %s", self.temporary_directory)
            shutil.rmtree(self.temporary_directory)
            self.temporary_directory = None


class CustomSearchPath(TemporaryDirectory):

    """Context manager to create an isolated executable search path."""

    def __init__(self, *args, **kw):
        """Initialize an :class:`CustomSearchPath` object."""
        super(CustomSearchPath, self).__init__(*args, **kw)
        self.original_search_path = None

    def __enter__(self):
        """Activate the isolated search path."""
        directory = super(CustomSearchPath, self).__enter__()
        self.original_search_path = os.environ.get('PATH')
        os.environ['PATH'] = self.custom_search_path
        return directory

    def __exit__(self, *args, **kw):
        """Deactivate the isolated search path."""
        if self.original_search_path is not None:
            os.environ['PATH'] = self.original_search_path
            self.original_search_path = None
        return super(CustomSearchPath, self).__exit__(*args, **kw)

    @property
    def custom_search_path(self):
        """The custom search path (a string)."""
        return self.temporary_directory


class MockProgram(CustomSearchPath):

    """Context manager to mock executables."""

    def __init__(self, name, returncode=0, *args, **kw):
        """Initialize an :class:`MockProgram` object."""
        super(MockProgram, self).__init__(*args, **kw)
        self.program_name = name
        self.returncode = returncode
        self.signal_file = None

    def __enter__(self):
        """Create the mock program."""
        directory = super(MockProgram, self).__enter__()
        self.signal_file = os.path.join(directory, 'signal-file')
        pathname = os.path.join(directory, self.program_name)
        with open(pathname, 'w') as handle:
            handle.write('#!/bin/sh\n')
            handle.write('echo > %s\n' % pipes.quote(self.signal_file))
            handle.write('exit %i\n' % self.returncode)
        os.chmod(pathname, 0o755)
        return directory

    def __exit__(self, *args, **kw):
        """Make sure the mock program was run."""
        try:
            assert self.signal_file and os.path.isfile(self.signal_file), \
                ("Looks like %r was never run!" % self.program_name)
        finally:
            return super(MockProgram, self).__exit__(*args, **kw)

    @property
    def custom_search_path(self):
        """The custom search path (a string)."""
        return os.pathsep.join([self.temporary_directory] + get_search_path())
