from __future__ import unicode_literals
from asgi_redis import RedisChannelLayer


class RedisLocalChannelLayer(RedisChannelLayer):
    """
    Variant of the Redis channel layer that also uses a local-machine
    channel layer instance to route all non-machine-specific messages
    to a local machine, while using the Redis backend for all machine-specific
    messages and group management/sends.

    This allows the majority of traffic to go over the local layer for things
    like http.request and websocket.receive, while still allowing Groups to
    broadcast to all connected clients and keeping reply_channel names valid
    across all workers.
    """

    def __init__(self, expiry=60, prefix="asgi:", group_expiry=86400, capacity=100, channel_capacity=None, **kwargs):
        # Initialise the base class
        super(RedisLocalChannelLayer, self).__init__(
            prefix = prefix,
            expiry = expiry,
            group_expiry = group_expiry,
            capacity = capacity,
            channel_capacity = channel_capacity,
            **kwargs
        )
        # Set up our local transport layer as well
        try:
            from asgi_ipc import IPCChannelLayer
        except ImportError:
            raise ValueError("You must install asgi_ipc to use the local variant")
        self.local_layer = IPCChannelLayer(
            prefix = prefix.replace(":", ""),
            expiry = expiry,
            group_expiry = group_expiry,
            capacity = capacity,
            channel_capacity = channel_capacity,
        )

    ### ASGI API ###

    def send(self, channel, message):
        # If the channel is "normal", use IPC layer, otherwise use Redis layer
        if "!" in channel or "?" in channel:
            return super(RedisLocalChannelLayer, self).send(channel, message)
        else:
            return self.local_layer.send(channel, message)

    def receive(self, channels, block=False):
        # Work out what kinds of channels are in there
        num_remote = len([channel for channel in channels if "!" in channel or "?" in channel])
        num_local = len(channels) - num_remote
        # If they mixed types, force nonblock mode and query both backends, local first
        if num_local and num_remote:
            result = self.local_layer.receive(channels, block=False)
            if result[0] is not None:
                return result
            return super(RedisLocalChannelLayer, self).receive(channels, block=block)
        # If they just did one type, pass off to that backend
        elif num_local:
            return self.local_layer.receive(channels, block=block)
        else:
            return super(RedisLocalChannelLayer, self).receive(channels, block=block)

    # new_channel always goes to Redis as it's always remote channels.
    # Group APIs always go to Redis too.

    def flush(self):
        # Dispatch flush to both
        super(RedisLocalChannelLayer, self).flush()
        self.local_layer.flush()
