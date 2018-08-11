# proc: Simple interface to Linux process information.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 27, 2016
# URL: https://proc.readthedocs.io

"""
The :mod:`proc.apache` module monitors the memory usage of Apache_ workers.

This module builds on top of the :mod:`proc.tree` module as an example of
how memory usage of web server workers can be monitored using the `proc`
package.

The main entry point of this module is :func:`find_apache_memory_usage()`
which provides you with the minimum, average, median and maximum memory usage
of the discovered Apache worker processes (it also provides the raw
:attr:`~proc.core.Process.rss` value of each worker, in case you don't trust
the aggregates ;-).

.. note:: This module only works if you've configured your Apache web server to
          use an MPM_ based on processes (not threads). The main reason for
          this is that :mod:`proc.core` doesn't expose information about the
          individual threads in a process based on ``/proc/[pid]/task`` yet
          (I'm still on the fence about whether to expose this information or
          not).

.. _Apache: http://en.wikipedia.org/wiki/Apache_HTTP_Server
.. _MPM: http://httpd.apache.org/docs/current/mpm.html
"""

# Standard library modules.
import collections
import logging
import re

# External dependencies.
from proc.tree import get_process_tree, ProcessNode

# Initialize a logger.
logger = logging.getLogger(__name__)


def find_apache_memory_usage(exe_name='apache2'):
    """
    Find the memory usage of Apache workers.

    :param exe_name: The base name of the Apache executable (a string).
    :returns: A tuple of two values:

              1. A :class:`StatsList` of integers with the resident set size
                 of Apache workers that are not WSGI daemon processes.
              2. A dictionary of key/value pairs, as follows:

                 - Each key is a WSGI process group name (see the
                   :attr:`~MaybeApacheWorker.wsgi_process_group` property).
                 - Each value is a :class:`StatsList` of integers with the
                   resident set size of the workers belonging to the WSGI
                   process group.
    """
    worker_rss = StatsList()
    wsgi_rss = collections.defaultdict(StatsList)
    for worker in find_apache_workers(exe_name):
        if worker.wsgi_process_group:
            wsgi_rss[worker.wsgi_process_group].append(worker.rss)
        else:
            worker_rss.append(worker.rss)
    return worker_rss, wsgi_rss


class StatsList(list):

    """Subclass of :class:`list` that provides some simple statistics."""

    @property
    def min(self):
        """
        The minimum value from a list of numbers (a number).

        :raises: :exc:`~exceptions.ValueError` when the list is empty.
        """
        return min(self)

    @property
    def max(self):
        """
        The maximum value from a list of numbers (a number).

        :raises: :exc:`~exceptions.ValueError` when the list is empty.
        """
        return max(self)

    @property
    def average(self):
        """
        The average value from a list of numbers (a float).

        :raises: :exc:`~exceptions.ValueError` when the list is empty.
        """
        if len(self) == 0:
            raise ValueError("Cannot calculate average of empty list")
        return sum(self) / float(len(self))

    @property
    def median(self):
        """
        The median value from a list of numbers (a number).

        :raises: :exc:`~exceptions.ValueError` when the list is empty.
        """
        if len(self) == 0:
            raise ValueError("Cannot calculate median of empty list")
        self.sort()
        count = len(self)
        index = (count - 1) // 2
        if (count % 2):
            return self[index]
        else:
            return (self[index] + self[index + 1]) / 2.0


def find_apache_workers(exe_name='apache2'):
    """
    Find Apache workers in the process tree reported by :func:`~proc.tree.get_process_tree()`.

    :param exe_name: The base name of the Apache executable (a string).
    :returns: A generator of :class:`MaybeApacheWorker` objects.
    :raises: :exc:`ApacheDaemonNotRunning` when the Apache master process
             cannot be found.
    """
    init = get_process_tree(obj_type=MaybeApacheWorker)
    master = init.find(exe_name=exe_name)
    if not master:
        raise ApacheDaemonNotRunning("Could not find Apache master process! Is it running?")
    for process in master.children:
        if process.exe_path == master.exe_path:
            yield process


class MaybeApacheWorker(ProcessNode):

    """Subclass of :class:`~proc.tree.ProcessNode` that understands Apache workers."""

    @property
    def wsgi_process_group(self):
        """
        The name of the mod_wsgi_ process group (a string).

        This property makes two assumptions about the way you've configured
        Apache's mod_wsgi_ module (which is required to reliably differentiate
        WSGI workers from regular Apache workers):

        1. The `display-name` option for the WSGIDaemonProcess_ directive is
           used to customize the process names of WSGI daemon processes.

        2. The configured `display-name` is of the form ``(wsgi:...)``. The
           closing parenthesis is not actually significant because the names of
           WSGI process groups can be truncated (refer to the documentation of
           the WSGIDaemonProcess_ directive for details) and in such cases the
           trailing parenthesis is truncated as well.

        If the first string in :attr:`~proc.core.Process.cmdline` doesn't
        start with ``(wsgi:`` this property returns an empty string.

        .. _mod_wsgi: https://code.google.com/p/modwsgi/
        .. _WSGIDaemonProcess: http://code.google.com/p/modwsgi/wiki/ConfigurationDirectives#WSGIDaemonProcess
        """
        if self.cmdline:
            m = re.match(r'^\(wsgi:([^)]+)', self.cmdline[0])
            if m:
                return m.group(1)
        return ''


class ApacheDaemonNotRunning(Exception):

    """Exception raised by :func:`find_apache_workers()` when it cannot locate the Apache daemon process."""
