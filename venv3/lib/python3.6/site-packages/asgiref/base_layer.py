from __future__ import unicode_literals

import fnmatch
import re
import six
import warnings


class BaseChannelLayer(object):
    """
    Base channel layer object; outlines the core API and contains some handy
    reuseable code bits. You don't have to inherit from this, but it might
    save you time.
    """

    def __init__(self, expiry=60, group_expiry=86400, capacity=100, channel_capacity=None):
        self.expiry = expiry
        self.capacity = capacity
        self.group_expiry = group_expiry
        self.channel_capacity = self.compile_capacities(channel_capacity or {})

    ### ASGI API ###

    extensions = []

    class ChannelFull(Exception):
        pass

    class MessageTooLarge(Exception):
        pass

    def send(self, channel, message):
        raise NotImplementedError()

    def receive(self, channels, block=False):
        raise NotImplementedError()

    def receive_many(self, channels, block=False):
        """
        receive_many is deprecated, but this is provided for backwards compatability.
        """
        warnings.warn("receive_many is deprecated; please use receive", DeprecationWarning)
        return self.receive(channels, block)

    def new_channel(self, pattern):
        raise NotImplementedError()

    ### ASGI Group API ###

    def group_add(self, group, channel):
        raise NotImplementedError()

    def group_discard(self, group, channel):
        raise NotImplementedError()

    def group_channels(self, group):
        raise NotImplementedError()

    def send_group(self, group, message):
        raise NotImplementedError()

    ### ASGI Flush API ###

    def flush(self):
        raise NotImplementedError()

    ### Capacity utility functions

    def compile_capacities(self, channel_capacity):
        """
        Takes an input channel_capacity dict and returns the compiled list
        of regexes that get_capacity will look for as self.channel_capacity/
        """
        result = []
        for pattern, value in channel_capacity.items():
            # If they passed in a precompiled regex, leave it, else intepret
            # it as a glob.
            if hasattr(pattern, "match"):
                result.append((pattern, value))
            else:
                result.append((re.compile(fnmatch.translate(pattern)), value))
        return result

    def get_capacity(self, channel):
        """
        Gets the correct capacity for the given channel; either the default,
        or a matching result from channel_capacity. Returns the first matching
        result; if you want to control the order of matches, use an ordered dict
        as input.
        """
        for pattern, capacity in self.channel_capacity:
            if pattern.match(channel):
                return capacity
        return self.capacity

    def match_type_and_length(self, name):
        if (len(name) < 100) and (isinstance(name, six.text_type)):
            return True
        return False

    ### Name validation functions

    channel_name_regex = re.compile(r"^[a-zA-Z\d\-_.]+((\?|\!)[\d\w\-_.]*)?$")
    group_name_regex = re.compile(r"^[a-zA-Z\d\-_.]+$")
    invalid_name_error = "{} name must be a valid unicode string containing only ASCII alphanumerics, hyphens, underscores, or periods."

    def valid_channel_name(self, name, receive=False):
        if self.match_type_and_length(name):
            if bool(self.channel_name_regex.match(name)):
                # Check cases for special channels
                if "?" in name and name.endswith("?"):
                    raise TypeError("Single-reader channel names must not end with ?")
                elif "!" in name and not name.endswith("!") and receive:
                    raise TypeError("Process-local channel names in receive() must end at the !")
                return True
        raise TypeError("Channel name must be a valid unicode string containing only ASCII alphanumerics, hyphens, or periods, not '{}'.".format(name))

    def valid_group_name(self, name):
        if self.match_type_and_length(name):
            if bool(self.group_name_regex.match(name)):
                return True
        raise TypeError("Group name must be a valid unicode string containing only ASCII alphanumerics, hyphens, or periods.")

    def valid_channel_names(self, names, receive=False):
        _non_empty_list = True if names else False
        _names_type = isinstance(names, list)
        assert _non_empty_list and _names_type, "names must be a non-empty list"

        assert all(self.valid_channel_name(channel, receive=receive) for channel in names)
        return True

    def non_local_name(self, name):
        """
        Given a channel name, returns the "non-local" part. If the channel name
        is a process-specific channel (contains !) this means the part up to
        and including the !; if it is anything else, this means the full name.
        """
        if "!" in name:
            return name[:name.find("!")+1]
        else:
            return name
