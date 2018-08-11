# Human friendly input/output in Python.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: February 17, 2016
# URL: https://humanfriendly.readthedocs.io

"""
Customizations for and integration with the Sphinx_ documentation generator.

The :mod:`humanfriendly.sphinx` module uses the `Sphinx extension API`_ to
customize the process of generating Sphinx based Python documentation.
The most relevant functions to take a look at are :func:`setup()`,
:func:`enable_special_methods()` and :func:`enable_usage_formatting()`.

.. _Sphinx: http://www.sphinx-doc.org/
.. _Sphinx extension API: http://sphinx-doc.org/extdev/appapi.html
"""

# Standard library modules.
import logging
import types

# Modules included in our package.
from humanfriendly.usage import USAGE_MARKER, render_usage

# Initialize a logger for this module.
logger = logging.getLogger(__name__)


def setup(app):
    """
    Enable all of the provided Sphinx_ customizations.

    :param app: The Sphinx application object.

    The :func:`setup()` function makes it easy to enable all of the Sphinx
    customizations provided by the :mod:`humanfriendly.sphinx` module with the
    least amount of code. All you need to do is to add the module name to the
    ``extensions`` variable in your ``conf.py`` file:

    .. code-block:: python

       # Sphinx extension module names.
       extensions = [
           'sphinx.ext.autodoc',
           'sphinx.ext.doctest',
           'sphinx.ext.intersphinx',
           'humanfriendly.sphinx',
       ]

    When Sphinx sees the :mod:`humanfriendly.sphinx` name it will import the
    module and call its :func:`setup()` function.

    At the time of writing this just calls :func:`enable_special_methods()` and
    :func:`enable_usage_formatting()`, but of course more functionality may be
    added at a later stage. If you don't like that idea you may be better of
    calling the individual functions from your own ``setup()`` function.
    """
    enable_special_methods(app)
    enable_usage_formatting(app)


def enable_special_methods(app):
    """
    Enable documenting "special methods" using the autodoc_ extension.

    :param app: The Sphinx application object.

    This function connects the :func:`special_methods_callback()` function to
    ``autodoc-skip-member`` events.

    .. _autodoc: http://www.sphinx-doc.org/en/stable/ext/autodoc.html
    """
    app.connect('autodoc-skip-member', special_methods_callback)


def special_methods_callback(app, what, name, obj, skip, options):
    """
    Enable documenting "special methods" using the autodoc_ extension.

    Refer to :func:`enable_special_methods()` to enable the use of this
    function (you probably don't want to call
    :func:`special_methods_callback()` directly).

    This function implements a callback for ``autodoc-skip-member`` events to
    include documented "special methods" (method names with two leading and two
    trailing underscores) in your documentation. The result is similar to the
    use of the ``special-members`` flag with one big difference: Special
    methods are included but other types of members are ignored. This means
    that attributes like ``__weakref__`` will always be ignored (this was my
    main annoyance with the ``special-members`` flag).

    The parameters expected by this function are those defined for Sphinx event
    callback functions (i.e. I'm not going to document them here :-).
    """
    if getattr(obj, '__doc__', None) and isinstance(obj, (types.FunctionType, types.MethodType)):
        return False
    else:
        return skip


def enable_usage_formatting(app):
    """
    Reformat human friendly usage messages to reStructuredText_.

    :param app: The Sphinx application object (as given to ``setup()``).

    This function connects the :func:`usage_message_callback()` function to
    ``autodoc-process-docstring`` events.

    .. _reStructuredText: https://en.wikipedia.org/wiki/ReStructuredText
    """
    app.connect('autodoc-process-docstring', usage_message_callback)


def usage_message_callback(app, what, name, obj, options, lines):
    """
    Reformat human friendly usage messages to reStructuredText_.

    Refer to :func:`enable_usage_formatting()` to enable the use of this
    function (you probably don't want to call :func:`usage_message_callback()`
    directly).

    This function implements a callback for ``autodoc-process-docstring`` that
    reformats module docstrings using :func:`.render_usage()` so that Sphinx
    doesn't mangle usage messages that were written to be human readable
    instead of machine readable. Only module docstrings whose first line starts
    with :data:`.USAGE_MARKER` are reformatted.

    The parameters expected by this function are those defined for Sphinx event
    callback functions (i.e. I'm not going to document them here :-).
    """
    # Make sure we only modify the docstrings of modules.
    if isinstance(obj, types.ModuleType) and lines:
        # Make sure we only modify docstrings containing a usage message.
        if lines[0].startswith(USAGE_MARKER):
            # Convert the usage message to reStructuredText.
            text = render_usage('\n'.join(lines))
            # Clear the existing line buffer.
            while lines:
                lines.pop()
            # Fill up the buffer with our modified docstring.
            lines.extend(text.splitlines())
