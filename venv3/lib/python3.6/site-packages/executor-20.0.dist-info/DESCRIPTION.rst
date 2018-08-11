executor: Programmer friendly subprocess wrapper
================================================

.. image:: https://travis-ci.org/xolox/python-executor.svg?branch=master
   :target: https://travis-ci.org/xolox/python-executor

.. image:: https://coveralls.io/repos/xolox/python-executor/badge.png?branch=master
   :target: https://coveralls.io/r/xolox/python-executor?branch=master

The `executor` package is a simple wrapper for Python's subprocess_ module
that makes it very easy to handle subprocesses on UNIX systems with proper
escaping of arguments and error checking:

- An object oriented interface is used to execute commands using sane but
  customizable (and well documented) defaults.

- Remote commands (executed over SSH_) are supported using the same object
  oriented interface, as are commands inside chroots_ (executed using
  schroot_).

- There's also support for executing a group of commands concurrently in
  what's called a "command pool". The concurrency level can be customized and
  of course both local and remote commands are supported.

The package is currently tested on Python 2.6, 2.7, 3.4, 3.5, 3.6 and PyPy. For
usage instructions please refer to following sections and the documentation_.

.. contents::
   :local:
   :depth: 2

Installation
------------

The `executor` package is available on PyPI_ which means installation should be
as simple as:

.. code-block:: sh

   $ pip install executor

There's actually a multitude of ways to install Python packages (e.g. the `per
user site-packages directory`_, `virtual environments`_ or just installing
system wide) and I have no intention of getting into that discussion here, so
if this intimidates you then read up on your options before returning to these
instructions ;-).

Usage
-----

There are two ways to use the `executor` package: As the command line program
``executor`` and as a Python API. The command line interface is described below
and there are also some examples of simple use cases of the Python API.

.. contents::
   :local:
   :depth: 1

Command line
~~~~~~~~~~~~

.. A DRY solution to avoid duplication of the `executor --help' text:
..
.. [[[cog
.. from humanfriendly.usage import inject_usage
.. inject_usage('executor.cli')
.. ]]]

**Usage:** `executor [OPTIONS] COMMAND ...`

Easy subprocess management on the command line based on the Python package with
the same name. The "executor" program runs external commands with support for
timeouts, dynamic startup delay (fudge factor) and exclusive locking.

You can think of "executor" as a combination of the "flock" and "timelimit"
programs with some additional niceties (namely the dynamic startup delay and
integrated system logging on UNIX platforms).

**Supported options:**

.. csv-table::
   :header: Option, Description
   :widths: 30, 70


   "``-t``, ``--timeout=LIMIT``","Set the time after which the given command will be aborted. By default
   ``LIMIT`` is counted in seconds. You can also use one of the suffixes ""s""
   (seconds), ""m"" (minutes), ""h"" (hours) or ""d"" (days)."
   "``-f``, ``--fudge-factor=LIMIT``","This option controls the dynamic startup delay (fudge factor) which is
   useful when you want a periodic task to run once per given interval but the
   exact time is not important. Refer to the ``--timeout`` option for acceptable
   values of ``LIMIT``, this number specifies the maximum amount of time to sleep
   before running the command (the minimum is zero, otherwise you could just
   include the command ""sleep N && ..."" in your command line :-)."
   "``-e``, ``--exclusive``","Use an interprocess lock file to guarantee that executor will never run
   the external command concurrently. Refer to the ``--lock-timeout`` option
   to customize blocking / non-blocking behavior. To customize the name
   of the lock file you can use the ``--lock-file`` option."
   "``-T``, ``--lock-timeout=LIMIT``","By default executor tries to claim the lock and if it fails it will exit
   with a nonzero exit code. This option can be used to enable blocking
   behavior. Refer to the ``--timeout`` option for acceptable values of ``LIMIT``."
   "``-l``, ``--lock-file=NAME``","Customize the name of the lock file. By default this is the base name of
   the external command, so if you're running something generic like ""bash""
   or ""python"" you might want to change this :-)."
   "``-v``, ``--verbose``",Increase logging verbosity (can be repeated).
   "``-q``, ``--quiet``",Decrease logging verbosity (can be repeated).
   "``-h``, ``--help``",Show this message and exit.

.. [[[end]]]

Python API
~~~~~~~~~~

Below are some examples of how versatile the `execute()`_ function is. Refer to
the API documentation on `Read the Docs`_ for (a lot of) other use cases.

.. contents::
   :local:

Checking status codes
+++++++++++++++++++++

By default the status code of the external command is returned as a boolean:

>>> from executor import execute
>>> execute('true')
True

If an external command exits with a nonzero status code an exception is raised,
this makes it easy to do the right thing (never forget to check the status code
of an external command without having to write a lot of repetitive code):

