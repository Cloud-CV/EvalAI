from django.test import TestCase
from django.contrib.auth.models import User

from hosts.models import ChallengeHost, ChallengeHostTeam


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
        first_user = User.objects.create(username="user1", email="user1@test.com", password="password")
        second_user = User.objects.create(username="user2", email="user2@test.com", password="password")
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

        other_team = ChallengeHostTeam.objects.create(team_name="Other Team", created_by=self.user)
        other_user = User.objects.create(username="other", email="other@test.com", password="password")
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
