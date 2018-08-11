# Useful property variants for Python programming.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: May 19, 2018
# URL: https://property-manager.readthedocs.org

"""
Useful :class:`property` variants for Python programming.

Introduction
============

The :mod:`property_manager` module defines several :class:`property` variants
that implement Python's `descriptor protocol`_ to provide decorators that turn
methods into computed properties with several additional features.

Custom property types
---------------------

Here's an overview of the predefined property variants and their supported
operations:

==========================  ==========  ============  ==========  =======
Variant                     Assignment  Reassignment  Deletion    Caching
==========================  ==========  ============  ==========  =======
:class:`custom_property`    No          No            No          No
:class:`writable_property`  Yes         Yes           No          No
:class:`mutable_property`   Yes         Yes           Yes         No
:class:`required_property`  Yes         Yes           No          No
:class:`key_property`       Yes         No            No          No
:class:`lazy_property`      No          No            No          Yes
:class:`cached_property`    No          No            Yes         Yes
==========================  ==========  ============  ==========  =======

If you want a different combination of supported options (for example a cached
property that supports assignment) this is also possible, please take a look at
:class:`custom_property.__new__()`.

The following inheritance diagram shows how the predefined :class:`property`
variants relate to each other:

.. inheritance-diagram:: property_manager.custom_property \
                         property_manager.writable_property \
                         property_manager.mutable_property \
                         property_manager.required_property \
                         property_manager.key_property \
                         property_manager.lazy_property \
                         property_manager.cached_property
   :parts: 1

The property manager superclass
-------------------------------

In addition to these :class:`property` variants the :mod:`property_manager`
module also defines a :class:`PropertyManager` class which implements several
related enhancements:

- Keyword arguments to the constructor can be used to set writable properties
  created using any of the :class:`property` variants defined by the
  :mod:`property_manager` module.

- Required properties without an assigned value will cause the constructor
  to raise an appropriate exception (:exc:`~exceptions.TypeError`).

- The :func:`repr()` of :class:`PropertyManager` objects shows the names and
  values of all properties. Individual properties can be omitted from the
  :func:`repr()` output by setting the :attr:`~custom_property.repr` option to
  :data:`False`.

Logging
=======

The :mod:`property_manager` module emits log messages at the custom log level
:data:`~verboselogs.SPAM` which is considered *more* verbose than
:data:`~logging.DEBUG`, so if you want these messages to be logged
make sure they're not being ignored based on their level.

Classes
=======

.. _descriptor protocol: https://docs.python.org/2/howto/descriptor.html
"""

# Standard library modules.
import collections
import os
import sys
import textwrap

# External dependencies.
from humanfriendly import coerce_boolean, compact, concatenate, format, pluralize
from verboselogs import VerboseLogger

try:
    # Check if `basestring' is defined (Python 2).
    basestring = basestring
except NameError:
    # Alias basestring to str in Python 3.
    basestring = str

__version__ = '2.3.1'
"""Semi-standard module versioning."""

SPHINX_ACTIVE = 'sphinx' in sys.modules
"""
:data:`True` when Sphinx_ is running, :data:`False` otherwise.

We detect whether Sphinx is running by checking for the presence of the
'sphinx' key in :data:`sys.modules`. The result determines the default
value of :data:`USAGE_NOTES_ENABLED`.
"""

USAGE_NOTES_VARIABLE = 'PROPERTY_MANAGER_USAGE_NOTES'
"""The name of the environment variable that controls whether usage notes are enabled (a string)."""

USAGE_NOTES_ENABLED = (coerce_boolean(os.environ[USAGE_NOTES_VARIABLE])
                       if USAGE_NOTES_VARIABLE in os.environ
                       else SPHINX_ACTIVE)
"""
:data:`True` if usage notes are enabled, :data:`False` otherwise.

This defaults to the environment variable :data:`USAGE_NOTES_VARIABLE` (coerced
using :func:`~humanfriendly.coerce_boolean()`) when available, otherwise
:data:`SPHINX_ACTIVE` determines the default value.

Usage notes are only injected when Sphinx is running because of performance.
It's nothing critical of course, but modifying hundreds or thousands of
docstrings that no one is going to look at seems rather pointless :-).
"""

NOTHING = object()
"""A unique object instance used to detect missing attributes."""

