from unittest.mock import MagicMock, patch

import dns.exception
import dns.resolver
from accounts.adapter import (
    DISPOSABLE_DOMAINS,
    DOMAIN_TYPO_MAP,
    ROLE_BASED_LOCAL_PARTS,
    EvalAIAccountAdapter,
)
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings


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


class TestRoleBasedEmailRejection(TestCase):
    def setUp(self):
        self.adapter = EvalAIAccountAdapter()

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_noreply_address(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("noreply@example.com")
        self.assertIn("Role-based email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_admin_address(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("admin@example.com")
        self.assertIn("Role-based email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_postmaster_address(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("postmaster@example.com")
        self.assertIn("Role-based email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_support_address(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("support@example.com")
        self.assertIn("Role-based email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_role_based_case_insensitive(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("NoReply@example.com")
        self.assertIn("Role-based email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_allows_personal_address(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        result = self.adapter.clean_email("john.doe@example.com")
        self.assertEqual(result, "john.doe@example.com")

    def test_all_role_parts_are_lowercase(self):
        for part in ROLE_BASED_LOCAL_PARTS:
            self.assertEqual(part, part.lower())


class TestDisposableEmailRejection(TestCase):
    def setUp(self):
        self.adapter = EvalAIAccountAdapter()

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_known_disposable_domain(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        self.assertIn("mailinator.com", DISPOSABLE_DOMAINS)
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("user@mailinator.com")
        self.assertIn("Disposable email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_guerrillamail(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        self.assertIn("guerrillamail.com", DISPOSABLE_DOMAINS)
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("user@guerrillamail.com")
        self.assertIn("Disposable email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_allows_legitimate_domain(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        result = self.adapter.clean_email("user@gmail.com")
        self.assertEqual(result, "user@gmail.com")

    @patch("accounts.adapter.dns.resolver.resolve")
    @override_settings(BLOCKED_EMAIL_DOMAINS=["custom-blocked.com"])
    def test_rejects_admin_blocked_domain(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("user@custom-blocked.com")
        self.assertIn("Disposable email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    @override_settings(BLOCKED_EMAIL_DOMAINS=["custom-blocked.com"])
    def test_admin_blocklist_does_not_affect_legitimate(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        result = self.adapter.clean_email("user@gmail.com")
        self.assertEqual(result, "user@gmail.com")

    def test_disposable_domains_set_is_populated(self):
        self.assertGreater(len(DISPOSABLE_DOMAINS), 1000)


class TestDomainTypoDetection(TestCase):
    def setUp(self):
        self.adapter = EvalAIAccountAdapter()

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_gmial_with_suggestion(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("alice@gmial.com")
        msg = str(ctx.exception)
        self.assertIn("Did you mean alice@gmail.com", msg)
        self.assertIn("looks like a typo", msg)

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_hotmal_with_suggestion(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("bob@hotmal.com")
        self.assertIn("Did you mean bob@hotmail.com", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_yaho_with_suggestion(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("carol@yaho.com")
        self.assertIn("Did you mean carol@yahoo.com", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_rejects_outlok_with_suggestion(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("dave@outlok.com")
        self.assertIn("Did you mean dave@outlook.com", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_allows_correct_gmail(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        result = self.adapter.clean_email("user@gmail.com")
        self.assertEqual(result, "user@gmail.com")

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_typo_check_is_case_insensitive(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("user@GMIAL.COM")
        self.assertIn("Did you mean", str(ctx.exception))

    def test_all_typo_map_keys_are_lowercase(self):
        for key in DOMAIN_TYPO_MAP:
            self.assertEqual(key, key.lower())

    def test_all_typo_map_values_are_lowercase(self):
        for value in DOMAIN_TYPO_MAP.values():
            self.assertEqual(value, value.lower())


class TestValidationOrder(TestCase):
    """Verify that checks run in the documented order:
    duplicate -> role-based -> disposable -> typo -> MX
    """

    def setUp(self):
        self.adapter = EvalAIAccountAdapter()

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_duplicate_checked_before_role_based(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        User.objects.create(
            username="dup", email="admin@example.com", password="pw"
        )
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("admin@example.com")
        self.assertIn("already registered", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_role_based_checked_before_disposable(self, mock_resolve):
        """noreply@ at a disposable domain should fail on role-based first."""
        mock_resolve.return_value = [MagicMock()]
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("noreply@mailinator.com")
        self.assertIn("Role-based email", str(ctx.exception))

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_disposable_checked_before_mx(self, mock_resolve):
        """Disposable domains should be rejected without even doing MX lookup."""
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("user@mailinator.com")
        self.assertIn("Disposable email", str(ctx.exception))
        mock_resolve.assert_not_called()

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_typo_checked_before_mx(self, mock_resolve):
        """Typo'd domains should be rejected without MX lookup."""
        with self.assertRaises(ValidationError) as ctx:
            self.adapter.clean_email("user@gmial.com")
        self.assertIn("Did you mean", str(ctx.exception))
        mock_resolve.assert_not_called()
