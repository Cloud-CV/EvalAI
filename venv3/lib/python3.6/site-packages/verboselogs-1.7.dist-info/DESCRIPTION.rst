verboselogs: Verbose logging level for Python's logging module
==============================================================

.. image:: https://travis-ci.org/xolox/python-verboselogs.svg?branch=master
   :target: https://travis-ci.org/xolox/python-verboselogs

.. image:: https://coveralls.io/repos/xolox/python-verboselogs/badge.png?branch=master
   :target: https://coveralls.io/r/xolox/python-verboselogs?branch=master

The verboselogs_ package extends Python's logging_ module to add the log levels
NOTICE_, SPAM_, SUCCESS_ and VERBOSE_:

- The NOTICE level sits between the predefined WARNING and INFO levels.
- The SPAM level sits between the predefined DEBUG and NOTSET levels.
- The SUCCESS level sits between the predefined WARNING and ERROR levels.
- The VERBOSE level sits between the predefined INFO and DEBUG levels.

The code to do this is simple and short, but I still don't want to copy/paste
it to every project I'm working on, hence this package. It's currently tested
on Python 2.6, 2.7, 3.4, 3.5, 3.6 and PyPy.

.. contents::
   :local:
   :depth: 2

Installation
------------

The verboselogs package is available on PyPI_ which means installation should
be as simple as:

.. code-block:: sh

   $ pip install verboselogs