CUSTOM_PROPERTY_NOTE = compact("""
    The :attr:`{name}` property is a :class:`~{type}`.
""")

DYNAMIC_PROPERTY_NOTE = compact("""
    The :attr:`{name}` property is a :class:`~{type}`.
""")

ENVIRONMENT_PROPERTY_NOTE = compact("""
    If the environment variable ``${variable}`` is set it overrides the
    computed value of this property.
""")

REQUIRED_PROPERTY_NOTE = compact("""
    You are required to provide a value for this property by calling the
    constructor of the class that defines the property with a keyword argument
    named `{name}` (unless a custom constructor is defined, in this case please
    refer to the documentation of that constructor).
""")

KEY_PROPERTY_NOTE = compact("""
    Once this property has been assigned a value you are not allowed to assign
    a new value to the property.
""")

WRITABLE_PROPERTY_NOTE = compact("""
    You can change the value of this property using normal attribute assignment
    syntax.
""")

CACHED_PROPERTY_NOTE = compact("""
    This property's value is computed once (the first time it is accessed) and
    the result is cached.
""")

RESETTABLE_CACHED_PROPERTY_NOTE = compact("""
    To clear the cached value you can use :keyword:`del` or
    :func:`delattr()`.
""")

RESETTABLE_WRITABLE_PROPERTY_NOTE = compact("""
    To reset it to its default (computed) value you can use :keyword:`del` or
    :func:`delattr()`.
""")

# Initialize a logger for this module.
logger = VerboseLogger(__name__)


def set_property(obj, name, value):
    """
    Set or override the value of a property.

    :param obj: The object that owns the property.
    :param name: The name of the property (a string).
    :param value: The new value for the property.

    This function directly modifies the :attr:`~object.__dict__` of the given
    object and as such it avoids any interaction with object properties. This
    is intentional: :func:`set_property()` is meant to be used by extensions of
    the `property-manager` project and by user defined setter methods.
    """
    logger.spam("Setting value of %s property to %r ..", format_property(obj, name), value)
    obj.__dict__[name] = value


def clear_property(obj, name):
    """
    Clear the assigned or cached value of a property.

    :param obj: The object that owns the property.
    :param name: The name of the property (a string).

    This function directly modifies the :attr:`~object.__dict__` of the given
    object and as such it avoids any interaction with object properties. This
    is intentional: :func:`clear_property()` is meant to be used by extensions
    of the `property-manager` project and by user defined deleter methods.
    """
    logger.spam("Clearing value of %s property ..", format_property(obj, name))
    obj.__dict__.pop(name, None)


def format_property(obj, name):
    """
    Format an object property's dotted name.

    :param obj: The object that owns the property.
    :param name: The name of the property (a string).
    :returns: The dotted path (a string).
    """
    return "%s.%s" % (obj.__class__.__name__, name)


