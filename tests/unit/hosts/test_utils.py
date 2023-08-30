from datetime import timedelta

from django.contrib.auth.models import AnonymousUser, User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework.test import APITestCase

from challenges.models import Challenge
from participants.models import ParticipantTeam
from hosts.models import ChallengeHost, ChallengeHostTeam
from hosts.utils import is_user_a_host_of_challenge, is_user_a_staff_or_host


class BaseTestClass(APITestCase):
    def setUp(self):

        self.host_user = User.objects.create(
            username="host_user",
            email="host_user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.host_user,
            email="host_user@test.com",
            primary=True,
            verified=True,
        )

        self.user = User.objects.create(
            username="user", email="user@test.com", password="secret_password"
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.host_user
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description for test challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
        )

        self.challenge_host = ChallengeHost.objects.create(
            user=self.host_user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge",
            created_by=self.host_user,
        )

        self.client.force_authenticate(user=self.host_user)


class TestChallengeHost(BaseTestClass):
    def test_is_user_a_host_of_challenge_with_anonymous_user(self):

        expected = False
        user = AnonymousUser()
        output = is_user_a_host_of_challenge(user, self.challenge.pk)
        self.assertEqual(output, expected)

    def test_is_user_a_host_of_challenge_with_authenticated_host_user(self):

        expected = True
        output = is_user_a_host_of_challenge(self.host_user, self.challenge.pk)
        self.assertEqual(output, expected)

    def test_is_user_a_host_of_challenge_with_authenticated_not_host_user(
        self,
    ):

        self.client.force_authenticate(user=self.user)
        expected = False
        output = is_user_a_host_of_challenge(self.user, self.challenge.pk)
        self.assertEqual(output, expected)


class TestUserisStafforHost(BaseTestClass):
    def setUp(self):
        self.user = User.objects.create(
            username="someuser1",
            email="user@test.com",
            password="secret_password",
            is_staff=True,
        )

        self.user2 = User.objects.create(
            username="someuser2",
            email="user2@test.com",
            password="secret_password2",
            is_staff=False,
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        EmailAddress.objects.create(
            user=self.user2, email="user2@test.com", primary=True, verified=True
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

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
        )

    def test_if_user_is_staff(self):
        self.assertTrue(is_user_a_staff_or_host(self.user, self.challenge.pk))

    def test_if_user_is_not_staff(self):
        self.assertFalse(is_user_a_staff_or_host(self.user2, self.challenge.pk))

    def test_if_user_is_host(self):
        self.user.is_staff = False
        self.user.save()
        self.assertTrue(is_user_a_staff_or_host(self.user, self.challenge.pk))

    def test_if_user_is_not_host(self):
        self.assertFalse(is_user_a_staff_or_host(self.user2, self.challenge.pk))

    def test_if_user_is_not_host_or_staff(self):
        self.assertFalse(is_user_a_staff_or_host(self.user2, self.challenge.pk))
