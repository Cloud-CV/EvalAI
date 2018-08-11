asgi_redis
==========

.. image:: https://api.travis-ci.org/django/asgi_redis.svg
    :target: https://travis-ci.org/django/asgi_redis

.. image:: https://img.shields.io/pypi/v/asgi_redis.svg
    :target: https://pypi.python.org/pypi/asgi_redis

An ASGI channel layer that uses Redis as its backing store, and supports
both a single-server and sharded configurations, as well as group support.


Usage
-----

You'll need to instantiate the channel layer with at least ``hosts``,
and other options if you need them.

Example:

.. code-block:: python

    channel_layer = RedisChannelLayer(
        host="redis",
        db=4,
        channel_capacity={
            "http.request": 200,
            "http.response*": 10,
        }
    )

``hosts``
~~~~~~~~~

The server(s) to connect to, as either URIs or ``(host, port)`` tuples. Defaults to ``['localhost', 6379]``. Pass multiple hosts to enable sharding, but note that changing the host list will lose some sharded data.

``prefix``
~~~~~~~~~~

Prefix to add to all Redis keys. Defaults to ``asgi:``. If you're running
two or more entirely separate channel layers through the same Redis instance,
make sure they have different prefixes. All servers talking to the same layer
should have the same prefix, though.

``expiry``
~~~~~~~~~~

Message expiry in seconds. Defaults to ``60``. You generally shouldn't need
to change this, but you may want to turn it down if you have peaky traffic you
wish to drop, or up if you have peaky traffic you want to backlog until you
get to it.

``group_expiry``
~~~~~~~~~~~~~~~~

Group expiry in seconds. Defaults to ``86400``. Interface servers will drop
connections after this amount of time; it's recommended you reduce it for a
healthier system that encourages disconnections.

``capacity``
~~~~~~~~~~~~

Default channel capacity. Defaults to ``100``. Once a channel is at capacity,
it will refuse more messages. How this affects different parts of the system
varies; a HTTP server will refuse connections, for example, while Django
sending a response will just wait until there's space.

``channel_capacity``
~~~~~~~~~~~~~~~~~~~~

Per-channel capacity configuration. This lets you tweak the channel capacity
based on the channel name, and supports both globbing and regular expressions.

It should be a dict mapping channel name pattern to desired capacity; if the
dict key is a string, it's intepreted as a glob, while if it's a compiled
``re`` object, it's treated as a regular expression.

This example sets ``http.request`` to 200, all ``http.response!`` channels
to 10, and all ``websocket.send!`` channels to 20:

.. code-block:: python

    channel_capacity={
        "http.request": 200,
        "http.response!*": 10,
        re.compile(r"^websocket.send\!.+"): 20,
    }

If you want to enforce a matching order, use an ``OrderedDict`` as the
argument; channels will then be matched in the order the dict provides them.

``symmetric_encryption_keys``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Pass this to enable the optional symmetric encryption mode of the backend. To
use it, make sure you have the ``cryptography`` package installed, or specify
the ``cryptography`` extra when you install ``asgi_redis``::

    pip install asgi_redis[cryptography]

``symmetric_encryption_keys`` should be a list of strings, with each string
being an encryption key. The first key is always used for encryption; all are
considered for decryption, so you can rotate keys without downtime - just add
a new key at the start and move the old one down, then remove the old one
after the message expiry time has passed.

Data is encrypted both on the wire and at rest in Redis, though we advise
you also route your Redis connections over TLS for higher security; the Redis
protocol is still unencrypted, and the channel and group key names could
potentially contain metadata patterns of use to attackers.

Keys **should have at least 32 bytes of entropy** - they are passed through
the SHA256 hash function before being used as an encryption key. Any string
will work, but the shorter the string, the easier the encryption is to break.

If you're using Django, you may also wish to set this to your site's
``SECRET_KEY`` setting via the ``CHANNEL_LAYERS`` setting:

