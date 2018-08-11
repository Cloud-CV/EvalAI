from __future__ import unicode_literals

import six


STATUS_MAP = {
    200: b"OK",
    201: b"Created",
    204: b"No Content",
    400: b"Bad Request",
    401: b"Unauthorized",
    403: b"Forbidden",
    404: b"Not Found",
    500: b"Internal Server Error",
}


class WsgiToAsgiAdapter(object):
    """
    Class which acts as a WSGI application and translates the requests onto
    HTTP requests on an ASGI backend.

    Fully synchronous, so you'll likely want to run a lot of threads/processes;
    the main application logic isn't in memory, so the footprint should be
    lower.
    """

    def __init__(self, channel_layer):
        self.channel_layer = channel_layer

    def get_reply_channel(self):
        """
        Overrideable for tests, where you want a fixed reply channel.
        """
        return self.channel_layer.new_channel("http.response!")

    def __call__(self, environ, start_response):
        # Translate the environ into an ASGI-style request
        request = self.translate_request(environ)
        # Run it through ASGI
        reply_channel = self.get_reply_channel()
        request["reply_channel"] = reply_channel
        self.channel_layer.send("http.request", request)
        # Translate the first response message
        response = self.get_message(reply_channel)
        status = (
            six.text_type(response["status"]).encode("latin1") +
            b" " +
            response.get(
                "status_text",
                STATUS_MAP.get(response["status"], b"Unknown Status")
            )
        )
        start_response(
            status,
            [(n.encode("latin1"), v) for n, v in response.get("headers", [])],
        )
        yield response.get("content", b"")
        while response.get("more_content", False):
            response = self.get_message(reply_channel)
            yield response.get("content", b"")

    def translate_request(self, environ):
        """
        Turns a WSGI environ into an ASGI http.request message
        """
        request = {}
        # HTTP version
        if "SERVER_PROTOCOL" in environ and "HTTP/" in environ["SERVER_PROTOCOL"]:
            request["http_version"] = environ["SERVER_PROTOCOL"][5:]
        else:
            # Lowest possible feature set
            request["http_version"] = "1.0"
        # Method
        request["method"] = environ["REQUEST_METHOD"].upper()
        # Query string
        request["query_string"] = environ.get("QUERY_STRING", "").encode("latin1")
        # Path and root path
        request["root_path"] =  environ.get("SCRIPT_NAME", "").encode("latin1")
        request["path"] = environ.get("PATH_INFO", "").encode("latin1")
        if request["root_path"]:
            request["path"] = request["root_path"] + request["path"]
        if not request["path"]:
            request["path"] = b"/"
        # Headers
        # TODO
        # Body
        # TODO
        # Client (if provided)
        if "REMOTE_ADDR" in environ and "REMOTE_PORT" in environ:
            request["client"] = [environ["REMOTE_ADDR"], int(environ["REMOTE_PORT"])]
        # Server (if provided)
        if "SERVER_NAME" in environ and "SERVER_PORT" in environ:
            request["server"] = [environ["SERVER_NAME"], int(environ["SERVER_PORT"])]
        return request

    def get_message(self, channel):
        """
        Blocks until it gets a message on channel, then returns it.
        """
        while True:
            _, message = self.channel_layer.receive([channel], block=True)
            if message is not None:
                return message
