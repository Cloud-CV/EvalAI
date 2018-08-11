# Useful property variants for Python programming.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 19, 2018
# URL: https://property-manager.readthedocs.org

"""
Integration with the Sphinx_ documentation generator.

The :mod:`property_manager.sphinx` module uses the `Sphinx extension API`_ to
customize the process of generating Sphinx based Python documentation. It
modifies the documentation of :class:`.PropertyManager` subclasses to include
an overview of superclasses, properties, public methods and special methods. It
also includes hints about required properties and how the values of properties
can be set by passing keyword arguments to the class initializer.

For a simple example check out the documentation of the :class:`TypeInspector`
class. Yes, that means this module is being used to document itself :-).

The entry point to this module is the :func:`setup()` function.

.. _Sphinx extension API: http://sphinx-doc.org/extdev/appapi.html
"""

# Standard library modules.
import types

# Modules included in our package.
from property_manager import PropertyManager, custom_property, lazy_property, required_property
from humanfriendly import compact, concatenate, format
from humanfriendly.tables import format_rst_table

# Public identifiers that require documentation.
__all__ = (
    'setup',
    'append_property_docs',
    'TypeInspector',
)


def setup(app):
    """
    Make it possible to use :mod:`property_manager.sphinx` as a Sphinx extension.

    :param app: The Sphinx application object.

    To enable the use of this module you add the name of the module
    to the ``extensions`` option in your ``docs/conf.py`` script:

    .. code-block:: python

       extensions = [
           'sphinx.ext.autodoc',
           'sphinx.ext.intersphinx',
           'property_manager.sphinx',
       ]

    When Sphinx sees the :mod:`property_manager.sphinx` name it will import
    this module and call the :func:`setup()` function which will connect the
    :func:`append_property_docs()` function to ``autodoc-process-docstring``
    events.
    """
    app.connect('autodoc-process-docstring', append_property_docs)


def append_property_docs(app, what, name, obj, options, lines):
    """
    Render an overview with properties and methods of :class:`.PropertyManager` subclasses.

    This function implements a callback for ``autodoc-process-docstring`` that
    generates and appends an overview of member details to the docstrings of
    :class:`.PropertyManager` subclasses.

    The parameters expected by this function are those defined for Sphinx event
    callback functions (i.e. I'm not going to document them here :-).
    """
    if is_suitable_type(obj):
        paragraphs = []
        details = TypeInspector(type=obj)
        hints = (details.required_hint, details.initializer_hint)
        if any(hints):
            paragraphs.append(' '.join(h for h in hints if h))
        paragraphs.append(format("Here's an overview of the :class:`%s` class:", obj.__name__))
        # Whitespace in labels is replaced with non breaking spaces to disable wrapping of the label text.
        data = [(format("%s:", label.replace(' ', u'\u00A0')), text) for label, text in details.overview if text]
        paragraphs.append(format_rst_table(data))
        if lines:
            lines.append('')
        lines.extend('\n\n'.join(paragraphs).splitlines())


def is_suitable_type(obj):
    try:
        return issubclass(obj, PropertyManager)
    except Exception:
        return False


class TypeInspector(PropertyManager):

    """Introspection of :class:`.PropertyManager` subclasses."""

    @lazy_property
    def custom_properties(self):
        """A list of tuples with the names and values of custom properties."""
        return [(n, v) for n, v in self.properties if isinstance(v, custom_property)]

    @lazy_property
    def initializer_hint(self):
        """A hint that properties can be set using keyword arguments to the initializer (a string or :data:`None`)."""
        names = sorted(
            name for name, value in self.custom_properties
            if value.key or value.required or value.writable
        )
        if names:
            return compact(
                """
                You can set the {values} of the {names} {properties}
                by passing {arguments} to the class initializer.
                """,
                names=self.format_properties(names),
                values=("value" if len(names) == 1 else "values"),
                properties=("property" if len(names) == 1 else "properties"),
                arguments=("a keyword argument" if len(names) == 1 else "keyword arguments"),
            )

    @lazy_property
    def members(self):
        """An iterable of tuples with the names and values of the non-inherited members of :class:`type`."""
        return list(self.type.__dict__.items())

    @lazy_property
    def methods(self):
        """An iterable of method names of :class:`type`."""
        return sorted(n for n, v in self.members if isinstance(v, types.FunctionType))

    @lazy_property
    def overview(self):
        """Render an overview with related members grouped together."""
        return (
            ("Superclass" if len(self.type.__bases__) == 1 else "Superclasses",
             concatenate(format(":class:`~%s.%s`", b.__module__, b.__name__) for b in self.type.__bases__)),
            ("Special methods", self.format_methods(self.special_methods)),
            ("Public methods", self.format_methods(self.public_methods)),
            ("Properties", self.format_properties(n for n, v in self.properties)),
        )

    @lazy_property
    def properties(self):
        """An iterable of tuples with property names (strings) and values (:class:`property` objects)."""
        return [(n, v) for n, v in self.members if isinstance(v, property)]

    @lazy_property
    def public_methods(self):
        """An iterable of strings with the names of public methods (that don't start with an underscore)."""
        return sorted(n for n in self.methods if not n.startswith('_'))

    @lazy_property
    def required_hint(self):
        """A hint about required properties (a string or :data:`None`)."""
        names = sorted(name for name, value in self.custom_properties if value.required)
        if names:
            return compact(
                """
                When you initialize a :class:`{type}` object you are required
                to provide {values} for the {required} {properties}.
                """,
                type=self.type.__name__,
                required=self.format_properties(names),
                values=("a value" if len(names) == 1 else "values"),
                properties=("property" if len(names) == 1 else "properties"),
            )

    @lazy_property
    def special_methods(self):
        """An iterable of strings with the names of special methods (surrounded in double underscores)."""
        methods = sorted(name for name in self.methods if name.startswith('__') and name.endswith('__'))
        if '__init__' in methods:
            methods.remove('__init__')
            methods.insert(0, '__init__')
        return methods

    @required_property
    def type(self):
        """A subclass of :class:`.PropertyManager`."""

    def format_methods(self, names):
        """Format a list of method names as reStructuredText."""
        return concatenate(format(":func:`%s()`", n) for n in sorted(names))

    def format_properties(self, names):
        """Format a list of property names as reStructuredText."""
        return concatenate(format(":attr:`%s`", n) for n in sorted(names))
