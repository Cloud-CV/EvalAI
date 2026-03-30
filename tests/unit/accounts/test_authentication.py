"""Tests for custom ExpiringTokenAuthentication."""

from unittest.mock import patch

from accounts.authentication import ExpiringTokenAuthentication
from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import exceptions
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
from rest_framework_expiring_authtoken.models import ExpiringToken


class TestExpiringTokenAuthenticationCredentials(TestCase):
    """Tests for authenticate_credentials."""

    def setUp(self):
        self.auth = ExpiringTokenAuthentication()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass",
        )

    def tearDown(self):
        ExpiringToken.objects.filter(user__username="testuser").delete()
        User.objects.filter(username="testuser").delete()

    def test_authenticate_credentials_invalid_token_raises(self):
        """Invalid token key raises AuthenticationFailed with 'Invalid token'."""
        with self.assertRaises(exceptions.AuthenticationFailed) as ctx:
            self.auth.authenticate_credentials("nonexistent-key-12345")
        self.assertEqual(ctx.exception.detail, "Invalid token")

    def test_authenticate_credentials_inactive_user_raises(self):
        """Inactive user raises AuthenticationFailed."""
        token = ExpiringToken.objects.create(user=self.user)
        self.user.is_active = False
        self.user.save()
        try:
            with self.assertRaises(exceptions.AuthenticationFailed) as ctx:
                self.auth.authenticate_credentials(token.key)
            self.assertEqual(ctx.exception.detail, "User inactive or deleted")
        finally:
            self.user.is_active = True
            self.user.save()
            token.delete()

    def test_authenticate_credentials_expired_token_raises(self):
        """Expired token raises AuthenticationFailed."""
        token = ExpiringToken.objects.create(user=self.user)
        with patch.object(token, "expired", return_value=True):
            with patch(
                "accounts.authentication.ExpiringToken.objects.get",
                return_value=token,
            ):
                with self.assertRaises(exceptions.AuthenticationFailed) as ctx:
                    self.auth.authenticate_credentials(token.key)
                self.assertEqual(ctx.exception.detail, "Token has expired")
        token.delete()

    def test_authenticate_credentials_valid_token_returns_user_and_token(self):
        """Valid token returns (user, token) tuple."""
        token = ExpiringToken.objects.create(user=self.user)
        with patch.object(token, "expired", return_value=False):
            with patch(
                "accounts.authentication.ExpiringToken.objects.get",
                return_value=token,
            ):
                result = self.auth.authenticate_credentials(token.key)
        self.assertEqual(result, (self.user, token))
        token.delete()


class TestExpiringTokenAuthenticationAuthenticate(TestCase):
    """Tests for authenticate() and logout on failure."""

    def setUp(self):
        self.auth = ExpiringTokenAuthentication()
        self.factory = APIRequestFactory()

    def test_authenticate_calls_logout_on_authentication_failed(self):
        """When super().authenticate raises AuthenticationFailed, logout is called."""
        request = self.factory.get(
            "/api/auth/user/",
            HTTP_AUTHORIZATION="Token invalid-key",
        )
        drf_request = Request(request)

        with patch.object(
            self.auth,
            "authenticate_credentials",
            side_effect=exceptions.AuthenticationFailed("Invalid token"),
        ):
            with patch("accounts.authentication.logout") as mock_logout:
                with self.assertRaises(exceptions.AuthenticationFailed):
                    self.auth.authenticate(drf_request)
                mock_logout.assert_called_once_with(request)

    def test_authenticate_re_raises_authentication_failed(self):
        """AuthenticationFailed from credentials is re-raised after logout."""
        request = self.factory.get(
            "/api/auth/user/",
            HTTP_AUTHORIZATION="Token invalid-key",
        )
        drf_request = Request(request)

        with patch.object(
            self.auth,
            "authenticate_credentials",
            side_effect=exceptions.AuthenticationFailed("Invalid token"),
        ):
            with patch("accounts.authentication.logout"):
                with self.assertRaises(exceptions.AuthenticationFailed) as ctx:
                    self.auth.authenticate(drf_request)
                self.assertEqual(ctx.exception.detail, "Invalid token")
