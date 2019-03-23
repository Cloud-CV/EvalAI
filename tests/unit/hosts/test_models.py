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