There's actually a multitude of ways to install Python packages (e.g. the `per
user site-packages directory`_, `virtual environments`_ or just installing
system wide) and I have no intention of getting into that discussion here, so
if this intimidates you then read up on your options before returning to these
instructions ;-).

Usage
-----

It's very simple to start using the verboselogs package:

>>> import logging, verboselogs
>>> logger = verboselogs.VerboseLogger('verbose-demo')
>>> logger.addHandler(logging.StreamHandler())
>>> logger.setLevel(logging.VERBOSE)
>>> logger.verbose("Can we have verbose logging? %s", "Yes we can!")

Here's a skeleton of a very simple Python program with a command line interface
and configurable logging:

.. code-block:: python

   """
   Usage: demo.py [OPTIONS]

   This is the usage message of demo.py. Usually
   this text explains how to use the program.

   Supported options:
     -v, --verbose  make more noise
     -h, --help     show this message and exit
   """

   import getopt
   import logging
   import sys
   import verboselogs

   logger = verboselogs.VerboseLogger('demo')
   logger.addHandler(logging.StreamHandler())
   logger.setLevel(logging.INFO)

   # Command line option defaults.
   verbosity = 0

   # Parse command line options.
   opts, args = getopt.getopt(sys.argv[1:], 'vqh', ['verbose', 'quiet', 'help'])

   # Map command line options to variables.
   for option, argument in opts:
       if option in ('-v', '--verbose'):
           verbosity += 1
       elif option in ('-q', '--quiet'):
           verbosity -= 1
       elif option in ('-h', '--help'):
           print __doc__.strip()
           sys.exit(0)
       else:
           assert False, "Unhandled option!"

   # Configure logger for requested verbosity.
   if verbosity >= 4:
       logger.setLevel(logging.SPAM)
   elif verbosity >= 3:
       logger.setLevel(logging.DEBUG)
   elif verbosity >= 2:
       logger.setLevel(logging.VERBOSE)
   elif verbosity >= 1:
       logger.setLevel(logging.NOTICE)
   elif verbosity < 0:
       logger.setLevel(logging.WARNING)

   # Your code goes here.
   ...

If you want to set VerboseLogger_ as the default logging class for all
subsequent logger instances, you can do so using `verboselogs.install()`_:

.. code-block:: python

   import logging
   import verboselogs

   verboselogs.install()
   logger = logging.getLogger(__name__) # will be a VerboseLogger instance

Pylint plugin
-------------

If using the above `verboselogs.install()`_ approach, Pylint_ is not smart
enough to recognize that logging_ is using verboselogs, resulting in errors
like::

   E:285,24: Module 'logging' has no 'VERBOSE' member (no-member)
   E:375,12: Instance of 'RootLogger' has no 'verbose' member (no-member)

To fix this, verboselogs provides a Pylint plugin verboselogs.pylint_ which,
when loaded with ``pylint --load-plugins verboselogs.pylint``, adds the
verboselogs methods and constants to Pylint's understanding of the logging_
module.

Overview of logging levels
--------------------------

The table below shows the names, `numeric values`_ and descriptions_ of the
predefined log levels and the VERBOSE, NOTICE, and SPAM levels defined by this
package, plus some notes that I added.

========  =====  =============================  =============================
Level     Value  Description                    Notes
========  =====  =============================  =============================
NOTSET    0      When a logger is created, the  This level isn't intended to
                 level is set to NOTSET (note   be used explicitly, however
                 that the root logger is        when a logger has its level
                 created with level WARNING).   set to NOTSET its effective
                                                level will be inherited from
                                                the parent logger.
SPAM      5      Way too verbose for regular
                 debugging, but nice to have
                 when someone is getting
                 desperate in a late night
                 debugging session and decides
                 that they want as much
                 instrumentation as possible!
                 :-)
DEBUG     10     Detailed information,          Usually at this level the
                 typically of interest only     logging output is so low
                 when diagnosing problems.      level that it's not useful
                                                to users who are not
                                                familiar with the software's
                                                internals.
VERBOSE   15     Detailed information that
                 should be understandable to
                 experienced users to provide
                 insight in the software's
                 behavior; a sort of high
                 level debugging information.
INFO      20     Confirmation that things
                 are working as expected.
NOTICE    25     Auditing information about
                 things that have multiple
                 success paths or may need to
                 be reverted.
WARNING   30     An indication that something
                 unexpected happened, or
                 indicative of some problem
                 in the near future (e.g.
                 ‘disk space low’). The
                 software is still working
                 as expected.
SUCCESS   35     A very explicit confirmation
                 of success.
ERROR     40     Due to a more serious
                 problem, the software has not
                 been able to perform some
                 function.
CRITICAL  50     A serious error, indicating
                 that the program itself may
                 be unable to continue
                 running.
========  =====  =============================  =============================

Contact
-------

The latest version of verboselogs is available on PyPI_ and GitHub_. The
documentation is hosted on `Read the Docs`_. For bug reports please create an
issue on GitHub_. If you have questions, suggestions, etc. feel free to send me
an e-mail at `peter@peterodding.com`_.

License
-------

This software is licensed under the `MIT license`_.

© 2017 Peter Odding.

.. External references:
.. _descriptions: http://docs.python.org/howto/logging.html#when-to-use-logging
.. _GitHub: https://github.com/xolox/python-verboselogs
.. _logging: http://docs.python.org/library/logging.html
.. _MIT license: http://en.wikipedia.org/wiki/MIT_License
.. _NOTICE: http://verboselogs.readthedocs.io/en/latest/api.html#verboselogs.NOTICE
.. _numeric values: http://docs.python.org/howto/logging.html#logging-levels
.. _per user site-packages directory: https://www.python.org/dev/peps/pep-0370/
.. _peter@peterodding.com: peter@peterodding.com
.. _Pylint: https://pypi.python.org/pypi/pylint
.. _PyPI: https://pypi.python.org/pypi/verboselogs
.. _Read the Docs: https://verboselogs.readthedocs.io
.. _SPAM: http://verboselogs.readthedocs.io/en/latest/api.html#verboselogs.SPAM
.. _SUCCESS: http://verboselogs.readthedocs.io/en/latest/api.html#verboselogs.SUCCESS
.. _VERBOSE: http://verboselogs.readthedocs.io/en/latest/api.html#verboselogs.VERBOSE
.. _VerboseLogger: http://verboselogs.readthedocs.io/en/latest/api.html#verboselogs.VerboseLogger
.. _verboselogs.install(): http://verboselogs.readthedocs.io/en/latest/api.html#verboselogs.install
.. _verboselogs.pylint: http://verboselogs.readthedocs.io/en/latest/api.html#verboselogs.pylint
.. _verboselogs: https://pypi.python.org/pypi/verboselogs/
.. _virtual environments: http://docs.python-guide.org/en/latest/dev/virtualenvs/


