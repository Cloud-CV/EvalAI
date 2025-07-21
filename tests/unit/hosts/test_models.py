from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from hosts.models import (
    ChallengeHost,
    ChallengeHostTeam,
    ChallengeHostTeamInvitation,
)


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="user", email="user@test.com", password="password"
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )


class ChallengeHostTestCase(BaseTestCase):
    def setUp(self):
        super(ChallengeHostTestCase, self).setUp()

    def test__str__(self):
        user = self.challenge_host.user
        team_name = self.challenge_host.team_name
        permissions = self.challenge_host.permissions
        final_string = "{}:{}:{}".format(team_name, user, permissions)
        self.assertEqual(final_string, self.challenge_host.__str__())


class ChallengeHostTeamTestCase(BaseTestCase):
    def setUp(self):
        super(ChallengeHostTeamTestCase, self).setUp()

    def test__str__(self):
        team_name = self.challenge_host_team.team_name
        created_by = self.challenge_host_team.created_by
        self.assertEqual(
            "{}: {}".format(team_name, created_by),
            self.challenge_host_team.__str__(),
        )

    def test_get_all_challenge_host_email(self):
        first_user = User.objects.create(
            username="user1", email="user1@test.com", password="password"
        )
        second_user = User.objects.create(
            username="user2", email="user2@test.com", password="password"
        )
        ChallengeHost.objects.create(
            user=first_user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.READ,
        )
        ChallengeHost.objects.create(
            user=second_user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.PENDING,
            permissions=ChallengeHost.WRITE,
        )

        other_team = ChallengeHostTeam.objects.create(
            team_name="Other Team", created_by=self.user
        )
        other_user = User.objects.create(
            username="other", email="other@test.com", password="password"
        )
        ChallengeHost.objects.create(
            user=other_user,
            team_name=other_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )
        emails = self.challenge_host_team.get_all_challenge_host_email()
        self.assertEqual(len(emails), 3)
        self.assertIn("user@test.com", emails)
        self.assertIn("user1@test.com", emails)
        self.assertIn("user2@test.com", emails)
        self.assertNotIn("other@test.com", emails)
        self.assertIsInstance(emails, list)


class ChallengeHostTeamInvitationTestCase(BaseTestCase):
    def setUp(self):
        super(ChallengeHostTeamInvitationTestCase, self).setUp()
        self.invitation = ChallengeHostTeamInvitation.objects.create(
            email="invitee@test.com",
            team=self.challenge_host_team,
            invited_by=self.user,
            status="pending",
        )

    def test__str__(self):
        expected = f"{self.invitation.email} invitation to {self.invitation.team.team_name}"
        self.assertEqual(str(self.invitation), expected)

    def test_generate_invitation_key(self):
        """Test that invitation key is generated correctly"""
        key = self.invitation.generate_invitation_key()
        self.assertIsInstance(key, str)
        self.assertEqual(len(key), 32)  # UUID4 hex is 32 characters

    def test_save_generates_invitation_key(self):
        """Test that invitation key is auto-generated on save"""
        invitation = ChallengeHostTeamInvitation(
            email="new@test.com",
            team=self.challenge_host_team,
            invited_by=self.user,
        )
        # The invitation key might be empty string initially, not None
        self.assertFalse(invitation.invitation_key)
        invitation.save()
        self.assertIsNotNone(invitation.invitation_key)
        self.assertEqual(len(invitation.invitation_key), 32)

    def test_is_expired_fresh_invitation(self):
        """Test that fresh invitation is not expired"""
        self.assertFalse(self.invitation.is_expired())

    def test_is_expired_old_invitation(self):
        """Test that old invitation is expired"""
        # Manually set created_at to be older than expiry days
        old_date = timezone.now() - timedelta(
            days=self.invitation.INVITATION_EXPIRY_DAYS + 1
        )
        self.invitation.created_at = old_date
        self.invitation.save()
        self.assertTrue(self.invitation.is_expired())

    def test_is_usable_pending_invitation(self):
        """Test that pending invitation is usable"""
        self.assertTrue(self.invitation.is_usable())

    def test_is_usable_accepted_invitation(self):
        """Test that accepted invitation is not usable"""
        self.invitation.status = "accepted"
        self.invitation.save()
        self.assertFalse(self.invitation.is_usable())

    def test_is_usable_expired_invitation(self):
        """Test that expired invitation is not usable"""
        # Make invitation expired
        old_date = timezone.now() - timedelta(
            days=self.invitation.INVITATION_EXPIRY_DAYS + 1
        )
        self.invitation.created_at = old_date
        self.invitation.save()
        self.assertFalse(self.invitation.is_usable())

    def test_mark_as_expired_pending_expired_invitation(self):
        """Test marking expired pending invitation as expired"""
        # Make invitation expired
        old_date = timezone.now() - timedelta(
            days=self.invitation.INVITATION_EXPIRY_DAYS + 1
        )
        self.invitation.created_at = old_date
        self.invitation.save()

        self.invitation.mark_as_expired()
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, "expired")

    def test_mark_as_expired_fresh_invitation(self):
        """Test that fresh invitation is not marked as expired"""
        original_status = self.invitation.status
        self.invitation.mark_as_expired()
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, original_status)

    def test_mark_as_expired_already_accepted_invitation(self):
        """Test that accepted invitation is not changed when marking as expired"""
        self.invitation.status = "accepted"
        self.invitation.save()

        self.invitation.mark_as_expired()
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, "accepted")

    def test_expire_old_invitations_class_method(self):
        """Test the class method to expire old invitations"""
        # Create an expired invitation
        old_date = timezone.now() - timedelta(
            days=self.invitation.INVITATION_EXPIRY_DAYS + 1
        )
        expired_invitation = ChallengeHostTeamInvitation.objects.create(
            email="expired@test.com",
            team=self.challenge_host_team,
            invited_by=self.user,
            status="pending",
        )
        expired_invitation.created_at = old_date
        expired_invitation.save()

        # Create a fresh invitation
        fresh_invitation = ChallengeHostTeamInvitation.objects.create(
            email="fresh@test.com",
            team=self.challenge_host_team,
            invited_by=self.user,
            status="pending",
        )

        # Run the class method
        ChallengeHostTeamInvitation.expire_old_invitations()

        # Check that expired invitation was marked as expired
        expired_invitation.refresh_from_db()
        self.assertEqual(expired_invitation.status, "expired")

        # Check that fresh invitation was not changed
        fresh_invitation.refresh_from_db()
        self.assertEqual(fresh_invitation.status, "pending")

        # Check that our original invitation was not changed
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.status, "pending")

    def test_invitation_key_uniqueness(self):
        """Test that invitation keys are unique"""
        invitation1 = ChallengeHostTeamInvitation.objects.create(
            email="test1@test.com",
            team=self.challenge_host_team,
            invited_by=self.user,
        )
        invitation2 = ChallengeHostTeamInvitation.objects.create(
            email="test2@test.com",
            team=self.challenge_host_team,
            invited_by=self.user,
        )

        self.assertNotEqual(
            invitation1.invitation_key, invitation2.invitation_key
        )
        self.assertNotEqual(
            invitation1.invitation_key, self.invitation.invitation_key
        )
