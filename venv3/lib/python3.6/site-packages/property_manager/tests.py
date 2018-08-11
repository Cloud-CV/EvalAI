# Tests of custom properties for Python programming.
#
# Author: Peter Odding <peter@peterodding.com>
# Last Change: April 27, 2018
# URL: https://property-manager.readthedocs.org

"""Automated tests for the :mod:`property_manager` module."""

# Standard library modules.
import logging
import os
import random
import sys
import unittest

# External dependencies.
import coloredlogs
from humanfriendly import compact, format
from verboselogs import VerboseLogger

# Modules included in our package.
import property_manager
from property_manager import (
    CACHED_PROPERTY_NOTE,
    CUSTOM_PROPERTY_NOTE,
    DYNAMIC_PROPERTY_NOTE,
    ENVIRONMENT_PROPERTY_NOTE,
    REQUIRED_PROPERTY_NOTE,
    RESETTABLE_CACHED_PROPERTY_NOTE,
    RESETTABLE_WRITABLE_PROPERTY_NOTE,
    WRITABLE_PROPERTY_NOTE,
    PropertyManager,
    cached_property,
    custom_property,
    key_property,
    lazy_property,
    mutable_property,
    required_property,
    writable_property,
)
from property_manager.sphinx import TypeInspector, setup, append_property_docs

# Initialize a logger for this module.
logger = VerboseLogger(__name__)


