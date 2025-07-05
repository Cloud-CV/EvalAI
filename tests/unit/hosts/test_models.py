from django.contrib.auth.models import User
from django.test import TestCase
from hosts.models import ChallengeHost, ChallengeHostTeam, ChallengeHostTeamInvitation
from datetime import timedelta
from django.utils import timezone


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
            email="invitee@example.com",
            team=self.challenge_host_team,
            invited_by=self.user,
            status="pending"
        )
    
    def test_invitation_key_generation(self):
        self.assertIsNotNone(self.invitation.invitation_key)
        self.assertEqual(len(self.invitation.invitation_key), 32) 
    
    def test_is_expired_method(self):
        self.assertFalse(self.invitation.is_expired())
        
        self.invitation.created_at = timezone.now() - timedelta(
            days=self.invitation.INVITATION_EXPIRY_DAYS + 1
        )
        self.invitation.save()
        
        self.assertTrue(self.invitation.is_expired())
    
    def test_is_usable_method(self):
        """Test invitation usability check"""
        self.assertTrue(self.invitation.is_usable())
        
        self.invitation.status = "accepted"
        self.invitation.save()
        self.assertFalse(self.invitation.is_usable())
        
        self.invitation.status = "pending"
        self.invitation.created_at = timezone.now() - timedelta(
            days=self.invitation.INVITATION_EXPIRY_DAYS + 1
        )
        self.invitation.save()
        self.assertFalse(self.invitation.is_usable())
    
    def test_mark_as_expired(self):
        """Test marking invitation as expired"""
        self.invitation.created_at = timezone.now() - timedelta(
            days=self.invitation.INVITATION_EXPIRY_DAYS + 1
        )
        self.invitation.save()
        
        self.assertEqual(self.invitation.status, "pending")
        self.invitation.mark_as_expired()
        self.assertEqual(self.invitation.status, "expired")

    def test_expire_old_invitations_class_method(self):
        """Test class method to expire old invitations"""
        expired_invitation = ChallengeHostTeamInvitation.objects.create(
            email="expired@example.com",
            team=self.challenge_host_team,
            invited_by=self.user,
            status="pending"
        )
        expired_invitation.created_at = timezone.now() - timedelta(
            days=ChallengeHostTeamInvitation.INVITATION_EXPIRY_DAYS + 1
        )
        expired_invitation.save()
        
        ChallengeHostTeamInvitation.expire_old_invitations()
        
        expired_invitation.refresh_from_db()
        self.assertEqual(expired_invitation.status, "expired")
    
    def test__str__(self):
        expected_str = "invitee@example.com invitation to Test Host Team"
        self.assertEqual(str(self.invitation), expected_str)

