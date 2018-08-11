# proc: Simple interface to Linux process information.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: November 10, 2015
# URL: https://proc.readthedocs.io

"""
The :mod:`proc.tree` module builds tree data structures based on process trees.

This module builds on top of :mod:`proc.core` to provide a tree data
structure that mirrors the process tree implied by the process information
reported by :func:`~proc.core.find_processes()` (specifically the
:attr:`~proc.core.Process.ppid` attributes). Here's a simple example that
shows how much code you need to find the `cron daemon`_, it's workers and the
children of those workers (cron jobs):

>>> from proc.tree import get_process_tree
>>> init = get_process_tree()
>>> cron_daemon = init.find(exe_name='cron')
>>> cron_workers = cron_daemon.children
>>> cron_jobs = cron_daemon.grandchildren

After the above five lines the ``cron_jobs`` variable will contain a collection
of :class:`ProcessNode` objects, one for each cron job that ``cron`` is
executing. The :mod:`proc.cron` module contains a more full fledged example
of using the :mod:`proc.tree` module.

.. _cron daemon: http://en.wikipedia.org/wiki/Cron
.. _flatten a list of lists: http://stackoverflow.com/questions/406121/flattening-a-shallow-list-in-python
"""

# Standard library modules.
import logging

# External dependencies.
from property_manager import lazy_property, writable_property

# Modules provided by our package.
from proc.core import find_processes, Process

# Initialize a logger.
logger = logging.getLogger(__name__)


class ProcessNode(Process):

    """
    Process information including relationships that model the process tree.

    :class:`ProcessNode` is a subclass of :class:`~proc.core.Process`
    that adds relationships between processes to model the process tree as a
    tree data structure. This makes it easier and more intuitive to extract
    information from the process tree by analyzing the relationships:

    - To construct a tree you use :func:`get_process_tree()`. This function
      connects all of the nodes in the tree before returning the root node
      (this node represents init_).

    - To navigate the tree you can use the :attr:`parent`,
      :attr:`children`, :attr:`grandchildren` and :attr:`descendants`
      properties.

    - If you're looking for specific descendant processes consider using
      :func:`find()` or :func:`find_all()`.
    """

    @writable_property
    def parent(self):
        """
        The :class:`ProcessNode` object of the parent of this process.

        Based on the :attr:`~proc.core.Process.ppid` attribute. ``None`` when
        the process doesn't have a parent.
        """

    @lazy_property
    def children(self):
        """A list of :class:`ProcessNode` objects with the children of this process."""
        return []

    @property
    def grandchildren(self):
        """
        Find the grandchildren of this process.

        :returns: A generator of :class:`ProcessNode` objects.
        """
        for child in self.children:
            for grandchild in child.children:
                yield grandchild

    @property
    def descendants(self):
        """
        Find the descendants of this process.

        :returns: A generator of :class:`ProcessNode` objects.
        """
        stack = list(self.children)
        while stack:
            process = stack.pop(0)
            stack.extend(process.children)
            yield process

    def find(self, *args, **kw):
        """
        Find the first child process of this process that matches one or more criteria.

        This method accepts the same parameters as the :func:`find_all()` method.

        :returns: The :class:`ProcessNode` object of the first process that
                  matches the given criteria or ``None`` if no processes match.
        """
        for process in self.find_all(*args, **kw):
            return process

    def find_all(self, pid=None, exe_name=None, exe_path=None, recursive=False):
        """
        Find child processes of this process that match one or more criteria.

        :param pid: If this parameter is given, only processes with the given
                    :attr:`~proc.core.Process.pid` will be returned.
        :param exe_name: If this parameter is given, only processes with the
                         given :attr:`~proc.core.Process.exe_name` will be
                         returned.
        :param exe_path: If this parameter is given, only processes with the
                         given :attr:`~proc.core.Process.exe_path` will be
                         returned.
        :param recursive: If this is ``True`` (not the default) all processes
                          in :attr:`descendants` will be searched, otherwise
                          only the processes in :attr:`children` are
                          searched (the default).
        :returns: A generator of :class:`ProcessNode` objects.
        """
        for process in (self.descendants if recursive else self.children):
            if ((pid is None or process.pid == pid) and
                    (exe_name is None or process.exe_name == exe_name) and
                    (exe_path is None or process.exe_path == exe_path)):
                yield process


def get_process_tree(obj_type=ProcessNode):
    """
    Construct a process tree from the result of :func:`~proc.core.find_processes()`.

    :param obj_type: The type of process objects to construct (expected to be
                     :class:`ProcessNode` or a subclass of
                     :class:`ProcessNode`).
    :returns: A :class:`ProcessNode` object that forms the root node of the
              constructed tree (this node represents init_).

    .. _init: http://en.wikipedia.org/wiki/init
    """
    if not issubclass(obj_type, ProcessNode):
        raise TypeError("Custom process types should inherit from proc.tree.ProcessNode!")
    mapping = dict((p.pid, p) for p in find_processes(obj_type=obj_type))
    for obj in mapping.values():
        if obj.ppid != 0 and obj.ppid in mapping:
            obj.parent = mapping[obj.ppid]
            obj.parent.children.append(obj)
    return mapping[1]
