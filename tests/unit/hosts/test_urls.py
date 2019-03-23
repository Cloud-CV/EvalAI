from django.urls import reverse_lazy
from rest_framework.test import APITestCase, APIClient
from hosts.models import ChallengeHost, ChallengeHostTeam
from django.contrib.auth.models import User


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
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

        self.client.force_authenticate(user=self.user)


class TestStringMethods(BaseAPITestClass):
    def test_host_urls(self):
        url = reverse_lazy("hosts:get_challenge_host_team_list")
        self.assertEqual(url, "/api/hosts/challenge_host_team/")

        url = reverse_lazy(
            "hosts:get_challenge_host_team_details",
            kwargs={"pk": self.challenge_host.pk},
        )
        self.assertEqual(
            url,
            "/api/hosts/challenge_host_team/" + str(self.challenge_host.pk),
        )

        url = reverse_lazy("hosts:create_challenge_host_team")
        self.assertEqual(url, "/api/hosts/create_challenge_host_team")

        url = reverse_lazy(
            "hosts:get_challenge_host_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )
        self.assertEqual(
            url,
            "/api/hosts/challenge_host_team/"
            + str(self.challenge_host_team.pk)
            + "/challenge_host",
        )

        url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "pk": self.challenge_host.pk,
            },
        )
        self.assertEqual(
            url,
            "/api/hosts/challenge_host_team/"
            + str(self.challenge_host_team.pk)
            + "/challenge_host/"
            + str(self.challenge_host.pk),
        )

        url = reverse_lazy(
            "hosts:remove_self_from_challenge_host_team",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )
        self.assertEqual(
            url,
            "/api/hosts/remove_self_from_challenge_host/"
            + str(self.challenge_host_team.pk),
        )

        url = reverse_lazy(
            "hosts:invite_host_to_team",
            kwargs={"pk": self.challenge_host_team.pk},
        )
        self.assertEqual(
            url,
            "/api/hosts/challenge_host_teams/"
            + str(self.challenge_host_team.pk)
            + "/invite",
        )
