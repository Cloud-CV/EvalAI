proc: Linux process information interface
=========================================

.. image:: https://travis-ci.org/xolox/python-proc.svg?branch=master
   :target: https://travis-ci.org/xolox/python-proc

.. image:: https://coveralls.io/repos/xolox/python-proc/badge.svg?branch=master
   :target: https://coveralls.io/r/xolox/python-proc?branch=master

The Python package `proc` exposes process information available in the Linux
`process information pseudo-file system`_ available at ``/proc``. The `proc`
package is currently tested on cPython 2.6, 2.7, 3.4, 3.5 and PyPy (2.7). The
automated test suite regularly runs on Ubuntu Linux but other Linux variants
(also those not based on Debian Linux) should work fine. For usage instructions
please refer to the documentation_.

.. contents::
   :local:

Installation
------------

The `proc` package is available on PyPI_ which means installation should be as
simple as:

.. code-block:: sh

   $ pip install proc

There's actually a multitude of ways to install Python packages (e.g. the `per
user site-packages directory`_, `virtual environments`_ or just installing
system wide) and I have no intention of getting into that discussion here, so
if this intimidates you then read up on your options before returning to these
instructions ;-).

Once you've installed the `proc` package head over to the documentation_ for
some examples of how the `proc` package can be used.

Design choices
--------------

The `proc` package was created with the following considerations in mind:

**Completely specialized to Linux**
 It parses ``/proc`` and nothing else ;-).

**Fully implemented in Python**
 No binary/compiled components, as opposed to psutil_ which is way more
 portable but requires a compiler for installation.

**Very well documented**
 The documentation should make it easy to get started (as opposed to procfs_
 which I evaluated and eventually gave up on because I had to resort to reading
 through its source code just to be disappointed in its implementation).

**Robust implementation**
 Reading ``/proc`` is inherently sensitive to race conditions and the `proc`
 package takes this into account, in fact the test suite contains a test that
 creates race conditions in order to verify that they are handled correctly.
 The API of the `proc` package hides race conditions as much as possible and
 where this is not possible the consequences are clearly documented.

**Layered API design** (where each layer is documented)
 Builds higher level abstractions on top of lower level abstractions:

 **The proc.unix module**
  Defines a simple process class that combines process IDs and common UNIX
  signals to implement process control primitives like waiting for a process to
  end and gracefully or forcefully terminating a process.

 **The proc.core module**
  Builds on top of the ``proc.unix`` module to provide a simple, fast and easy
  to use API for the process information available in ``/proc``. If you're
  looking for a simple and/or fast interface to ``/proc`` that does the heavy
  lifting (parsing) for you then this is what you're looking for.

 **The proc.tree module**
  Builds on top of the ``proc.core`` module to provide an in-memory tree data
  structure that mimics the actual process tree, enabling easy searching and
  navigation through the process tree.

 **The proc.apache module**
  Builds on top of the ``proc.tree`` module to implement an easy to use Python
  API that does metrics collection for monitoring of Apache web server worker
  memory usage, including support for WSGI process groups.

 **The proc.cron module**
  Implements the command line program ``cron-graceful`` which gracefully
  terminates cron daemons. This module builds on top of the ``proc.tree``
  module as a demonstration of the possibilities of the `proc` package and as a
  practical tool that is ready to be used on any Linux system that has Python
  and cron_ installed.

 **The proc.notify module**
  Implements the command line program ``notify-send-headless`` which can be
  used to run the program ``notify-send`` in headless environments like cron
  jobs and system daemons.

History
-------

I've been writing shell and Python scripts that parse ``/proc`` for years now
(it seems so temptingly easy when you get started ;-). Sometimes I resorted to
copy/pasting snippets of Python code between personal and work projects because
the code was basically done, just not available in an easy to share form.

Once I started fixing bugs in diverging copies of that code I decided it was
time to combine all of the features I'd grown to appreciate into a single well
tested and well documented Python package with an easy to use API and share it
with the world.

This means that, although I made my first commit on the `proc` package in March
2015, much of its code has existed for years in various forms.

Similar projects
----------------

Below are several other Python libraries that expose process information. If
the `proc` package isn't working out for you consider trying one of these. The
summaries are copied and/or paraphrased from the documentation of each
package:

psutil_
  A cross-platform library for retrieving information on running processes and
  system utilization (CPU, memory, disks, network) in Python.

procpy_
  A Python wrapper for the procps_ library and a module containing higher level
  classes (with some extensions compared to procps_).

procfs_
  Python API for the Linux ``/proc`` virtual filesystem.

Future improvements
-------------------

Some random ideas for future improvements:

- The ``notify-send-headless`` program can be generalized into "please run this
  external command inside the current graphical environment". I recently ran
  into several unrelated situations where this would have been useful!

Contact
-------

The latest version of `proc` is available on PyPI_ and GitHub_. The
documentation is hosted on `Read the Docs`_. For bug reports please create an
issue on GitHub_. If you have questions, suggestions, etc. feel free to send me
an e-mail at `peter@peterodding.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2016 Peter Odding.

.. External references:
.. _cron: http://en.wikipedia.org/wiki/Cron
.. _documentation: https://proc.readthedocs.io
.. _GitHub: https://github.com/xolox/python-proc
.. _MIT license: http://en.wikipedia.org/wiki/MIT_License
.. _per user site-packages directory: https://www.python.org/dev/peps/pep-0370/
.. _peter@peterodding.com: peter@peterodding.com
.. _process information pseudo-file system: http://linux.die.net/man/5/proc
.. _procfs: https://pypi.python.org/pypi/procfs
.. _procps: http://procps.sourceforge.net/
.. _procpy: http://code.google.com/p/procpy/
.. _psutil: https://pypi.python.org/pypi/psutil/
.. _PyPI: https://pypi.python.org/pypi/proc
.. _Read the Docs: https://proc.readthedocs.io
.. _virtual environments: http://docs.python-guide.org/en/latest/dev/virtualenvs/


