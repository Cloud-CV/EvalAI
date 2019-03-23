from datetime import timedelta

from django.urls import reverse_lazy, resolve
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge
from hosts.models import ChallengeHost, ChallengeHostTeam
from participants.models import ParticipantTeam


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

        self.invite_user = User.objects.create(
            username="otheruser",
            email="other@platform.com",
            password="other_secret_password",
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user
        )

        # user who create a challenge host team
        self.user2 = User.objects.create(
            username="someuser2", password="some_secret_password"
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Some Test Challenge Host Team", created_by=self.user2
        )

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user2,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
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
    def test_participant_team_list_url(self):
        self.url = reverse_lazy("participants:get_participant_team_list")
        self.assertEqual(str(self.url), "/api/participants/participant_team")
        resolver = resolve(self.url)
        self.assertEqual(
            resolver.view_name, "participants:get_participant_team_list"
        )

    def test_get_participant_team_challenge_list(self):
        self.url = reverse_lazy(
            "participants:get_participant_team_challenge_list",
            kwargs={"participant_team_pk": self.participant_team.pk},
        )
        self.assertEqual(
            str(self.url),
            "/api/participants/participant_team/%s/challenge"
            % (self.participant_team.pk),
        )
        resolver = resolve(self.url)
        self.assertEqual(
            resolver.view_name,
            "participants:get_participant_team_challenge_list",
        )

    def test_participant_team_detail_url(self):
        self.url = reverse_lazy(
            "participants:get_participant_team_details",
            kwargs={"pk": self.participant_team.pk},
        )
        self.assertEqual(
            str(self.url),
            "/api/participants/participant_team/%s"
            % (self.participant_team.pk),
        )
        resolver = resolve(self.url)
        self.assertEqual(
            resolver.view_name, "participants:get_participant_team_details"
        )

    def test_invite_participant_to_team_url(self):
        self.url = reverse_lazy(
            "participants:invite_participant_to_team",
            kwargs={"pk": self.participant_team.pk},
        )
        self.assertEqual(
            str(self.url),
            "/api/participants/participant_team/%s/invite"
            % (self.participant_team.pk),
        )
        resolver = resolve(self.url)
        self.assertEqual(
            resolver.view_name, "participants:invite_participant_to_team"
        )

    def test_delete_participant_from_team_url(self):
        self.url = reverse_lazy(
            "participants:delete_participant_from_team",
            kwargs={
                "participant_team_pk": self.participant_team.pk,
                "participant_pk": self.invite_user.pk,
            },
        )
        self.assertEqual(
            str(self.url),
            "/api/participants/participant_team/%s/participant/%s"
            % (self.participant_team.pk, self.invite_user.pk),
        )
        resolver = resolve(self.url)
        self.assertEqual(
            resolver.view_name, "participants:delete_participant_from_team"
        )

    def test_get_teams_and_corresponding_challenges_for_a_participant_url(
        self
    ):
        self.url = reverse_lazy(
            "participants:get_teams_and_corresponding_challenges_for_a_participant",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.assertEqual(
            str(self.url),
            "/api/participants/participant_teams/challenges/{}/user".format(
                self.challenge.pk
            ),
        )
        resolver = resolve(self.url)
        self.assertEqual(
            resolver.view_name,
            "participants:get_teams_and_corresponding_challenges_for_a_participant",
        )

    def test_remove_self_from_participant_team_url(self):
        self.url = reverse_lazy(
            "participants:remove_self_from_participant_team",
            kwargs={"participant_team_pk": self.participant_team.pk},
        )
        self.assertEqual(
            str(self.url),
            "/api/participants/remove_self_from_participant_team/%s"
            % (self.participant_team.pk),
        )
        resolver = resolve(self.url)
        self.assertEqual(
            resolver.view_name,
            "participants:remove_self_from_participant_team",
        )