class PropertyManager(object):

    """
    Optional superclass for classes that use the computed properties from this module.

    Provides support for required properties, setting of properties in the
    constructor and generating a useful textual representation of objects with
    properties.
    """

    def __init__(self, **kw):
        """
        Initialize a :class:`PropertyManager` object.

        :param kw: Any keyword arguments are passed on to :func:`set_properties()`.
        """
        self.set_properties(**kw)
        missing_properties = self.missing_properties
        if missing_properties:
            msg = "missing %s" % pluralize(len(missing_properties), "required argument")
            raise TypeError("%s (%s)" % (msg, concatenate(missing_properties)))

    def set_properties(self, **kw):
        """
        Set instance properties from keyword arguments.

        :param kw: Every keyword argument is used to assign a value to the
                   instance property whose name matches the keyword argument.
        :raises: :exc:`~exceptions.TypeError` when a keyword argument doesn't
                 match a :class:`property` on the given object.
        """
        for name, value in kw.items():
            if self.have_property(name):
                setattr(self, name, value)
            else:
                msg = "got an unexpected keyword argument %r"
                raise TypeError(msg % name)

    @property
    def key_properties(self):
        """A sorted list of strings with the names of any :attr:`~custom_property.key` properties."""
        return self.find_properties(key=True)

    @property
    def key_values(self):
        """A tuple of tuples with (name, value) pairs for each name in :attr:`key_properties`."""
        return tuple((name, getattr(self, name)) for name in self.key_properties)

    @property
    def missing_properties(self):
        """
        The names of key and/or required properties that are missing.

        This is a list of strings with the names of key and/or required
        properties that either haven't been set or are set to :data:`None`.
        """
        names = sorted(set(self.required_properties) | set(self.key_properties))
        return [n for n in names if getattr(self, n, None) is None]

    @property
    def repr_properties(self):
        """
        The names of the properties rendered by :func:`__repr__()` (a list of strings).

        When :attr:`key_properties` is nonempty the names of the key properties
        are returned, otherwise a more complex selection is made (of properties
        defined by subclasses of :class:`PropertyManager` whose
        :attr:`~custom_property.repr` is :data:`True`).
        """
        return self.key_properties or [
            name for name in self.find_properties(repr=True)
            if not hasattr(PropertyManager, name)
        ]

    @property
    def required_properties(self):
        """A sorted list of strings with the names of any :attr:`~custom_property.required` properties."""
        return self.find_properties(required=True)

    def find_properties(self, **options):
        """
        Find an object's properties (of a certain type).

        :param options: Passed on to :func:`have_property()` to enable
                        filtering properties by the operations they support.
        :returns: A sorted list of strings with the names of properties.
        """
        # We don't explicitly sort our results here because the dir() function
        # is documented to sort its results alphabetically.
        return [n for n in dir(self) if self.have_property(n, **options)]

    def have_property(self, name, **options):
        """
        Check if the object has a property (of a certain type).

        :param name: The name of the property (a string).
        :param options: Any keyword arguments give the name of an option
                        (one of :attr:`~custom_property.writable`,
                        :attr:`~custom_property.resettable`,
                        :attr:`~custom_property.cached`,
                        :attr:`~custom_property.required`,
                        :attr:`~custom_property.key`,
                        :attr:`~custom_property.repr`) and an expected value
                        (:data:`True` or :data:`False`). Filtering on more than
                        one option is supported.
        :returns: :data:`True` if the object has a property with the expected
                  options enabled/disabled, :data:`False` otherwise.
        """
        property_type = getattr(self.__class__, name, None)
        if isinstance(property_type, property):
            if options:
                return all(getattr(property_type, n, None) == v or
                           n == 'repr' and v is True and getattr(property_type, n, None) is not False
                           for n, v in options.items())
            else:
                return True
        else:
            return False

    def clear_cached_properties(self):
        """Clear cached properties so that their values are recomputed."""
        for name in self.find_properties(cached=True, resettable=True):
            delattr(self, name)

    def render_properties(self, *names):
        """
        Render a human friendly string representation of an object with computed properties.

        :param names: Each positional argument gives the name of a property
                      to include in the rendered object representation.
        :returns: The rendered object representation (a string).

        This method generates a user friendly textual representation for
        objects that use computed properties created using the
        :mod:`property_manager` module.
        """
        fields = []
        for name in names:
            value = getattr(self, name, None)
            if value is not None or name in self.key_properties:
                fields.append("%s=%r" % (name, value))
        return "%s(%s)" % (self.__class__.__name__, ", ".join(fields))

    def __eq__(self, other):
        """Enable equality comparison and hashing for :class:`PropertyManager` subclasses."""
        our_key = self.key_values
        return (our_key == other.key_values
                if our_key and isinstance(other, PropertyManager)
                else NotImplemented)

    def __ne__(self, other):
        """Enable non-equality comparison for :class:`PropertyManager` subclasses."""
        our_key = self.key_values
        return (our_key != other.key_values
                if our_key and isinstance(other, PropertyManager)
                else NotImplemented)

    def __lt__(self, other):
        """Enable "less than" comparison for :class:`PropertyManager` subclasses."""
        our_key = self.key_values
        return (our_key < other.key_values
                if our_key and isinstance(other, PropertyManager)
                else NotImplemented)

    def __le__(self, other):
        """Enable "less than or equal" comparison for :class:`PropertyManager` subclasses."""
        our_key = self.key_values
        return (our_key <= other.key_values
                if our_key and isinstance(other, PropertyManager)
                else NotImplemented)

    def __gt__(self, other):
        """Enable "greater than" comparison for :class:`PropertyManager` subclasses."""
        our_key = self.key_values
        return (our_key > other.key_values
                if our_key and isinstance(other, PropertyManager)
                else NotImplemented)

    def __ge__(self, other):
        """Enable "greater than or equal" comparison for :class:`PropertyManager` subclasses."""
        our_key = self.key_values
        return (our_key >= other.key_values
                if our_key and isinstance(other, PropertyManager)
                else NotImplemented)

    def __hash__(self):
        """
        Enable hashing for :class:`PropertyManager` subclasses.

        This method makes it possible to add :class:`PropertyManager` objects
        to sets and use them as dictionary keys. The hashes computed by this
        method are based on the values in :attr:`key_values`.
        """
        return hash(PropertyManager) ^ hash(self.key_values)

    def __repr__(self):
        """
        Render a human friendly string representation of an object with computed properties.

        :returns: The rendered object representation (a string).

        This method uses :func:`render_properties()` to render the properties
        whose names are given by :attr:`repr_properties`. When the object
        doesn't have any key properties, :func:`__repr__()` assumes that
        all of the object's properties are idempotent and may be evaluated
        at any given time without worrying too much about performance (refer
        to the :attr:`~custom_property.repr` option for an escape hatch).
        """
        return self.render_properties(*self.repr_properties)