.. code-block:: python

    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "asgi_redis.RedisChannelLayer",
            "ROUTING": "my_project.routing.channel_routing",
            "CONFIG": {
                "hosts": ["redis://:password@127.0.0.1:6379/0"],
                "symmetric_encryption_keys": [SECRET_KEY],
            },
        },
    }

``connection_kwargs``
---------------------

Optional extra arguments to pass to the ``redis-py`` connection class. Options
include ``socket_connect_timeout``, ``socket_timeout``, ``socket_keepalive``,
and ``socket_keepalive_options``. See the
`redis-py documentation <https://redis-py.readthedocs.io/en/latest/>`_ for more.


Local-and-Remote Mode
---------------------

A "local and remote" mode is also supported, where the Redis channel layer
works in conjunction with a machine-local channel layer (``asgi_ipc``) in order
to route all normal channels over the local layer, while routing all
single-reader and process-specific channels over the Redis layer.

This allows traffic on things like ``http.request`` and ``websocket.receive``
to stay in the local layer and not go through Redis, while still allowing Group
send and sends to arbitrary channels terminated on other machines to work
correctly. It will improve performance and decrease the load on your
Redis cluster, but **it requires all normal channels are consumed on the
same machine**.

In practice, this means you MUST run workers that consume every channel your
application has code to handle on the same machine as your HTTP or WebSocket
terminator. If you fail to do this, requests to that machine will get routed
into only the local queue and hang as nothing is reading them.

To use it, just use the ``asgi_redis.RedisLocalChannelLayer`` class in your
configuration instead of ``RedisChannelLayer`` and make sure you have the
``asgi_ipc`` package installed; no other change is needed.


Sentinel Mode
-------------

"Sentinel" mode is also supported, where the Redis channel layer will connect to
a redis sentinel cluster to find the present Redis master before writing or reading
data.

Sentinel mode supports sharding, but does not support multiple Sentinel clusters. To
run sharding of keys across multiple Redis clusters, use a single sentinel cluster,
but have that sentinel cluster monitor multiple "services". Then in the configuration
for the RedisSentinelChannelLayer, add a list of the service names. You can also
leave the list of services blank, and the layer will pull all services that are
configured on the sentinel master.

Redis Sentinel mode does not support URL-style connection strings, just tuple-based ones.

Configuration for Sentinel mode looks like this:

.. code-block:: python

    CHANNEL_LAYERS = {
        "default": {
            "BACKEND": "asgi_redis.RedisSentinelChannelLayer",
            "CONFIG": {
                "hosts": [("10.0.0.1", 26739), ("10.0.0.2", 26379), ("10.0.0.3", 26379)],
                "services": ["shard1", "shard2", "shard3"],
            },
        },
    }

The "shard1", "shard2", etc entries correspond to the name of the service configured in  your
redis `sentinel.conf` file. For example, if your `sentinel.conf` says ``sentinel monitor local 127.0.0.1 6379 1``
then you would want to include "local" as a service in the `RedisSentinelChannelLayer` configuration.

You may also pass a ``sentinel_refresh_interval`` value in the ``CONFIG``, which
will enable caching of the Sentinel results for the specified number of seconds.
This is recommended to reduce the need to query Sentinel every time; even a
low value of 5 seconds will significantly reduce overhead.

Dependencies
------------

Redis >= 2.6 is required for `asgi_redis`. It supports Python 2.7, 3.4,
3.5 and 3.6.

Contributing
------------

Please refer to the
`main Channels contributing docs <https://github.com/django/channels/blob/master/CONTRIBUTING.rst>`_.
That also contains advice on how to set up the development environment and run the tests.

Maintenance and Security
------------------------

To report security issues, please contact security@djangoproject.com. For GPG
signatures and more security process information, see
https://docs.djangoproject.com/en/dev/internals/security/.

To report bugs or request new features, please open a new GitHub issue.

This repository is part of the Channels project. For the shepherd and maintenance team, please see the
`main Channels readme <https://github.com/django/channels/blob/master/README.rst>`_.


