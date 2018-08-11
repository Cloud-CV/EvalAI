
monotonic
~~~~~~~~~

This module provides a ``monotonic()`` function which returns the
value (in fractional seconds) of a clock which never goes backwards.

On Python 3.3 or newer, ``monotonic`` will be an alias of
``time.monotonic`` from the standard library. On older versions,
it will fall back to an equivalent implementation:

+------------------+----------------------------------------+
| Linux, BSD, AIX  | ``clock_gettime(3)``                   |
+------------------+----------------------------------------+
| Windows          | ``GetTickCount`` or ``GetTickCount64`` |
+------------------+----------------------------------------+
| OS X             | ``mach_absolute_time``                 |
+------------------+----------------------------------------+

If no suitable implementation exists for the current platform,
attempting to import this module (or to import from it) will
cause a ``RuntimeError`` exception to be raised.