class PropertyManagerTestCase(unittest.TestCase):

    """Container for the :mod:`property_manager` test suite."""

    def setUp(self):
        """Enable verbose logging and usage notes."""
        property_manager.USAGE_NOTES_ENABLED = True
        coloredlogs.install(level=logging.NOTSET)
        # Separate the name of the test method (printed by the superclass
        # and/or py.test without a newline at the end) from the first line of
        # logging output that the test method is likely going to generate.
        sys.stderr.write("\n")

    def test_builtin_property(self):
        """
        Test that our assumptions about the behavior of :class:`property` are correct.

        This test helps to confirm that :class:`PropertyInspector` (on which
        other tests are based) shows sane behavior regardless of whether a
        custom property is inspected.
        """
        class NormalPropertyTest(object):
            @property
            def normal_test_property(self):
                return random.random()
        with PropertyInspector(NormalPropertyTest, 'normal_test_property') as p:
            assert p.is_recognizable
            assert p.is_recomputed
            assert p.is_read_only
            assert not p.is_injectable

    def test_custom_property(self):
        """Test that :class:`.custom_property` works just like :class:`property`."""
        class CustomPropertyTest(object):
            @custom_property
            def custom_test_property(self):
                return random.random()
        with PropertyInspector(CustomPropertyTest, 'custom_test_property') as p:
            assert p.is_recognizable
            assert p.is_recomputed
            assert p.is_read_only
            assert not p.is_injectable
            p.check_usage_notes()
        # Test that custom properties expect a function argument and validate their assumption.
        self.assertRaises(ValueError, custom_property, None)

    def test_writable_property(self):
        """Test that :class:`.writable_property` supports assignment."""
        class WritablePropertyTest(object):
            @writable_property
            def writable_test_property(self):
                return random.random()
        with PropertyInspector(WritablePropertyTest, 'writable_test_property') as p:
            assert p.is_recognizable
            assert p.is_recomputed
            assert p.is_writable
            assert not p.is_resettable
            assert p.is_injectable
            p.check_usage_notes()

    def test_required_property(self):
        """Test that :class:`.required_property` performs validation."""
        class RequiredPropertyTest(PropertyManager):
            @required_property
            def required_test_property(self):
                pass
        with PropertyInspector(RequiredPropertyTest, 'required_test_property', required_test_property=42) as p:
            assert p.is_recognizable
            assert p.is_writable
            assert not p.is_resettable
            assert p.is_injectable
            p.check_usage_notes()
        # Test that required properties must be set using the constructor.
        self.assertRaises(TypeError, RequiredPropertyTest)

    def test_mutable_property(self):
        """Test that :class:`mutable_property` supports assignment and deletion."""
        class MutablePropertyTest(object):
            @mutable_property
            def mutable_test_property(self):
                return random.random()
        with PropertyInspector(MutablePropertyTest, 'mutable_test_property') as p:
            assert p.is_recognizable
            assert p.is_recomputed
            assert p.is_writable
            assert p.is_resettable
            assert p.is_injectable
            p.check_usage_notes()

    def test_lazy_property(self):
        """Test that :class:`lazy_property` caches computed values."""
        class LazyPropertyTest(object):
            @lazy_property
            def lazy_test_property(self):
                return random.random()
        with PropertyInspector(LazyPropertyTest, 'lazy_test_property') as p:
            assert p.is_recognizable
            assert p.is_cached
            assert p.is_read_only
            p.check_usage_notes()

    def test_cached_property(self):
        """Test that :class:`.cached_property` caches its result."""
        class CachedPropertyTest(object):
            @cached_property
            def cached_test_property(self):
                return random.random()
        with PropertyInspector(CachedPropertyTest, 'cached_test_property') as p:
            assert p.is_recognizable
            assert p.is_cached
            assert not p.is_writable
            assert p.is_resettable
            p.check_usage_notes()

    def test_environment_property(self):
        """Test that custom properties can be based on environment variables."""
        variable_name = 'PROPERTY_MANAGER_TEST_VALUE'

        class EnvironmentPropertyTest(object):
            @mutable_property(environment_variable=variable_name)
            def environment_test_property(self):
                return str(random.random())

        with PropertyInspector(EnvironmentPropertyTest, 'environment_test_property') as p:
            # Make sure the property's value can be overridden using the
            # expected environment variable.
            value_from_environment = str(random.random())
            os.environ[variable_name] = value_from_environment
            assert p.value == value_from_environment
            # Make sure assignment overrides the value from the environment.
            value_from_assignment = str(random.random())
            assert value_from_assignment != value_from_environment
            p.value = value_from_assignment
            assert p.value == value_from_assignment
            # Make sure the assigned value can be cleared so that the
            # property's value falls back to the environment variable.
            p.delete()
            assert p.value == value_from_environment
            # Make sure the property's value falls back to the computed value
            # if the environment variable isn't set.
            os.environ.pop(variable_name)
            assert p.value != value_from_assignment
            assert p.value != value_from_environment
            p.check_usage_notes()

    def test_property_manager_repr(self):
        """Test :func:`repr()` rendering of :class:`PropertyManager` objects."""
        class RepresentationTest(PropertyManager):
            @required_property
            def important(self):
                pass

            @mutable_property
            def optional(self):
                return 42
        instance = RepresentationTest(important=1)
        assert "important=1" in repr(instance)
        assert "optional=42" in repr(instance)

    def test_property_injection(self):
        """Test that :class:`.PropertyManager` raises an error for unknown properties."""
        class PropertyInjectionTest(PropertyManager):
            @mutable_property
            def injected_test_property(self):
                return 'default'
        assert PropertyInjectionTest().injected_test_property == 'default'
        assert PropertyInjectionTest(injected_test_property='injected').injected_test_property == 'injected'
        self.assertRaises(TypeError, PropertyInjectionTest, random_keyword_argument=True)

    def test_property_customization(self):
        """Test that :func:`.custom_property.__new__()` dynamically constructs subclasses."""
        class CustomizedPropertyTest(object):
            @custom_property(cached=True, writable=True)
            def customized_test_property(self):
                pass
        with PropertyInspector(CustomizedPropertyTest, 'customized_test_property') as p:
            assert p.is_recognizable
            assert p.is_cached
            assert p.is_writable

    def test_setters(self):
        """Test that custom properties support setters."""
        class SetterTest(object):

            @custom_property
            def setter_test_property(self):
                return getattr(self, 'whatever_you_want_goes_here', 42)

            @setter_test_property.setter
            def setter_test_property(self, value):
                if value < 0:
                    raise ValueError
                self.whatever_you_want_goes_here = value

        with PropertyInspector(SetterTest, 'setter_test_property') as p:
            # This is basically just testing the lazy property.
            assert p.is_recognizable
            assert p.value == 42
            # Test that the setter is being called by verifying
            # that it raises a value error on invalid arguments.
            self.assertRaises(ValueError, setattr, p, 'value', -5)
            # Test that valid values are actually set.
            p.value = 13
            assert p.value == 13

    def test_deleters(self):
        """Test that custom properties support deleters."""
        class DeleterTest(object):

            @custom_property
            def deleter_test_property(self):
                return getattr(self, 'whatever_you_want_goes_here', 42)

            @deleter_test_property.setter
            def deleter_test_property(self, value):
                self.whatever_you_want_goes_here = value

            @deleter_test_property.deleter
            def deleter_test_property(self):
                delattr(self, 'whatever_you_want_goes_here')

        with PropertyInspector(DeleterTest, 'deleter_test_property') as p:
            # This is basically just testing the custom property.
            assert p.is_recognizable
            assert p.value == 42
            # Make sure we can set a new value.
            p.value = 13
            assert p.value == 13
            # Make sure we can delete the value.
            p.delete()
            # Here we expect the computed value.
            assert p.value == 42

    def test_cache_invalidation(self):
        """Test that :func:`.PropertyManager.clear_cached_properties()` correctly clears cached property values."""
        class CacheInvalidationTest(PropertyManager):

            def __init__(self, counter):
                self.counter = counter

            @lazy_property
            def lazy(self):
                return self.counter * 2

            @cached_property
            def cached(self):
                return self.counter * 2

        instance = CacheInvalidationTest(42)
        # Test that the lazy property was calculated based on the input.
        assert instance.lazy == (42 * 2)
        # Test that the cached property was calculated based on the input.
        assert instance.cached == (42 * 2)
        # Invalidate the values of cached properties.
        instance.counter *= 2
        instance.clear_cached_properties()
        # Make sure the value of the lazy property *wasn't* cleared.
        assert instance.lazy == (42 * 2)
        # Make sure the value of the cached property *was* cleared.
        assert instance.cached == (42 * 2 * 2)

    def test_key_properties(self):
        """Test that :attr:`.PropertyManager.key_properties` reports only properties defined by subclasses."""
        class KeyPropertiesTest(PropertyManager):

            @key_property
            def one(self):
                return 1

            @key_property
            def two(self):
                return 2

        instance = KeyPropertiesTest()
        assert list(instance.key_properties) == ['one', 'two']
        assert instance.key_values == (('one', 1), ('two', 2))

    def test_hashable_objects(self):
        """Test that :attr:`.PropertyManager.__hash__` works properly."""
        class HashableObject(PropertyManager):

            @key_property
            def a(self):
                return 1

            @key_property
            def b(self):
                return 2

        # Create a set and put an object in it.
        collection = set()
        collection.add(HashableObject())
        assert len(collection) == 1
        # Add a second (identical) object (or not :-).
        collection.add(HashableObject())
        assert len(collection) == 1
        # Add a third (non-identical) object.
        collection.add(HashableObject(b=42))
        assert len(collection) == 2
        # Try to add an object with an unhashable property value.
        self.assertRaises(ValueError, HashableObject, b=[])

    def test_sortable_objects(self):
        """Test that the rich comparison methods work properly."""
        class SortableObject(PropertyManager):

            @key_property
            def a(self):
                return 1

            @key_property
            def b(self):
                return 2

        # Test the non-equality operator.
        assert SortableObject(a=1, b=2) != SortableObject(a=2, b=2)
        # Test the "less than" operator.
        assert SortableObject(a=1, b=2) < SortableObject(a=2, b=1)
        assert not SortableObject(a=2, b=1) < SortableObject(a=1, b=2)
        # Test the "less than or equal" operator.
        assert SortableObject(a=1, b=2) <= SortableObject(a=2, b=1)
        assert SortableObject(a=1, b=2) <= SortableObject(a=1, b=2)
        assert not SortableObject(a=2, b=1) <= SortableObject(a=1, b=2)
        # Test the "greater than" operator.
        assert SortableObject(a=2, b=1) > SortableObject(a=1, b=2)
        assert not SortableObject(a=1, b=2) > SortableObject(a=2, b=1)
        # Test the "greater than or equal" operator.
        assert SortableObject(a=2, b=1) >= SortableObject(a=1, b=2)
        assert SortableObject(a=2, b=1) >= SortableObject(a=2, b=1)
        assert not SortableObject(a=1, b=2) >= SortableObject(a=2, b=1)
        # Test comparison with arbitrary objects. This should not raise any
        # unexpected exceptions.
        instance = SortableObject()
        arbitrary_object = object()
        if sys.version_info[0] <= 2:
            # In Python 2 arbitrary objects "supported" rich comparison.
            assert instance >= arbitrary_object or instance <= arbitrary_object
        else:
            # Since Python 3 it raises a TypeError instead.
            self.assertRaises(TypeError, lambda: instance >= arbitrary_object or instance <= arbitrary_object)

    def test_sphinx_integration(self):
        """Tests for the :mod:`property_manager.sphinx` module."""
        class FakeApp(object):

            def __init__(self):
                self.callbacks = {}

            def connect(self, event, callback):
                self.callbacks.setdefault(event, []).append(callback)

        app = FakeApp()
        setup(app)
        assert append_property_docs in app.callbacks['autodoc-process-docstring']
        lines = ["Some boring description."]
        obj = TypeInspector
        append_property_docs(app=app, what=None, name=None, obj=obj, options=None, lines=lines)
        assert len(lines) > 0
        assert lines[0] == "Some boring description."
        assert not lines[1]
        assert lines[2] == compact("""
            When you initialize a :class:`TypeInspector` object you are
            required to provide a value for the :attr:`type` property. You can
            set the value of the :attr:`type` property by passing a keyword
            argument to the class initializer.
        """)
        assert not lines[3]
        assert lines[4] == "Here's an overview of the :class:`TypeInspector` class:"

    def test_init_sorting(self):
        """Make sure __init__() is sorted before other special methods."""
        inspector = TypeInspector(type=PropertyInspector)
        assert inspector.special_methods[0] == '__init__'


