from datetime import timedelta

from accounts.tasks import deactivate_stale_bounced_accounts
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone


class TestDeactivateStaleBounced(TestCase):
    def _create_user(self, username, email, verified=True):
        user = User.objects.create(
            username=username, email=email, password="password"
        )
        EmailAddress.objects.create(
            user=user, email=email, primary=True, verified=verified
        )
        return user

    def test_deactivates_account_after_24_hours(self):
        user = self._create_user("stale", "stale@test.com")
        user.profile.email_bounced = True
        user.profile.email_bounced_at = timezone.now() - timedelta(hours=25)
        user.profile.save()

        count = deactivate_stale_bounced_accounts()

        self.assertEqual(count, 1)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_does_not_deactivate_within_24_hours(self):
        user = self._create_user("fresh", "fresh@test.com")
        user.profile.email_bounced = True
        user.profile.email_bounced_at = timezone.now() - timedelta(hours=12)
        user.profile.save()

        count = deactivate_stale_bounced_accounts()

        self.assertEqual(count, 0)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_skips_already_deactivated_accounts(self):
        user = self._create_user("inactive", "inactive@test.com")
        user.is_active = False
        user.save()
        user.profile.email_bounced = True
        user.profile.email_bounced_at = timezone.now() - timedelta(hours=48)
        user.profile.save()

        count = deactivate_stale_bounced_accounts()

        self.assertEqual(count, 0)

    def test_skips_non_bounced_users(self):
        user = self._create_user("clean", "clean@test.com")

        count = deactivate_stale_bounced_accounts()

        self.assertEqual(count, 0)
        user.refresh_from_db()
        self.assertTrue(user.is_active)

    def test_deactivates_multiple_stale_accounts(self):
        user1 = self._create_user("stale1", "stale1@test.com")
        user1.profile.email_bounced = True
        user1.profile.email_bounced_at = timezone.now() - timedelta(hours=30)
        user1.profile.save()

        user2 = self._create_user("stale2", "stale2@test.com")
        user2.profile.email_bounced = True
        user2.profile.email_bounced_at = timezone.now() - timedelta(hours=48)
        user2.profile.save()

        fresh = self._create_user("fresh", "fresh@test.com")
        fresh.profile.email_bounced = True
        fresh.profile.email_bounced_at = timezone.now() - timedelta(hours=6)
        fresh.profile.save()

        count = deactivate_stale_bounced_accounts()

        self.assertEqual(count, 2)
        user1.refresh_from_db()
        user2.refresh_from_db()
        fresh.refresh_from_db()
        self.assertFalse(user1.is_active)
        self.assertFalse(user2.is_active)
        self.assertTrue(fresh.is_active)

    def test_user_who_resolved_bounce_is_not_deactivated(self):
        """If a user cleared the bounce flag (by confirming a new email),
        they should not be deactivated even if email_bounced_at is old."""
        user = self._create_user("resolved", "resolved@test.com")
        user.profile.email_bounced = False
        user.profile.email_bounced_at = timezone.now() - timedelta(hours=48)
        user.profile.save()

        count = deactivate_stale_bounced_accounts()

        self.assertEqual(count, 0)
        user.refresh_from_db()
        self.assertTrue(user.is_active)
