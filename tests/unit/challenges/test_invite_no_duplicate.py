from datetime import timedelta

from allauth.account.models import EmailAddress
from challenges.models import Challenge
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class InviteExistingUserNoDuplicateTest(APITestCase):
    """The invite flow must reuse an existing user rather than creating a duplicate."""

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.host_user = User.objects.create_user(
            username="host", email="host@test.com", password="password"
        )
        EmailAddress.objects.create(
            user=self.host_user,
            email="host@test.com",
            primary=True,
            verified=True,
        )

        self.existing_user = User.objects.create_user(
            username="existing_user",
            email="invitee@test.com",
            password="password",
        )
        EmailAddress.objects.create(
            user=self.existing_user,
            email="invitee@test.com",
            primary=True,
            verified=True,
        )

        self.host_team = ChallengeHostTeam.objects.create(
            team_name="TestHostTeam", created_by=self.host_user
        )
        ChallengeHost.objects.create(
            user=self.host_user,
            team_name=self.host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="short",
            description="desc",
            terms_and_conditions="terms",
            submission_guidelines="guidelines",
            creator=self.host_team,
            domain="CV",
            list_tags=["Paper"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
            approved_by_admin=True,
        )
        self.client.force_authenticate(user=self.host_user)

    def test_invite_does_not_create_duplicate_user(self):
        user_count_before = User.objects.filter(
            email="invitee@test.com"
        ).count()
        self.assertEqual(user_count_before, 1)

        url = reverse(
            "challenges:invite_users_to_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.post(
            url,
            {"emails": '["invitee@test.com"]'},
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
        )

        user_count_after = User.objects.filter(
            email="invitee@test.com"
        ).count()
        self.assertEqual(user_count_after, 1)

    def test_invite_creates_user_for_new_email(self):
        url = reverse(
            "challenges:invite_users_to_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.post(
            url,
            {"emails": '["newuser@test.com"]'},
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST],
        )

        self.assertTrue(User.objects.filter(email="newuser@test.com").exists())
