from __future__ import unicode_literals

try:
    from twisted.internet import defer
except ImportError:
    class defer(object):
        """
        Fake "defer" object that allows us to use decorators in the main
        class file but that errors when it's attempted to be invoked.

        Used so you can import the client without Twisted but can't run
        without it.
        """

        @staticmethod
        def inlineCallbacks(func):
            def inner(*args, **kwargs):
                raise NotImplementedError("Twisted is not installed")
            return inner
