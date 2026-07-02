from unittest.mock import MagicMock

from accounts.throttles import (
    PasswordResetEmailThrottle,
    PasswordResetIPThrottle,
    ResendEmailThrottle,
)
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


class TestPasswordResetEmailThrottle(TestCase):
    def test_get_cache_key_normalizes_email(self):
        throttle = PasswordResetEmailThrottle()
        request = MagicMock()
        request.data = {"email": "  User@Example.COM  "}

        cache_key = throttle.get_cache_key(request, MagicMock())

        self.assertIn("throttle_password_reset_email", cache_key)
        self.assertIn("user@example.com", cache_key)

    def test_get_cache_key_returns_none_without_email(self):
        throttle = PasswordResetEmailThrottle()
        request = MagicMock()
        request.data = {}

        cache_key = throttle.get_cache_key(request, MagicMock())

        self.assertIsNone(cache_key)


class TestPasswordResetIPThrottle(TestCase):
    def test_get_cache_key_uses_client_ip(self):
        throttle = PasswordResetIPThrottle()
        request = MagicMock()
        request.META = {"REMOTE_ADDR": "10.0.0.1"}

        cache_key = throttle.get_cache_key(request, MagicMock())

        self.assertIn("throttle_password_reset_ip", cache_key)
        self.assertIn("10.0.0.1", cache_key)
