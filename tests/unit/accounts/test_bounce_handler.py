from accounts.bounce_handler import handle_bounce, handle_complaint
from accounts.models import Profile
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.test import TestCase


class BounceHandlerTestBase(TestCase):
    def setUp(self):
        self.verified_user = User.objects.create(
            username="verified",
            email="verified@test.com",
            password="password",
        )
        EmailAddress.objects.create(
            user=self.verified_user,
            email="verified@test.com",
            primary=True,
            verified=True,
        )

        self.unverified_user = User.objects.create(
            username="unverified",
            email="unverified@test.com",
            password="password",
        )
        EmailAddress.objects.create(
            user=self.unverified_user,
            email="unverified@test.com",
            primary=True,
            verified=False,
        )

    def _make_bounce_obj(self, bounce_type, emails):
        return {
            "bounceType": bounce_type,
            "bouncedRecipients": [{"emailAddress": e} for e in emails],
        }

    def _make_complaint_obj(self, emails):
        return {
            "complainedRecipients": [{"emailAddress": e} for e in emails],
        }


class TestHandleBounce(BounceHandlerTestBase):
    def test_permanent_bounce_verified_user_sets_flag(self):
        bounce_obj = self._make_bounce_obj("Permanent", ["verified@test.com"])
        handle_bounce(
            sender=None, mail_obj={}, bounce_obj=bounce_obj, raw_message={}
        )
        self.verified_user.refresh_from_db()
        self.verified_user.profile.refresh_from_db()
        self.assertTrue(self.verified_user.is_active)
        self.assertTrue(self.verified_user.profile.email_bounced)
        self.assertIsNotNone(self.verified_user.profile.email_bounced_at)

    def test_permanent_bounce_unverified_user_deactivates(self):
        bounce_obj = self._make_bounce_obj(
            "Permanent", ["unverified@test.com"]
        )
        handle_bounce(
            sender=None, mail_obj={}, bounce_obj=bounce_obj, raw_message={}
        )
        self.unverified_user.refresh_from_db()
        self.unverified_user.profile.refresh_from_db()
        self.assertFalse(self.unverified_user.is_active)
        self.assertFalse(self.unverified_user.profile.email_bounced)

    def test_transient_bounce_no_action(self):
        bounce_obj = self._make_bounce_obj("Transient", ["verified@test.com"])
        handle_bounce(
            sender=None, mail_obj={}, bounce_obj=bounce_obj, raw_message={}
        )
        self.verified_user.refresh_from_db()
        self.verified_user.profile.refresh_from_db()
        self.assertTrue(self.verified_user.is_active)
        self.assertFalse(self.verified_user.profile.email_bounced)

    def test_bounce_nonexistent_email_no_error(self):
        bounce_obj = self._make_bounce_obj("Permanent", ["nobody@nowhere.com"])
        handle_bounce(
            sender=None, mail_obj={}, bounce_obj=bounce_obj, raw_message={}
        )


class TestHandleComplaint(BounceHandlerTestBase):
    def test_complaint_verified_user_sets_flag(self):
        complaint_obj = self._make_complaint_obj(["verified@test.com"])
        handle_complaint(
            sender=None,
            mail_obj={},
            complaint_obj=complaint_obj,
            raw_message={},
        )
        self.verified_user.refresh_from_db()
        self.verified_user.profile.refresh_from_db()
        self.assertTrue(self.verified_user.is_active)
        self.assertTrue(self.verified_user.profile.email_bounced)

    def test_complaint_unverified_user_deactivates(self):
        complaint_obj = self._make_complaint_obj(["unverified@test.com"])
        handle_complaint(
            sender=None,
            mail_obj={},
            complaint_obj=complaint_obj,
            raw_message={},
        )
        self.unverified_user.refresh_from_db()
        self.assertFalse(self.unverified_user.is_active)


class TestBounceHandlerMissingProfile(BounceHandlerTestBase):
    """Tests that bounce handling works when user has no Profile."""

    def test_permanent_bounce_creates_profile_and_sets_flag(self):
        """Bounce for a verified user without a profile should
        create the profile and set email_bounced."""
        Profile.objects.filter(user=self.verified_user).delete()
        self.assertFalse(
            Profile.objects.filter(user=self.verified_user).exists()
        )

        bounce_obj = self._make_bounce_obj("Permanent", ["verified@test.com"])
        handle_bounce(
            sender=None,
            mail_obj={},
            bounce_obj=bounce_obj,
            raw_message={},
        )

        self.assertTrue(
            Profile.objects.filter(user=self.verified_user).exists()
        )
        profile = Profile.objects.get(user=self.verified_user)
        self.assertTrue(profile.email_bounced)
        self.assertIsNotNone(profile.email_bounced_at)
