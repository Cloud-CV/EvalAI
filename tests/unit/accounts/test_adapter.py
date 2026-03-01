from unittest.mock import MagicMock, patch

import dns.exception
import dns.resolver
from accounts.adapter import EvalAIAccountAdapter
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase


class TestEvalAIAccountAdapterMXValidation(TestCase):
    def setUp(self):
        self.adapter = EvalAIAccountAdapter()

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_clean_email_valid_domain(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        result = self.adapter.clean_email("user@valid-domain.com")
        self.assertEqual(result, "user@valid-domain.com")
        mock_resolve.assert_called_once_with("valid-domain.com", "MX")

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_clean_email_invalid_domain_nxdomain(self, mock_resolve):
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("user@nonexistent.xyz")
        self.assertIn("does not appear to accept email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_clean_email_invalid_domain_no_answer(self, mock_resolve):
        mock_resolve.side_effect = dns.resolver.NoAnswer()
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("user@no-mx.com")
        self.assertIn("does not appear to accept email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_clean_email_dns_timeout_allows_through(self, mock_resolve):
        mock_resolve.side_effect = dns.exception.Timeout()
        result = self.adapter.clean_email("user@slow-dns.com")
        self.assertEqual(result, "user@slow-dns.com")

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_clean_email_unexpected_error_allows_through(self, mock_resolve):
        mock_resolve.side_effect = RuntimeError("unexpected")
        result = self.adapter.clean_email("user@weird-error.com")
        self.assertEqual(result, "user@weird-error.com")


class TestEvalAIAccountAdapterDuplicateEmail(TestCase):
    def setUp(self):
        self.adapter = EvalAIAccountAdapter()
        self.existing_user = User.objects.create(
            username="existing",
            email="taken@example.com",
            password="password",
        )

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_clean_email_rejects_duplicate(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("taken@example.com")
        self.assertIn("already registered", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_clean_email_rejects_duplicate_case_insensitive(
        self, mock_resolve
    ):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("TAKEN@Example.COM")
        self.assertIn("already registered", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_clean_email_allows_new_address(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        result = self.adapter.clean_email("fresh@example.com")
        self.assertEqual(result, "fresh@example.com")


class TestEvalAIAccountAdapterSendMail(TestCase):
    def setUp(self):
        self.adapter = EvalAIAccountAdapter()
        self.user = User.objects.create(
            username="bounceuser",
            email="bounced@test.com",
            password="password",
        )
        self.user.profile.email_bounced = True
        self.user.profile.save()

    @patch.object(EvalAIAccountAdapter.__bases__[0], "send_mail")
    def test_send_mail_suppressed_for_bounced_user(self, mock_super_send):
        self.adapter.send_mail(
            "account/email/email_confirmation", "bounced@test.com", {}
        )
        mock_super_send.assert_not_called()

    @patch.object(EvalAIAccountAdapter.__bases__[0], "send_mail")
    def test_send_mail_allowed_for_non_bounced_user(self, mock_super_send):
        self.user.profile.email_bounced = False
        self.user.profile.save()
        self.adapter.send_mail(
            "account/email/email_confirmation", "bounced@test.com", {}
        )
        mock_super_send.assert_called_once()

    @patch.object(EvalAIAccountAdapter.__bases__[0], "send_mail")
    def test_send_mail_no_user_falls_through_to_default(self, mock_super_send):
        """When no User exists for the email, fall through to default sending."""
        self.adapter.send_mail(
            "account/email/email_confirmation",
            "nobody@example.com",
            {},
        )
        mock_super_send.assert_called_once()
