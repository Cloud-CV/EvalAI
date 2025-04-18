from unittest.mock import MagicMock

from accounts.throttles import ResendEmailThrottle
from django.test import TestCase


class TestResendEmailThrottle(TestCase):
    def test_get_cache_key_else_statement(self):
        throttle = ResendEmailThrottle()
        request = MagicMock()
        request.user.is_authenticated = False
        request.META = {"REMOTE_ADDR": "192.168.1.1"}

        cache_key = throttle.get_cache_key(request, MagicMock())

        self.assertIn("throttle_resend_email", cache_key)
        self.assertIn("192.168.1.1", cache_key)

    def test_get_cache_key_else_statement_with_auth_user(self):
        throttle = ResendEmailThrottle()
        user = MagicMock()
        user.pk = 1
        request = MagicMock()
        request.user = user
        request.user.is_authenticated = True

        cache_key = throttle.get_cache_key(request, MagicMock())

        self.assertIn("throttle_resend_email", cache_key)
        self.assertIn("1", cache_key)