>>> execute('false')
Traceback (most recent call last):
  File "executor/__init__.py", line 124, in execute
    cmd.start()
  File "executor/__init__.py", line 516, in start
    self.wait()
  File "executor/__init__.py", line 541, in wait
    self.check_errors()
  File "executor/__init__.py", line 568, in check_errors
    raise ExternalCommandFailed(self)
executor.ExternalCommandFailed: External command failed with exit code 1! (command: bash -c false)

The ExternalCommandFailed_ exception exposes ``command`` and ``returncode``
attributes. If you know a command is likely to exit with a nonzero status code
and you want `execute()`_ to simply return a boolean you can do this instead:

>>> execute('false', check=False)
False

Providing input
+++++++++++++++

Here's how you can provide input to an external command:

>>> execute('tr a-z A-Z', input='Hello world from Python!\n')
HELLO WORLD FROM PYTHON!
True

Getting output
++++++++++++++

Getting the output of external commands is really easy as well:

>>> execute('hostname', capture=True)
'peter-macbook'

Running commands as root
++++++++++++++++++++++++

It's also very easy to execute commands with super user privileges:

>>> execute('echo test > /etc/hostname', sudo=True)
[sudo] password for peter: **********
True
>>> execute('hostname', capture=True)
'test'

Enabling logging
++++++++++++++++

If you're wondering how prefixing the above command with ``sudo`` would
end up being helpful, here's how it works:

>>> import logging
>>> logging.basicConfig()
>>> logging.getLogger().setLevel(logging.DEBUG)
>>> execute('echo peter-macbook > /etc/hostname', sudo=True)
DEBUG:executor:Executing external command: sudo bash -c 'echo peter-macbook > /etc/hostname'

Running remote commands
+++++++++++++++++++++++

To run a command on a remote system using SSH_ you can use the RemoteCommand_
class, it works as follows:

>>> from executor.ssh.client import RemoteCommand
>>> cmd = RemoteCommand('localhost', 'echo $SSH_CONNECTION', capture=True)
>>> cmd.start()
>>> cmd.output
'127.0.0.1 57255 127.0.0.1 22'

Running remote commands concurrently
++++++++++++++++++++++++++++++++++++

The `foreach()`_ function wraps the RemoteCommand_ and CommandPool_ classes to
make it very easy to run a remote command concurrently on a group of hosts:

>>> from executor.ssh.client import foreach
>>> from pprint import pprint
>>> hosts = ['127.0.0.1', '127.0.0.2', '127.0.0.3', '127.0.0.4']
>>> commands = foreach(hosts, 'echo $SSH_CONNECTION')
>>> pprint([cmd.output for cmd in commands])
['127.0.0.1 57278 127.0.0.1 22',
 '127.0.0.1 52385 127.0.0.2 22',
 '127.0.0.1 49228 127.0.0.3 22',
 '127.0.0.1 40628 127.0.0.4 22']

Contact
-------

The latest version of `executor` is available on PyPI_ and GitHub_. The
documentation is hosted on `Read the Docs`_ and includes a changelog_. For bug
reports please create an issue on GitHub_. If you have questions, suggestions,
etc. feel free to send me an e-mail at `peter@peterodding.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2018 Peter Odding.

.. External references:
.. _changelog: https://executor.readthedocs.io/en/latest/changelog.html
.. _chroots: http://en.wikipedia.org/wiki/Chroot
.. _CommandPool: https://executor.readthedocs.io/en/latest/api.html#executor.concurrent.CommandPool
.. _documentation: https://executor.readthedocs.io
.. _execute(): http://executor.readthedocs.io/en/latest/api.html#executor.execute
.. _ExternalCommandFailed: http://executor.readthedocs.io/en/latest/api.html#executor.ExternalCommandFailed
.. _foreach(): https://executor.readthedocs.io/en/latest/api.html#executor.ssh.client.foreach
.. _GitHub: https://github.com/xolox/python-executor
.. _MIT license: http://en.wikipedia.org/wiki/MIT_License
.. _per user site-packages directory: https://www.python.org/dev/peps/pep-0370/
.. _peter@peterodding.com: peter@peterodding.com
.. _PyPI: https://pypi.python.org/pypi/executor
.. _Read the Docs: https://executor.readthedocs.io/en/latest/api.html#api-documentation
.. _RemoteCommand: https://executor.readthedocs.io/en/latest/api.html#executor.ssh.client.RemoteCommand
.. _schroot: https://wiki.debian.org/Schroot
.. _SSH: https://en.wikipedia.org/wiki/Secure_Shell
.. _subprocess: https://docs.python.org/2/library/subprocess.html
.. _virtual environments: http://docs.python-guide.org/en/latest/dev/virtualenvs/