class custom_property(property):

    """
    Custom :class:`property` subclass that supports additional features.

    The :class:`custom_property` class implements Python's `descriptor
    protocol`_ to provide a decorator that turns methods into computed
    properties with several additional features.

    .. _descriptor protocol: https://docs.python.org/2/howto/descriptor.html

    The additional features are controlled by attributes defined on the
    :class:`custom_property` class. These attributes (documented below) are
    intended to be changed by the constructor (:func:`__new__()`) and/or
    classes that inherit from :class:`custom_property`.
    """

    cached = False
    """
    If this attribute is set to :data:`True` the property's value is computed
    only once and then cached in an object's :attr:`~object.__dict__`. The next
    time you access the attribute's value the cached value is automatically
    returned. By combining the :attr:`cached` and :attr:`resettable` options
    you get a cached property whose cached value can be cleared. If the value
    should never be recomputed then don't enable the :attr:`resettable`
    option.

    :see also: :class:`cached_property` and :class:`lazy_property`.
    """

    dynamic = False
    """
    :data:`True` when the :class:`custom_property` subclass was dynamically
    constructed by :func:`__new__()`, :data:`False` otherwise. Used by
    :func:`compose_usage_notes()` to decide whether to link to the
    documentation of the subclass or not (because it's impossible to link to
    anonymous classes).
    """

    environment_variable = None
    """
    If this attribute is set to the name of an environment variable the
    property's value will default to the value of the environment variable. If
    the environment variable isn't set the property falls back to its computed
    value.
    """

    key = False
    """
    If this attribute is :data:`True` the property's name is included in the
    value of :attr:`~PropertyManager.key_properties` which means that the
    property's value becomes part of the "key" that is used to compare, sort
    and hash :class:`PropertyManager` objects. There are a few things to be
    aware of with regards to key properties and their values:

    - The property's value must be set during object initialization (the same
      as for :attr:`required` properties) and it cannot be changed after it is
      initially assigned a value (because allowing this would "compromise"
      the results of the :func:`~PropertyManager.__hash__()` method).
    - The property's value must be hashable (otherwise it can't be used by the
      :func:`~PropertyManager.__hash__()` method).

    :see also: :class:`key_property`.
    """

    repr = True
    """
    By default :func:`PropertyManager.__repr__()` includes the names and values
    of all properties that aren't :data:`None` in :func:`repr()` output. If you
    want to omit a certain property you can set :attr:`repr` to :data:`False`.

    Examples of why you would want to do this include property values that
    contain secrets or are expensive to calculate and data structures with
    cycles which cause :func:`repr()` to die a slow and horrible death :-).
    """

    required = False
    """
    If this attribute is set to :data:`True` the property requires a value to
    be set during the initialization of the object that owns the property. For
    this to work the class that owns the property needs to inherit from
    :class:`PropertyManager`.

    :see also: :class:`required_property`.

    The constructor of :class:`PropertyManager` will ensure that required
    properties are set to values that aren't :data:`None`. Required properties
    must be set by providing keyword arguments to the constructor of the class
    that inherits from :class:`PropertyManager`. When
    :func:`PropertyManager.__init__()` notices that required properties haven't
    been set it raises a :exc:`~exceptions.TypeError` similar to the type error
    raised by Python when required arguments are missing in a function call.
    Here's an example:

    .. code-block:: python

       from property_manager import PropertyManager, required_property, mutable_property

       class Example(PropertyManager):

           @required_property
           def important(self):
               "A very important attribute."

           @mutable_property
           def optional(self):
               "A not so important attribute."
               return 13

    Let's construct an instance of the class defined above:

    >>> Example()
    Traceback (most recent call last):
      File "property_manager/__init__.py", line 107, in __init__
        raise TypeError("%s (%s)" % (msg, concatenate(missing_properties)))
    TypeError: missing 1 required argument ('important')

    As expected it complains that a required property hasn't been
    initialized. Here's how it's supposed to work:

    >>> Example(important=42)
    Example(important=42, optional=13)
    """

    resettable = False
    """
    If this attribute is set to :data:`True` the property can be reset to its
    default or computed value using :keyword:`del` and :func:`delattr()`. This
    works by removing the assigned or cached value from the object's
    :attr:`~object.__dict__`.

    :see also: :class:`mutable_property` and :class:`cached_property`.
    """

    usage_notes = True
    """
    If this attribute is :data:`True` :func:`inject_usage_notes()` is used to
    inject usage notes into the documentation of the property. You can set this
    attribute to :data:`False` to disable :func:`inject_usage_notes()`.
    """

    writable = False
    """
    If this attribute is set to :data:`True` the property supports assignment.
    The assigned value is stored in the :attr:`~object.__dict__` of the object
    that owns the property.

    :see also: :class:`writable_property`, :class:`mutable_property` and
               :class:`required_property`.

    A relevant note about how Python looks up attributes: When an attribute is
    looked up and exists in an object's :attr:`~object.__dict__` Python ignores
    any property (descriptor) by the same name and immediately returns the
    value that was found in the object's :attr:`~object.__dict__`.
    """

    def __new__(cls, *args, **options):
        """
        Constructor for :class:`custom_property` subclasses and instances.

        To construct a subclass:

        :param args: The first positional argument is used as the name of the
                     subclass (defaults to 'customized_property').
        :param options: Each keyword argument gives the name of an option
                        (:attr:`writable`, :attr:`resettable`, :attr:`cached`,
                        :attr:`required`, :attr:`environment_variable`,
                        :attr:`repr`) and the value to use for that option
                        (:data:`True`, :data:`False` or a string).
        :returns: A dynamically constructed subclass of
                  :class:`custom_property` with the given options.

        To construct an instance:

        :param args: The first positional argument is the function that's
                     called to compute the value of the property.
        :returns: A :class:`custom_property` instance corresponding to the
                  class whose constructor was called.

        Here's an example of how the subclass constructor can be used to
        dynamically construct custom properties with specific options:

        .. code-block:: python

           from property_manager import custom_property

           class WritableCachedPropertyDemo(object):

               @custom_property(cached=True, writable=True)
               def customized_test_property(self):
                   return 42

        The example above defines and uses a property whose computed value is
        cached and which supports assignment of new values. The example could
        have been made even simpler:

        .. code-block:: python

           from property_manager import cached_property

           class WritableCachedPropertyDemo(object):

               @cached_property(writable=True)
               def customized_test_property(self):
                   return 42

        Basically you can take any of the custom property classes defined in
        the :mod:`property_manager` module and call the class with keyword
        arguments corresponding to the options you'd like to change.
        """
        if options:
            # Keyword arguments construct subclasses.
            name = args[0] if args else 'customized_property'
            options['dynamic'] = True
            return type(name, (cls,), options)
        else:
            # Positional arguments construct instances.
            return super(custom_property, cls).__new__(cls, *args)

    def __init__(self, *args, **kw):
        """
        Initialize a :class:`custom_property` object.

        :param args: Any positional arguments are passed on to the initializer
                     of the :class:`property` class.
        :param kw: Any keyword arguments are passed on to the initializer of
                   the :class:`property` class.

        Automatically calls :func:`inject_usage_notes()` during initialization
        (only if :data:`USAGE_NOTES_ENABLED` is :data:`True`).
        """
        # It's not documented so I went to try it out and apparently the
        # property class initializer performs absolutely no argument
        # validation. The first argument doesn't have to be a callable,
        # in fact none of the arguments are even mandatory?! :-P
        super(custom_property, self).__init__(*args, **kw)
        # Explicit is better than implicit so I'll just go ahead and check
        # whether the value(s) given by the user make sense :-).
        self.ensure_callable('fget')
        # We only check the 'fset' and 'fdel' values when they are not None
        # because both of these arguments are supposed to be optional :-).
        for name in 'fset', 'fdel':
            if getattr(self, name) is not None:
                self.ensure_callable(name)
        # Copy some important magic members from the decorated method.
        for name in '__doc__', '__module__', '__name__':
            value = getattr(self.fget, name, None)
            if value is not None:
                setattr(self, name, value)
        # Inject usage notes when running under Sphinx.
        if USAGE_NOTES_ENABLED:
            self.inject_usage_notes()

    def ensure_callable(self, role):
        """
        Ensure that a decorated value is in fact callable.

        :param role: The value's role (one of 'fget', 'fset' or 'fdel').
        :raises: :exc:`exceptions.ValueError` when the value isn't callable.
        """
        value = getattr(self, role)
        if not callable(value):
            msg = "Invalid '%s' value! (expected callable, got %r instead)"
            raise ValueError(msg % (role, value))

    def inject_usage_notes(self):
        """
        Inject the property's semantics into its documentation.

        Calls :func:`compose_usage_notes()` to get a description of the property's
        semantics and appends this to the property's documentation. If the
        property doesn't have documentation it will not be added.
        """
        if self.usage_notes and self.__doc__ and isinstance(self.__doc__, basestring):
            notes = self.compose_usage_notes()
            if notes:
                self.__doc__ = "\n\n".join([
                    textwrap.dedent(self.__doc__),
                    ".. note:: %s" % " ".join(notes),
                ])

    def compose_usage_notes(self):
        """
        Get a description of the property's semantics to include in its documentation.

        :returns: A list of strings describing the semantics of the
                  :class:`custom_property` in reStructuredText_ format with
                  Sphinx_ directives.

        .. _reStructuredText: https://en.wikipedia.org/wiki/ReStructuredText
        .. _Sphinx: http://sphinx-doc.org/
        """
        template = DYNAMIC_PROPERTY_NOTE if self.dynamic else CUSTOM_PROPERTY_NOTE
        cls = custom_property if self.dynamic else self.__class__
        dotted_path = "%s.%s" % (cls.__module__, cls.__name__)
        notes = [format(template, name=self.__name__, type=dotted_path)]
        if self.environment_variable:
            notes.append(format(ENVIRONMENT_PROPERTY_NOTE, variable=self.environment_variable))
        if self.required:
            notes.append(format(REQUIRED_PROPERTY_NOTE, name=self.__name__))
        if self.key:
            notes.append(KEY_PROPERTY_NOTE)
        if self.writable:
            notes.append(WRITABLE_PROPERTY_NOTE)
        if self.cached:
            notes.append(CACHED_PROPERTY_NOTE)
        if self.resettable:
            if self.cached:
                notes.append(RESETTABLE_CACHED_PROPERTY_NOTE)
            else:
                notes.append(RESETTABLE_WRITABLE_PROPERTY_NOTE)
        return notes

    def __get__(self, obj, type=None):
        """
        Get the assigned, cached or computed value of the property.

        :param obj: The instance that owns the property.
        :param type: The class that owns the property.
        :returns: The value of the property.
        """
        if obj is None:
            # Called to get the attribute of the class.
            return self
        else:
            # Called to get the attribute of an instance. We calculate the
            # property's dotted name here once to minimize string creation.
            dotted_name = format_property(obj, self.__name__)
            if self.key or self.writable or self.cached:
                # Check if a value has been assigned or cached.
                value = obj.__dict__.get(self.__name__, NOTHING)
                if value is not NOTHING:
                    logger.spam("%s reporting assigned or cached value (%r) ..", dotted_name, value)
                    return value
            # Check if the property has an environment variable. We do this
            # after checking for an assigned value so that the `writable' and
            # `environment_variable' options can be used together.
            if self.environment_variable:
                value = os.environ.get(self.environment_variable, NOTHING)
                if value is not NOTHING:
                    logger.spam("%s reporting value from environment variable (%r) ..", dotted_name, value)
                    return value
            # Compute the property's value.
            value = super(custom_property, self).__get__(obj, type)
            logger.spam("%s reporting computed value (%r) ..", dotted_name, value)
            if self.cached:
                # Cache the computed value.
                logger.spam("%s caching computed value ..", dotted_name)
                set_property(obj, self.__name__, value)
            return value

    def __set__(self, obj, value):
        """
        Override the computed value of the property.

        :param obj: The instance that owns the property.
        :param value: The new value for the property.
        :raises: :exc:`~exceptions.AttributeError` if :attr:`writable` is
                 :data:`False`.
        """
        # Calculate the property's dotted name only once.
        dotted_name = format_property(obj, self.__name__)
        # Evaluate the property's setter (if any).
        try:
            logger.spam("%s calling setter with value %r ..", dotted_name, value)
            super(custom_property, self).__set__(obj, value)
        except AttributeError:
            logger.spam("%s setter raised attribute error, falling back.", dotted_name)
            if self.writable:
                # Override a computed or previously assigned value.
                logger.spam("%s overriding computed value to %r ..", dotted_name, value)
                set_property(obj, self.__name__, value)
            else:
                # Check if we're setting a key property during initialization.
                if self.key and obj.__dict__.get(self.__name__, None) is None:
                    # Make sure we were given a hashable value.
                    if not isinstance(value, collections.Hashable):
                        msg = "Invalid value for key property '%s'! (expected hashable object, got %r instead)"
                        raise ValueError(msg % (self.__name__, value))
                    # Set the key property's value.
                    logger.spam("%s setting initial value to %r ..", dotted_name, value)
                    set_property(obj, self.__name__, value)
                else:
                    # Refuse to override the computed value.
                    msg = "%r object attribute %r is read-only"
                    raise AttributeError(msg % (obj.__class__.__name__, self.__name__))

    def __delete__(self, obj):
        """
        Reset the assigned or cached value of the property.

        :param obj: The instance that owns the property.
        :raises: :exc:`~exceptions.AttributeError` if :attr:`resettable` is
                 :data:`False`.

        Once the property has been deleted the next read will evaluate the
        decorated function to compute the value.
        """
        # Calculate the property's dotted name only once.
        dotted_name = format_property(obj, self.__name__)
        # Evaluate the property's deleter (if any).
        try:
            logger.spam("%s calling deleter ..", dotted_name)
            super(custom_property, self).__delete__(obj)
        except AttributeError:
            logger.spam("%s deleter raised attribute error, falling back.", dotted_name)
            if self.resettable:
                # Reset the computed or overridden value.
                logger.spam("%s clearing assigned or computed value ..", dotted_name)
                clear_property(obj, self.__name__)
            else:
                msg = "%r object attribute %r is read-only"
                raise AttributeError(msg % (obj.__class__.__name__, self.__name__))


