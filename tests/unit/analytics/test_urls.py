from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse_lazy

from allauth.account.models import EmailAddress
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge
from hosts.models import ChallengeHostTeam


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Some Test Challenge Host Team", created_by=self.user
        )

        self.challenge = Challenge.objects.create(
            title="Some Test Challenge",
            short_description="Short description for some test challenge",
            description="Description for some test challenge",
            terms_and_conditions="Terms and conditions for some test challenge",
            submission_guidelines="Submission guidelines for some test challenge",
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        self.client.force_authenticate(user=self.user)


class TestStringMethods(BaseAPITestClass):
    def test_get_participant_teams_url(self):
        url = reverse_lazy(
            "analytics:download_all_participants",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.assertEqual(
            str(url),
            "/api/analytics/challenges/{0}/download_all_participants/".format(
                self.challenge.pk
            ),
        )
