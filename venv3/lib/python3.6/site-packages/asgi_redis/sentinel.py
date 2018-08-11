from __future__ import unicode_literals

import itertools
import random
import redis
from redis.sentinel import Sentinel
import six
import time

from asgi_redis.core import BaseRedisChannelLayer

random.seed()


class RedisSentinelChannelLayer(BaseRedisChannelLayer):
    """
    Variant of the Redis channel layer that supports the Redis Sentinel HA protocol.

    Supports sharding, but assumes that there is only one sentinel cluster with multiple redis services
    monitored by that cluster. So, this will only connect to a single cluster of Sentinel servers,
    but will suppport sharding by asking that sentinel cluster for different services. Also, any redis connection
    options (socket timeout, socket keepalive, etc) will be assumed to be identical across redis server, and
    across all services.

    "hosts" in this arrangement, is used to list the redis sentinel hosts. As such, it only supports the
    tuple method of specifying hosts, as that's all the redis sentinel python library supports at the moment.

    "services" is the list of redis services monitored by the sentinel system that redis keys will be distributed
     across. If services is empty, this will fetch all services from Sentinel at initialization.
    """

    def __init__(
        self,
        expiry=60,
        hosts=None,
        prefix="asgi:",
        group_expiry=86400,
        capacity=100,
        channel_capacity=None,
        symmetric_encryption_keys=None,
        stats_prefix="asgi-meta:",
        connection_kwargs=None,
        services=None,
        sentinel_refresh_interval=0,
    ):
        super(RedisSentinelChannelLayer, self).__init__(
            expiry=expiry,
            hosts=hosts,
            prefix=prefix,
            group_expiry=group_expiry,
            capacity=capacity,
            channel_capacity=channel_capacity,
            symmetric_encryption_keys=symmetric_encryption_keys,
            stats_prefix=stats_prefix,
            connection_kwargs=connection_kwargs,
        )

        # Master connection caching
        self.sentinel_refresh_interval = sentinel_refresh_interval
        self._last_sentinel_refresh = 0
        self._master_connections = {}

        connection_kwargs = connection_kwargs or {}
        self._sentinel = Sentinel(self._setup_hosts(hosts), **connection_kwargs)
        if services:
            self._validate_service_names(services)
            self.services = services
        else:
            self.services = self._get_service_names()

        # Precalculate some values for ring selection
        self.ring_size = len(self.services)
        self._receive_index_generator = itertools.cycle(range(len(self.services)))
        self._send_index_generator = itertools.cycle(range(len(self.services)))
        self._register_scripts()

    ### Setup ###

    def _setup_hosts(self, hosts):
        # Override to only accept tuples, since the redis.sentinel.Sentinel does not accept URLs
        if not hosts:
            hosts = [("localhost", 26379)]
        final_hosts = list()
        if isinstance(hosts, six.string_types):
            # user accidentally used one host string instead of providing a list of hosts
            raise ValueError("ASGI Redis hosts must be specified as an iterable list of hosts.")

        for entry in hosts:
            if isinstance(entry, six.string_types):
                raise ValueError("Sentinel Redis host entries must be specified as tuples, not strings.")
            else:
                final_hosts.append(entry)
        return final_hosts

    def _validate_service_names(self, services):
        if isinstance(services, six.string_types):
            raise ValueError("Sentinel service types must be specified as an iterable list of strings")
        for entry in services:
            if not isinstance(entry, six.string_types):
                raise ValueError("Sentinel service types must be specified as strings.")

    def _get_service_names(self):
        """
        Get a list of service names from Sentinel. Tries Sentinel hosts until one succeeds; if none succeed,
        raises a ConnectionError.
        """
        master_info = None
        connection_errors = []
        for sentinel in self._sentinel.sentinels:
            # Unfortunately, redis.sentinel.Sentinel does not support sentinel_masters, so we have to step
            # through all of its connections manually
            try:
                master_info = sentinel.sentinel_masters()
                break
            except (redis.ConnectionError, redis.TimeoutError) as e:
                connection_errors.append("Failed to connect to {}: {}".format(sentinel, e))
                continue
        if master_info is None:
            raise redis.ConnectionError(
                "Could not get master info from sentinel\n{}.".format("\n".join(connection_errors)))
        return list(master_info.keys())

    ### Connection handling ####

    def _master_for(self, service_name):
        if self.sentinel_refresh_interval <= 0:
            return self._sentinel.master_for(service_name)
        else:
            if (time.time() - self._last_sentinel_refresh) > self.sentinel_refresh_interval:
                self._populate_masters()
            return self._master_connections[service_name]

    def _populate_masters(self):
        self._master_connections = {service: self._sentinel.master_for(service) for service in self.services}
        self._last_sentinel_refresh = time.time()

    def connection(self, index):
        # return the master for the given index
        # If index is explicitly None, pick a random server
        if index is None:
            index = self.random_index()
        # Catch bad indexes
        if not 0 <= index < self.ring_size:
            raise ValueError("There are only %s hosts - you asked for %s!" % (self.ring_size, index))
        service_name = self.services[index]
        return self._master_for(service_name)

    def random_index(self):
        return random.randint(0, len(self.services) - 1)

    ### Flush extension ###

    def flush(self):
        """
        Deletes all messages and groups on all shards.
        """
        for service_name in self.services:
            connection = self._master_for(service_name)
            self.delprefix(keys=[], args=[self.prefix + "*"], client=connection)
            self.delprefix(keys=[], args=[self.stats_prefix + "*"], client=connection)

    ### Statistics extension ###

    def global_statistics(self):
        connection_list = [self._master_for(service_name) for service_name in self.services]
        return self._count_global_stats(connection_list)

    def channel_statistics(self, channel):
        if "!" in channel or "?" in channel:
            connections = [self.connection(self.consistent_hash(channel))]
        else:
            # if we don't know where it is, we have to check in all shards
            connections = [self._master_for(service_name) for service_name in self.services]

        return self._count_channel_stats(channel, connections)

    def __str__(self):
        return "%s(services==%s)" % (self.__class__.__name__, self.services)