class writable_property(custom_property):

    """
    A computed property that supports assignment.

    This is a variant of :class:`custom_property`
    that has the :attr:`~custom_property.writable`
    option enabled by default.
    """

    writable = True


class required_property(writable_property):

    """
    A property that requires a value to be set.

    This is a variant of :class:`writable_property` that has the
    :attr:`~custom_property.required` option enabled by default. Refer to the
    documentation of the :attr:`~custom_property.required` option for an
    example.
    """

    required = True


class key_property(custom_property):

    """
    A property whose value is used for comparison and hashing.

    This is a variant of :class:`custom_property` that has the
    :attr:`~custom_property.key` and :attr:`~custom_property.required`
    options enabled by default.
    """

    key = True
    required = True


class mutable_property(writable_property):

    """
    A computed property that can be assigned and reset.

    This is a variant of :class:`writable_property` that
    has the :attr:`~custom_property.resettable`
    option enabled by default.
    """

    resettable = True


class lazy_property(custom_property):

    """
    A computed property whose value is computed once and cached.

    This is a variant of :class:`custom_property` that
    has the :attr:`~custom_property.cached`
    option enabled by default.
    """

    cached = True


class cached_property(lazy_property):

    """
    A computed property whose value is computed once and cached, but can be reset.

    This is a variant of :class:`lazy_property` that
    has the :attr:`~custom_property.resettable`
    option enabled by default.
    """

    resettable = True