class PropertyInspector(object):

    """Introspecting properties with properties (turtles all the way down)."""

    def __init__(self, owner, name, *args, **kw):
        """
        Initialize a :class:`PropertyInspector` object.

        :param owner: The class that owns the property.
        :param name: The name of the property (a string).
        :param args: Any positional arguments needed to initialize an instance
                     of the owner class.
        :param kw: Any keyword arguments needed to initialize an instance of
                   the owner class.
        """
        self.owner_object = owner(*args, **kw)
        self.owner_type = owner
        self.property_name = name
        self.property_object = getattr(owner, name)
        self.property_type = self.property_object.__class__

    def __enter__(self):
        """Enable the syntax of context managers."""
        return self

    def __exit__(self, exc_type=None, exc_value=None, traceback=None):
        """Enable the syntax of context managers."""
        pass

    @property
    def value(self):
        """Get the value of the property from the owner's instance."""
        return getattr(self.owner_object, self.property_name)

    @value.setter
    def value(self, new_value):
        """Set the value of the property on the owner's instance."""
        setattr(self.owner_object, self.property_name, new_value)

    def delete(self):
        """Delete the (value of the) property."""
        delattr(self.owner_object, self.property_name)

    @property
    def is_recognizable(self):
        """
        :data:`True` if the property can be easily recognized, :data:`False` otherwise.

        This function confirms that custom properties subclass Python's built
        in :class:`property` class so that introspection of class members using
        :func:`isinstance()` correctly recognizes properties as such, even for
        code which is otherwise unaware of the custom properties defined by the
        :mod:`property_manager` module.
        """
        return isinstance(self.property_object, property)

    @property
    def is_recomputed(self):
        """:data:`True` if the property is recomputed each time, :data:`False` otherwise."""
        return not self.is_cached

    @property
    def is_cached(self):
        """:data:`True` if the property is cached (not recomputed), :data:`False` otherwise."""
        class CachedPropertyTest(object):
            @self.property_type
            def value(self):
                return random.random()
        obj = CachedPropertyTest()
        return (obj.value == obj.value)

    @property
    def is_read_only(self):
        """:data:`True` if the property is read only, :data:`False` otherwise."""
        return not self.is_writable and not self.is_resettable

    @property
    def is_writable(self):
        """:data:`True` if the property supports assignment, :data:`False` otherwise."""
        unique_value = object()
        try:
            setattr(self.owner_object, self.property_name, unique_value)
            return getattr(self.owner_object, self.property_name) is unique_value
        except AttributeError:
            return False

    @property
    def is_resettable(self):
        """:data:`True` if the property can be reset to its computed value, :data:`False` otherwise."""
        try:
            delattr(self.owner_object, self.property_name)
            return True
        except AttributeError:
            return False

    @property
    def is_injectable(self):
        """:data:`True` if the property can be set via the owner's constructor, :data:`False` otherwise."""
        initial_value = object()
        injected_value = object()
        try:
            class PropertyOwner(PropertyManager):
                @self.property_type
                def test_property(self):
                    return initial_value
            clean_instance = PropertyOwner()
            injected_instance = PropertyOwner(test_property=injected_value)
            return clean_instance.test_property is initial_value and injected_instance.test_property is injected_value
        except AttributeError:
            return False

    def check_usage_notes(self):
        """Check whether the correct notes are embedded in the documentation."""
        class DocumentationTest(object):
            @self.property_type
            def documented_property(self):
                """Documentation written by the author."""
                return random.random()
        documentation = DocumentationTest.documented_property.__doc__
        # Test that the sentence added for custom properties is always present.
        cls = custom_property if self.property_type.dynamic else self.property_type
        custom_property_note = format(
            DYNAMIC_PROPERTY_NOTE if self.property_type.dynamic else CUSTOM_PROPERTY_NOTE,
            name='documented_property', type="%s.%s" % (cls.__module__, cls.__name__),
        )
        if DocumentationTest.documented_property.usage_notes:
            assert custom_property_note in documentation
        else:
            assert custom_property_note not in documentation
            # If CUSTOM_PROPERTY_NOTE is not present we assume that none of the
            # other usage notes will be present either.
            return
        # Test that the sentence added for writable properties is present when applicable.
        assert self.property_type.writable == (WRITABLE_PROPERTY_NOTE in documentation)
        # Test that the sentence added for cached properties is present when applicable.
        assert self.property_type.cached == (CACHED_PROPERTY_NOTE in documentation)
        # Test that the sentence added for resettable properties is present when applicable.
        if self.is_resettable:
            assert self.is_cached == (RESETTABLE_CACHED_PROPERTY_NOTE in documentation)
            assert self.is_writable == (RESETTABLE_WRITABLE_PROPERTY_NOTE in documentation)
        else:
            assert RESETTABLE_CACHED_PROPERTY_NOTE not in documentation
            assert RESETTABLE_WRITABLE_PROPERTY_NOTE not in documentation
        # Test that the sentence added for required properties is present when applicable.
        required_property_note = format(REQUIRED_PROPERTY_NOTE, name='documented_property')
        assert self.property_type.required == (required_property_note in documentation)
        # Test that the sentence added for environment properties is present when applicable.
        environment_note = format(ENVIRONMENT_PROPERTY_NOTE, variable=self.property_type.environment_variable)
        assert bool(self.property_type.environment_variable) == (environment_note in documentation)
