# pylint: disable=attribute-defined-outside-init,too-many-instance-attributes
import json
from datetime import timedelta

from accounts.models import Profile
from allauth.account.models import EmailAddress
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse_lazy
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam
from participants.views import invite_participant_to_team
from rest_framework import status
from rest_framework.test import (
    APIClient,
    APIRequestFactory,
    APITestCase,
    force_authenticate,
)


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

        self.participant = Participant.objects.create(
            user=self.user, team=self.participant_team, status=Participant.SELF
        )

        self.participant_profile = Profile.objects.get(user=self.user)

        self.client.force_authenticate(user=self.user)


class GetParticipantTeamTest(BaseAPITestClass):

    url = reverse_lazy("participants:get_participant_team_list")

    def setUp(self):
        super().setUp()

        self.user2 = User.objects.create(
            username="user2",
            email="user2@platform.com",
            password="user2_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@platform.com",
            primary=True,
            verified=True,
        )

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

        self.participant2_profile = Profile.objects.get(user=self.user2)

    def test_get_challenge(self):
        expected = [
            {
                "id": self.participant_team.pk,
                "team_name": self.participant_team.team_name,
                "created_by": self.user.username,
                "team_url": self.participant_team.team_url,
                "members": [
                    {
                        "member_name": self.participant.user.username,
                        "status": self.participant.status,
                        "first_name": self.participant.user.first_name,
                        "last_name": self.participant.user.last_name,
                        "email": self.participant.user.email,
                        "profile": {
                            "affiliation": self.participant_profile.affiliation,
                            "github_url": self.participant_profile.github_url,
                            "google_scholar_url": self.participant_profile.google_scholar_url,
                            "linkedin_url": self.participant_profile.linkedin_url,
                            "address_street": self.participant_profile.address_street,
                            "address_city": self.participant_profile.address_city,
                            "address_state": self.participant_profile.address_state,
                            "address_country": self.participant_profile.address_country,
                            "university": self.participant_profile.university,
                        },
                    },
                    {
                        "member_name": self.participant2.user.username,
                        "status": self.participant2.status,
                        "first_name": self.participant2.user.first_name,
                        "last_name": self.participant2.user.last_name,
                        "email": self.participant2.user.email,
                        "profile": {
                            "affiliation": self.participant2_profile.affiliation,
                            "github_url": self.participant2_profile.github_url,
                            "google_scholar_url": self.participant2_profile.google_scholar_url,
                            "linkedin_url": self.participant2_profile.linkedin_url,
                            "address_street": self.participant2_profile.address_street,
                            "address_city": self.participant2_profile.address_city,
                            "address_state": self.participant2_profile.address_state,
                            "address_country": self.participant2_profile.address_country,
                            "university": self.participant2_profile.university,
                        },
                    },
                ],
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(
            json.loads(json.dumps(response.data["results"], default=str)),
            json.loads(json.dumps(expected, default=str)),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_n_plus_one_queries_for_participant_teams(self):
        """
        Test that the participant_team_list endpoint doesn't have N+1 query issues.
        The number of queries should remain bounded regardless of:
        - Number of participant teams
        - Number of participants per team
        - Number of user profiles

        Before the fix, queries grew as:
        - 1 query per team for participants
        - 1 query per participant for user
        - 1 query per participant for profile

        After the fix using prefetch_related with select_related:
        - 1 query for teams
        - 1 query for participants with users and profiles (prefetched)
        """
        # Create additional teams with multiple participants
        additional_teams = []
        for i in range(3):
            # Create a new user for each team
            team_creator = User.objects.create(
                username=f"team_creator_{i}",
                email=f"team_creator_{i}@platform.com",
                password="password",
            )
            EmailAddress.objects.create(
                user=team_creator,
                email=f"team_creator_{i}@platform.com",
                primary=True,
                verified=True,
            )

            # Create the team
            team = ParticipantTeam.objects.create(
                team_name=f"Test Team {i}",
                created_by=team_creator,
            )
            additional_teams.append(team)

            # Add the creator as a participant
            Participant.objects.create(
                user=team_creator,
                status=Participant.SELF,
                team=team,
            )

            # Add the main user to each team (so they show up in the response)
            Participant.objects.create(
                user=self.user,
                status=Participant.ACCEPTED,
                team=team,
            )

            # Add additional participants to each team
            for j in range(2):
                member = User.objects.create(
                    username=f"team_{i}_member_{j}",
                    email=f"team_{i}_member_{j}@platform.com",
                    password="password",
                )
                EmailAddress.objects.create(
                    user=member,
                    email=f"team_{i}_member_{j}@platform.com",
                    primary=True,
                    verified=True,
                )
                Participant.objects.create(
                    user=member,
                    status=Participant.ACCEPTED,
                    team=team,
                )

        # Now we have:
        # - 1 original team with 2 participants
        # - 3 additional teams with 4 participants each (creator + main user + 2 members)
        # Total: 4 teams, 14 participants

        # Capture queries during the request
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(self.url, {})

        query_count = len(context)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Should return 4 teams (original + 3 new ones where user is a
        # participant)
        self.assertEqual(len(response.data["results"]), 4)

        # With the N+1 fix using prefetch_related and select_related:
        # - Queries should be bounded regardless of team/participant count
        # - Without the fix, we'd have: 4 (teams) + 14 (users) + 14 (profiles) = 32+ queries
        # - With the fix, we expect roughly:
        #   - 1 for participant IDs
        #   - 1 for teams
        #   - 1 for participants with users and profiles (prefetched)
        #   - Plus auth/session overhead (~5-10 queries)
        # Total should be under 20 queries
        self.assertLessEqual(
            query_count,
            20,
            f"Too many queries ({query_count}) - possible N+1 issue. "
            f"Queries: {[q['sql'][:100] for q in context.captured_queries]}",
        )


class CreateParticipantTeamTest(BaseAPITestClass):

    url = reverse_lazy("participants:get_participant_team_list")

    def setUp(self):
        super().setUp()
        self.data = {"team_name": "New Participant Team"}

    def test_create_participant_team_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_participant_team_with_team_name_same_as_with_existing_team(
        self,
    ):

        expected = {
            "team_name": [
                "participant team with this team name already exists."
            ]
        }

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Creating team with same team name
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected)

    def test_create_participant_team_with_no_data(self):
        del self.data["team_name"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetParticularParticipantTeam(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "participants:get_participant_team_details",
            kwargs={"pk": self.participant_team.pk},
        )

        self.user2 = User.objects.create(
            username="user2",
            email="user2@platform.com",
            password="user2_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@platform.com",
            primary=True,
            verified=True,
        )

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

        self.participant2_profile = Profile.objects.get(user=self.user2)

    def test_get_particular_participant_team(self):
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.participant_team.team_name,
            "created_by": self.user.username,
            "team_url": self.participant_team.team_url,
            "members": [
                {
                    "member_name": self.participant.user.username,
                    "status": self.participant.status,
                    "first_name": self.participant.user.first_name,
                    "last_name": self.participant.user.last_name,
                    "email": self.participant.user.email,
                    "profile": {
                        "affiliation": self.participant_profile.affiliation,
                        "github_url": self.participant_profile.github_url,
                        "google_scholar_url": self.participant_profile.google_scholar_url,
                        "linkedin_url": self.participant_profile.linkedin_url,
                        "address_street": self.participant_profile.address_street,
                        "address_city": self.participant_profile.address_city,
                        "address_state": self.participant_profile.address_state,
                        "address_country": self.participant_profile.address_country,
                        "university": self.participant_profile.university,
                    },
                },
                {
                    "member_name": self.participant2.user.username,
                    "status": self.participant2.status,
                    "first_name": self.participant2.user.first_name,
                    "last_name": self.participant2.user.last_name,
                    "email": self.participant2.user.email,
                    "profile": {
                        "affiliation": self.participant2_profile.affiliation,
                        "github_url": self.participant2_profile.github_url,
                        "google_scholar_url": self.participant2_profile.google_scholar_url,
                        "linkedin_url": self.participant2_profile.linkedin_url,
                        "address_street": self.participant2_profile.address_street,
                        "address_city": self.participant2_profile.address_city,
                        "address_state": self.participant2_profile.address_state,
                        "address_country": self.participant2_profile.address_country,
                        "university": self.participant2_profile.university,
                    },
                },
            ],
        }

        response = self.client.get(self.url, {})
        self.assertEqual(
            json.loads(json.dumps(response.data, default=str)),
            json.loads(json.dumps(expected, default=str)),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_participant_team_does_not_exist(self):
        self.url = reverse_lazy(
            "participants:get_participant_team_details",
            kwargs={"pk": self.participant_team.pk + 1},
        )
        expected = {"error": "ParticipantTeam does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class UpdateParticularParticipantTeam(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "participants:get_participant_team_details",
            kwargs={"pk": self.participant_team.pk},
        )

        self.partial_update_participant_team_name = (
            "Partial Update Participant Team"
        )
        self.update_participant_team_name = "Update Test Participant Team"
        self.data = {"team_name": self.update_participant_team_name}

    def test_particular_participant_team_partial_update(self):
        self.partial_update_data = {
            "team_name": self.partial_update_participant_team_name
        }
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.partial_update_participant_team_name,
            "created_by": self.user.username,
            "team_url": self.participant_team.team_url,
        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_participant_team_update(self):
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.update_participant_team_name,
            "created_by": self.user.username,
            "team_url": self.participant_team.team_url,
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_participant_team_update_with_no_data(self):
        self.data = {"team_name": ""}
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteParticularParticipantTeam(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "participants:get_participant_team_details",
            kwargs={"pk": self.participant_team.pk},
        )

    # TODO: Add the test back with the API
    # def test_particular_participant_team_delete(self):
    #     response = self.client.delete(self.url, {})
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class InviteParticipantToTeamTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()

        self.user1 = User.objects.create(
            username="user1",
            email="user1@platform.com",
            password="user1_password",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@platform.com",
            primary=True,
            verified=True,
        )

        self.participant_team1 = ParticipantTeam.objects.create(
            team_name="Team A", created_by=self.user1
        )

        self.participant1 = Participant.objects.create(
            user=self.user1,
            status=Participant.ACCEPTED,
            team=self.participant_team1,
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Host Team 1", created_by=self.user1
        )

        self.data = {"email": self.invite_user.email}
        self.url = reverse_lazy(
            "participants:invite_participant_to_team",
            kwargs={"pk": self.participant_team.pk},
        )

    def test_invite_participant_to_team_with_all_data(self):
        expected = {"message": "User has been successfully added to the team!"}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_invite_participant_to_team_with_no_data(self):
        del self.data["email"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_blocked_when_team_in_require_complete_profile_challenge_and_invitee_profile_incomplete(
        self,
    ):
        """Inviting a user with incomplete profile to a team that is in an
        active require_complete_profile challenge must be rejected."""
        host_team = ChallengeHostTeam.objects.create(
            team_name="Host Team", created_by=self.user
        )
        challenge = Challenge.objects.create(
            title="Require Profile Challenge",
            creator=host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=10),
        )
        challenge.participant_teams.add(self.participant_team)
        # invite_user has no first_name/last_name/address, so profile
        # incomplete
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertIn("error", response.data)
        self.assertIn("complete profile", response.data["error"])

    def test_invite_self_to_team(self):
        self.data = {"email": self.user.email}
        expected = {"error": "User is already part of the team!"}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_to_other_team_which_doesnot_belong_to_user(self):
        temp_user = User.objects.create(
            username="temp_user", password="test_password"
        )
        temp_participant_team = ParticipantTeam.objects.create(
            team_name="Test Team 1", created_by=temp_user
        )

        expected = {"error": "You are not a member of this team!"}

        self.url = reverse_lazy(
            "participants:invite_participant_to_team",
            kwargs={"pk": temp_participant_team.pk},
        )

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_user_which_does_not_exist_to_team(self):
        self.data = {"email": "userwhichdoesnotexist@platform.com"}
        expected = {"error": "User does not exist with this email address!"}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_participant_team_for_invite_does_not_exist(self):
        self.url = reverse_lazy(
            "participants:invite_participant_to_team",
            kwargs={"pk": self.participant_team.pk + 2},
        )
        expected = {"error": "Participant Team does not exist"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_when_team_participants_emails_are_banned(self):
        self.challenge1 = Challenge.objects.create(
            title="Test Challenge 1",
            short_description="Short description for test challenge 1",
            description="Description for test challenge 1",
            terms_and_conditions="Terms and conditions for test challenge 1",
            submission_guidelines="Submission guidelines for test challenge 1",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            banned_email_ids=["user1@platform.com"],
            leaderboard_description="Lorem ipsum dolor sit amet, consectetur adipiscing elit",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.challenge1.participant_teams.add(self.participant_team1)
        self.data = {"email": self.invite_user.email}
        self.client.force_authenticate(user=self.user1)
        self.url = reverse_lazy(
            "participants:invite_participant_to_team",
            kwargs={"pk": self.participant_team1.pk},
        )

        response = self.client.post(self.url, self.data)
        message = (
            f"You cannot invite as you're a part of {self.participant_team1.team_name} "
            "team and it has been banned from this challenge. Please contact the "
            "challenge host."
        )
        expected = {"error": message}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_when_invited_user_is_banned(self):
        self.challenge1 = Challenge.objects.create(
            title="Test Challenge 1",
            short_description="Short description for test challenge 1",
            description="Description for test challenge 1",
            terms_and_conditions="Terms and conditions for test challenge 1",
            submission_guidelines="Submission guidelines for test challenge 1",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            banned_email_ids=["other@platform.com"],
            leaderboard_description="Lorem ipsum dolor sit amet, consectetur adipiscing elit",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        self.challenge1.participant_teams.add(self.participant_team1)
        self.data = {"email": self.invite_user.email}
        self.client.force_authenticate(user=self.user1)
        self.url = reverse_lazy(
            "participants:invite_participant_to_team",
            kwargs={"pk": self.participant_team1.pk},
        )
        response = self.client.post(self.url, self.data)
        message = (
            "You cannot invite as the invited user has been banned "
            "from this challenge. Please contact the challenge host."
        )
        expected = {"error": message}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_when_invited_user_is_in_blocked_domains(self):
        self.challenge1 = Challenge.objects.create(
            title="Test Challenge 1",
            short_description="Short description for test challenge 1",
            description="Description for test challenge 1",
            terms_and_conditions="Terms and conditions for test challenge 1",
            submission_guidelines="Submission guidelines for test challenge 1",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            blocked_email_domains=["platform.com"],
            leaderboard_description="Lorem ipsum dolor sit amet, consectetur adipiscing elit",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        self.challenge1.participant_teams.add(self.participant_team1)
        self.data = {"email": self.invite_user.email}
        self.client.force_authenticate(user=self.user1)
        self.url = reverse_lazy(
            "participants:invite_participant_to_team",
            kwargs={"pk": self.participant_team1.pk},
        )

        response = self.client.post(self.url, self.data)
        expected = {
            "error": (
                "Sorry, users with platform.com email domain(s) are not allowed "
                "to participate in this challenge."
            )
        }
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_when_invited_user_is_not_in_allowed_domains(self):
        self.challenge1 = Challenge.objects.create(
            title="Test Challenge 1",
            short_description="Short description for test challenge 1",
            description="Description for test challenge 1",
            terms_and_conditions="Terms and conditions for test challenge 1",
            submission_guidelines="Submission guidelines for test challenge 1",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            allowed_email_domains=["example1"],
            leaderboard_description="Lorem ipsum dolor sit amet, consectetur adipiscing elit",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        self.challenge1.participant_teams.add(self.participant_team1)
        self.data = {"email": self.invite_user.email}
        self.client.force_authenticate(user=self.user1)
        self.url = reverse_lazy(
            "participants:invite_participant_to_team",
            kwargs={"pk": self.participant_team1.pk},
        )

        response = self.client.post(self.url, self.data)
        expected = {
            "error": (
                "Sorry, users with example1 email domain(s) are only allowed "
                "to participate in this challenge."
            )
        }

        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_participant_to_team_when_user_cannot_be_invited(self):
        """
        NOTE
        user: host user
        user1: participant 1
        user2: participant 2
        """
        self.user2 = User.objects.create(
            username="user2",
            email="user2@platform.com",
            password="user2_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@platform.com",
            primary=True,
            verified=True,
        )

        self.user3 = User.objects.create(
            username="user3",
            email="user3@platform.com",
            password="user3_password",
        )

        EmailAddress.objects.create(
            user=self.user3,
            email="user3@platform.com",
            primary=True,
            verified=True,
        )

        self.participant_team2 = ParticipantTeam.objects.create(
            team_name="Participant Team created by user 2",
            created_by=self.user2,
        )

        self.participant_team3 = ParticipantTeam.objects.create(
            team_name="Participant Team created by user 3",
            created_by=self.user3,
        )

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team2,
        )

        self.participant3 = Participant.objects.create(
            user=self.user3,
            status=Participant.ACCEPTED,
            team=self.participant_team3,
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
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
            leaderboard_description=None,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.client.force_authenticate(user=self.user2)

        self.challenge.participant_teams.add(self.participant_team2)
        self.challenge.participant_teams.add(self.participant_team3)

        self.data = {"email": self.user3.email}
        self.url = reverse_lazy(
            "participants:invite_participant_to_team",
            kwargs={"pk": self.participant_team2.pk},
        )

        expected = {
            "error": "Sorry, the invited user has already participated "
            "in atleast one of the challenges which you are already"
            " a part of. Please try creating a new team and then invite."
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class InviteParticipantRequireProfileGuardTest(APITestCase):
    """Focused tests for require_complete_profile invite guard."""

    def setUp(self):
        self.factory = APIRequestFactory()
        self.inviter = User.objects.create_user(
            username="invite_guard_inviter",
            email="invite_guard_inviter@example.com",
            password="password",
        )
        EmailAddress.objects.create(
            user=self.inviter,
            email=self.inviter.email,
            primary=True,
            verified=True,
        )

        self.invitee = User.objects.create_user(
            username="invite_guard_invitee",
            email="invite_guard_invitee@example.com",
            password="password",
        )
        EmailAddress.objects.create(
            user=self.invitee,
            email=self.invitee.email,
            primary=True,
            verified=True,
        )

        self.team = ParticipantTeam.objects.create(
            team_name="Invite Guard Team", created_by=self.inviter
        )
        Participant.objects.create(
            user=self.inviter, status=Participant.SELF, team=self.team
        )

        self.host_team = ChallengeHostTeam.objects.create(
            team_name="Invite Guard Host Team", created_by=self.inviter
        )

    def _invite(self):
        request = self.factory.post(
            "/api/participants/participant_team/{}/invite".format(
                self.team.pk
            ),
            {"email": self.invitee.email},
            format="json",
        )
        force_authenticate(request, user=self.inviter)
        return invite_participant_to_team(request, self.team.pk)

    def test_invite_blocked_for_incomplete_invitee_when_active_require_profile_challenge(
        self,
    ):
        Challenge.objects.create(
            title="Require Profile Active",
            creator=self.host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=5),
        ).participant_teams.add(self.team)

        response = self._invite()

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertIn("complete profile", response.data["error"])

    def test_invite_allowed_for_complete_invitee_when_active_require_profile_challenge(
        self,
    ):
        self.invitee.first_name = "First"
        self.invitee.last_name = "Last"
        self.invitee.save()
        self.invitee.profile.address_street = "123 Street"
        self.invitee.profile.address_city = "City"
        self.invitee.profile.address_state = "State"
        self.invitee.profile.address_country = "Country"
        self.invitee.profile.university = "University"
        self.invitee.profile.save()

        Challenge.objects.create(
            title="Require Profile Active 2",
            creator=self.host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=5),
        ).participant_teams.add(self.team)

        response = self._invite()

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(
            response.data["message"],
            "User has been successfully added to the team!",
        )


class DeleteParticipantFromTeamTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()

        self.participant = Participant.objects.create(
            user=self.user, status=Participant.SELF, team=self.participant_team
        )

        self.user2 = User.objects.create(
            username="user2",
            email="user2@platform.com",
            password="user2_password",
        )

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

        self.url = reverse_lazy(
            "participants:delete_participant_from_team",
            kwargs={
                "participant_team_pk": self.participant_team.pk,
                "participant_pk": self.invite_user.pk,
            },
        )

    def test_participant_does_not_exist_in_team(self):
        self.url = reverse_lazy(
            "participants:delete_participant_from_team",
            kwargs={
                "participant_team_pk": self.participant_team.pk,
                "participant_pk": self.participant2.pk + 1,
            },
        )

        expected = {"error": "Participant does not exist"}

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_participant_team_does_not_exist(self):
        self.url = reverse_lazy(
            "participants:delete_participant_from_team",
            kwargs={
                "participant_team_pk": self.participant_team.pk + 1,
                "participant_pk": self.participant2.pk,
            },
        )

        expected = {"error": "ParticipantTeam does not exist"}

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_participant_is_admin_and_wants_to_delete_himself(self):
        self.url = reverse_lazy(
            "participants:delete_participant_from_team",
            kwargs={
                "participant_team_pk": self.participant_team.pk,
                "participant_pk": self.participant.pk,
            },
        )

        expected = {
            "error": "You are not allowed to remove yourself since you are admin. Please delete the team if you want to do so!"  # noqa: ignore=E501
        }

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_participant_does_not_have_permissions_to_remove_another_participant(
        self,
    ):
        self.url = reverse_lazy(
            "participants:delete_participant_from_team",
            kwargs={
                "participant_team_pk": self.participant_team.pk,
                "participant_pk": self.participant2.pk,
            },
        )

        self.user3 = User.objects.create(
            username="user3",
            email="user3@platform.com",
            password="user3_password",
        )

        EmailAddress.objects.create(
            user=self.user3,
            email="user3@platform.com",
            primary=True,
            verified=True,
        )

        self.participant3 = Participant.objects.create(
            user=self.user3,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

        self.client.force_authenticate(user=self.user3)

        expected = {
            "error": "Sorry, you do not have permissions to remove this participant"
        }

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_when_a_participant_is_successfully_removed_from_team(self):
        self.url = reverse_lazy(
            "participants:delete_participant_from_team",
            kwargs={
                "participant_team_pk": self.participant_team.pk,
                "participant_pk": self.participant2.pk,
            },
        )
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class GetTeamsAndCorrespondingChallengesForAParticipant(BaseAPITestClass):
    def setUp(self):
        super().setUp()

        self.user2 = User.objects.create(
            username="user2",
            email="user2@platform.com",
            password="user2_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@platform.com",
            primary=True,
            verified=True,
        )

        self.participant_team2 = ParticipantTeam.objects.create(
            team_name="Team B", created_by=self.user2
        )  # created by user2 and not user

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team2,
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Host Team 1", created_by=self.user2
        )

        self.challenge1 = Challenge.objects.create(
            title="Test Challenge 1",
            short_description="Short description for test challenge 1",
            description="Description for test challenge 1",
            terms_and_conditions="Terms and conditions for test challenge 1",
            submission_guidelines="Submission guidelines for test challenge 1",
            creator=self.challenge_host_team,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=False,
            is_registration_open=True,
            enable_forum=True,
            leaderboard_description="Lorem ipsum dolor sit amet, consectetur adipiscing elit",
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            github_repository="challenge1/github_repo",
        )
        self.challenge1.slug = (
            f"{self.challenge1.title.replace(' ', '-').lower()}-"
            f"{self.challenge1.pk}"
        )[:199]
        self.challenge1.save()

        self.challenge2 = Challenge.objects.create(
            title="Test Challenge 2",
            short_description="Short description for test challenge 2",
            description="Description for test challenge 2",
            terms_and_conditions="Terms and conditions for test challenge 2",
            submission_guidelines="Submission guidelines for test challenge 2",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.url = reverse_lazy(
            "participants:get_teams_and_corresponding_challenges_for_a_participant",
            kwargs={"challenge_pk": self.challenge1.pk},
        )

        self.time = timezone.now()

    def test_get_teams_and_corresponding_challenges_for_a_participant(self):

        self.challenge1.participant_teams.add(self.participant_team)
        self.challenge1.save()

        expected = {
            "challenge_participant_team_list": [
                {
                    "challenge": {
                        "id": self.challenge1.id,
                        "title": self.challenge1.title,
                        "description": self.challenge1.description,
                        "short_description": self.challenge1.short_description,
                        "terms_and_conditions": self.challenge1.terms_and_conditions,
                        "submission_guidelines": self.challenge1.submission_guidelines,
                        "evaluation_details": self.challenge1.evaluation_details,
                        "image": None,
                        "start_date": (
                            f"{self.challenge1.start_date.isoformat()}Z"
                        ).replace("+00:00", ""),
                        "end_date": (
                            f"{self.challenge1.end_date.isoformat()}Z"
                        ).replace("+00:00", ""),
                        "creator": {
                            "id": self.challenge_host_team.id,
                            "team_name": self.challenge_host_team.team_name,
                            "created_by": self.challenge_host_team.created_by.username,
                            "team_url": self.challenge_host_team.team_url,
                        },
                        "domain": self.challenge1.domain,
                        "domain_name": "Computer Vision",
                        "list_tags": self.challenge1.list_tags,
                        "has_prize": self.challenge1.has_prize,
                        "has_sponsors": self.challenge1.has_sponsors,
                        "published": self.challenge1.published,
                        "submission_time_limit": self.challenge1.submission_time_limit,
                        "is_registration_open": self.challenge1.is_registration_open,
                        "enable_forum": self.challenge1.enable_forum,
                        "leaderboard_description": self.challenge1.leaderboard_description,
                        "anonymous_leaderboard": self.challenge1.anonymous_leaderboard,
                        "manual_participant_approval": self.challenge1.manual_participant_approval,
                        "require_complete_profile": self.challenge1.require_complete_profile,
                        "is_active": True,
                        "allowed_email_domains": [],
                        "blocked_email_domains": [],
                        "banned_email_ids": [],
                        "approved_by_admin": False,
                        "is_approval_requested": False,
                        "forum_url": self.challenge1.forum_url,
                        "is_docker_based": self.challenge1.is_docker_based,
                        "is_static_dataset_code_upload": self.challenge1.is_static_dataset_code_upload,
                        "slug": self.challenge1.slug,
                        "max_docker_image_size": self.challenge1.max_docker_image_size,
                        "cli_version": self.challenge1.cli_version,
                        "remote_evaluation": self.challenge1.remote_evaluation,
                        "allow_resuming_submissions": self.challenge1.allow_resuming_submissions,
                        "allow_host_cancel_submissions": self.challenge1.allow_host_cancel_submissions,
                        "allow_cancel_running_submissions": self.challenge1.allow_cancel_running_submissions,
                        "allow_participants_resubmissions": self.challenge1.allow_participants_resubmissions,
                        "workers": self.challenge1.workers,
                        "created_at": (
                            f"{self.challenge1.created_at.isoformat()}Z"
                        ).replace("+00:00", ""),
                        "queue": self.challenge1.queue,
                        "worker_cpu_cores": 512,
                        "worker_memory": 1024,
                        "cpu_only_jobs": self.challenge1.cpu_only_jobs,
                        "job_cpu_cores": self.challenge1.job_cpu_cores,
                        "job_memory": self.challenge1.job_memory,
                        "uses_ec2_worker": self.challenge1.uses_ec2_worker,
                        "ec2_storage": self.challenge1.ec2_storage,
                        "ephemeral_storage": self.challenge1.ephemeral_storage,
                        "evaluation_module_error": self.challenge1.evaluation_module_error,
                        "worker_image_url": self.challenge1.worker_image_url,
                        "worker_instance_type": self.challenge1.worker_instance_type,
                        "sqs_retention_period": self.challenge1.sqs_retention_period,
                        "github_repository": self.challenge1.github_repository,
                        "github_branch": self.challenge1.github_branch,
                        "is_frozen": False,
                        "is_submission_paused": False,
                    },
                    "participant_team": {
                        "id": self.participant_team.id,
                        "team_name": self.participant_team.team_name,
                        "created_by": self.participant_team.created_by.username,
                        "team_url": self.participant_team.team_url,
                    },
                }
            ],
            "is_challenge_host": False,
        }
        response = self.client.get(self.url, {})
        # checking 'datetime_now' separately because of time difference in
        # microseconds
        self.assertTrue(
            abs(response.data["datetime_now"] - self.time)
            < timedelta(seconds=1)
        )
        # deleting field 'datetime_now' from response to check with expected
        # response without time field
        del response.data["datetime_now"]
        self.assertEqual(
            json.loads(json.dumps(response.data, default=str)),
            json.loads(json.dumps(expected, default=str)),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_teams_and_corresponding_challenges_for_a_participant_with_no_teams(
        self,
    ):
        """User with no participant teams returns empty list."""
        user_no_teams = User.objects.create(
            username="user_no_teams",
            email="user_no_teams@platform.com",
            password="password",
        )
        EmailAddress.objects.create(
            user=user_no_teams,
            email="user_no_teams@platform.com",
            primary=True,
            verified=True,
        )
        self.client.force_authenticate(user=user_no_teams)

        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["challenge_participant_team_list"], [])
        self.assertIn("is_challenge_host", response.data)

    def test_get_teams_and_corresponding_challenges_for_a_participant_team_with_no_challenges(  # noqa: E501
        self,
    ):
        """Participant team with no challenges returns (null, team) entry."""
        # Create a second team for the user that has no challenges
        participant_team_no_challenges = ParticipantTeam.objects.create(
            team_name="Team No Challenges", created_by=self.user
        )
        Participant.objects.create(
            user=self.user,
            status=Participant.ACCEPTED,
            team=participant_team_no_challenges,
        )

        # participant_team has challenge1; participant_team_no_challenges has
        # none
        self.challenge1.participant_teams.add(self.participant_team)

        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data["challenge_participant_team_list"]
        self.assertEqual(len(items), 2)

        # One entry with challenge, one with null challenge
        challenges = [item["challenge"] for item in items]
        participant_teams = [item["participant_team"] for item in items]
        self.assertIn(None, challenges)
        self.assertEqual(
            len([c for c in challenges if c is not None]),
            1,
        )
        team_names = [pt["team_name"] for pt in participant_teams]
        self.assertIn("Participant Team", team_names)
        self.assertIn("Team No Challenges", team_names)

    def test_get_teams_and_corresponding_challenges_for_a_participant_multiple_teams(
        self,
    ):
        """User in multiple teams gets correct challenge-team pairs."""
        # Add user to participant_team2 (second team)
        Participant.objects.create(
            user=self.user,
            status=Participant.ACCEPTED,
            team=self.participant_team2,
        )
        self.challenge1.participant_teams.add(self.participant_team)
        self.challenge2.participant_teams.add(self.participant_team2)

        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        items = response.data["challenge_participant_team_list"]
        self.assertEqual(len(items), 2)

        challenge_ids = [
            item["challenge"]["id"] if item["challenge"] else None
            for item in items
        ]
        team_ids = [item["participant_team"]["id"] for item in items]
        self.assertIn(self.challenge1.id, challenge_ids)
        self.assertIn(self.challenge2.id, challenge_ids)
        self.assertIn(self.participant_team.id, team_ids)
        self.assertIn(self.participant_team2.id, team_ids)

    def test_get_teams_and_corresponding_challenges_no_n_plus_one_multiple_teams(
        self,
    ):
        """Query count stays bounded with multiple participant teams (N+1 fix)."""
        # Add user to multiple teams
        for i in range(5):
            team = ParticipantTeam.objects.create(
                team_name=f"Team {i}",
                created_by=self.user,
            )
            Participant.objects.create(
                user=self.user,
                status=Participant.ACCEPTED,
                team=team,
            )
            challenge = Challenge.objects.create(
                title=f"Extra Challenge {i}",
                short_description=f"Short desc {i}",
                description=f"Desc {i}",
                creator=self.challenge_host_team,
                published=False,
                is_registration_open=True,
                enable_forum=True,
                anonymous_leaderboard=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
            )
            challenge.participant_teams.add(team)

        with CaptureQueriesContext(connection) as context:
            response = self.client.get(self.url, {})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # With N+1 fix: queries should not grow with number of teams
        # (1 participants + 1 is_challenge_host + 1 challenges + 1 prefetch)
        self.assertLessEqual(
            len(context),
            25,
            f"Too many queries ({len(context)}) - possible N+1 with multiple "
            "participant teams",
        )

    def test_get_participant_team_challenge_list(self):
        self.url = reverse_lazy(
            "participants:get_participant_team_challenge_list",
            kwargs={"participant_team_pk": self.participant_team.pk},
        )
        expected = [
            {
                "id": self.challenge1.id,
                "title": self.challenge1.title,
                "description": self.challenge1.description,
                "short_description": self.challenge1.short_description,
                "terms_and_conditions": self.challenge1.terms_and_conditions,
                "submission_guidelines": self.challenge1.submission_guidelines,
                "evaluation_details": self.challenge1.evaluation_details,
                "image": None,
                "start_date": (
                    f"{self.challenge1.start_date.isoformat()}Z"
                ).replace("+00:00", ""),
                "end_date": (
                    f"{self.challenge1.end_date.isoformat()}Z"
                ).replace("+00:00", ""),
                "creator": {
                    "id": self.challenge_host_team.id,
                    "team_name": self.challenge_host_team.team_name,
                    "created_by": self.challenge_host_team.created_by.username,
                    "team_url": self.challenge_host_team.team_url,
                },
                "domain": self.challenge1.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge1.list_tags,
                "has_prize": self.challenge1.has_prize,
                "has_sponsors": self.challenge1.has_sponsors,
                "published": self.challenge1.published,
                "submission_time_limit": self.challenge1.submission_time_limit,
                "is_registration_open": self.challenge1.is_registration_open,
                "enable_forum": self.challenge1.enable_forum,
                "leaderboard_description": self.challenge1.leaderboard_description,
                "anonymous_leaderboard": self.challenge1.anonymous_leaderboard,
                "manual_participant_approval": self.challenge1.manual_participant_approval,
                "require_complete_profile": self.challenge1.require_complete_profile,
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": False,
                "is_approval_requested": False,
                "forum_url": self.challenge1.forum_url,
                "is_docker_based": self.challenge1.is_docker_based,
                "is_static_dataset_code_upload": self.challenge1.is_static_dataset_code_upload,
                "slug": self.challenge1.slug,
                "max_docker_image_size": self.challenge1.max_docker_image_size,
                "cli_version": self.challenge1.cli_version,
                "remote_evaluation": self.challenge1.remote_evaluation,
                "allow_resuming_submissions": self.challenge1.allow_resuming_submissions,
                "allow_host_cancel_submissions": self.challenge1.allow_host_cancel_submissions,
                "allow_cancel_running_submissions": self.challenge1.allow_cancel_running_submissions,
                "allow_participants_resubmissions": self.challenge1.allow_participants_resubmissions,
                "workers": self.challenge1.workers,
                "created_at": (
                    f"{self.challenge1.created_at.isoformat()}Z"
                ).replace("+00:00", ""),
                "queue": self.challenge1.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge1.cpu_only_jobs,
                "job_cpu_cores": self.challenge1.job_cpu_cores,
                "job_memory": self.challenge1.job_memory,
                "uses_ec2_worker": self.challenge1.uses_ec2_worker,
                "ec2_storage": self.challenge1.ec2_storage,
                "ephemeral_storage": self.challenge1.ephemeral_storage,
                "evaluation_module_error": self.challenge1.evaluation_module_error,
                "worker_image_url": self.challenge1.worker_image_url,
                "worker_instance_type": self.challenge1.worker_instance_type,
                "sqs_retention_period": self.challenge1.sqs_retention_period,
                "github_repository": self.challenge1.github_repository,
                "github_branch": self.challenge1.github_branch,
                "is_frozen": False,
                "is_submission_paused": False,
            }
        ]

        self.challenge1.participant_teams.add(self.participant_team)
        self.challenge1.save()

        response = self.client.get(self.url, {})
        self.assertEqual(
            json.loads(json.dumps(response.data["results"], default=str)),
            json.loads(json.dumps(expected, default=str)),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_when_participant_team_hasnot_participated_in_any_challenge(self):

        expected = {
            "challenge_participant_team_list": [
                {
                    "challenge": None,
                    "participant_team": {
                        "id": self.participant_team.id,
                        "team_name": self.participant_team.team_name,
                        "created_by": self.participant_team.created_by.username,
                        "team_url": self.participant_team.team_url,
                    },
                }
            ],
            "is_challenge_host": False,
        }
        response = self.client.get(self.url, {})
        # checking 'datetime_now' separately because of time difference in
        # microseconds
        self.assertTrue(
            abs(response.data["datetime_now"] - self.time)
            < timedelta(seconds=1)
        )
        # deleting field 'datetime_now' from response to check with expected
        # response without time field
        del response.data["datetime_now"]
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_when_there_is_no_participant_team_of_user(self):

        self.participant_team.delete()

        expected = {
            "challenge_participant_team_list": [],
            "is_challenge_host": False,
        }

        response = self.client.get(self.url, {})
        # checking 'datetime_now' separately because of time difference in
        # microseconds
        self.assertTrue(
            abs(response.data["datetime_now"] - self.time)
            < timedelta(seconds=1)
        )
        # deleting field 'datetime_now' from response to check with expected
        # response without time field
        del response.data["datetime_now"]
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_no_n_plus_one_queries_with_multiple_challenges(self):
        """
        Test that the endpoint doesn't have N+1 query issues when a single
        participant team is part of many challenges.
        The number of queries should remain constant regardless of
        the number of challenges the participant team is part of.
        """
        # Create additional challenges and add participant team to them
        challenges = [self.challenge1]
        for i in range(5):
            challenge = Challenge.objects.create(
                title=f"Test Challenge {i + 3}",
                short_description=f"Short description for test challenge {i + 3}",
                description=f"Description for test challenge {i + 3}",
                terms_and_conditions=f"Terms for test challenge {i + 3}",
                submission_guidelines=f"Guidelines for test challenge {i + 3}",
                creator=self.challenge_host_team,
                published=False,
                is_registration_open=True,
                enable_forum=True,
                anonymous_leaderboard=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
            )
            challenges.append(challenge)

        # Add participant team to all challenges
        for challenge in challenges:
            challenge.participant_teams.add(self.participant_team)
            challenge.save()

        # The query count should be bounded (not grow with number of challenges)
        # With the N+1 fix: 1 participants + 1 is_challenge_host + 1 challenges
        # + 1 prefetch participant_teams (bounded, not O(n))

        # Capture queries during the request
        with CaptureQueriesContext(connection) as context:
            response = self.client.get(self.url, {})

        query_count = len(context)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            len(response.data["challenge_participant_team_list"]),
            len(challenges),
        )

        # With the N+1 fix, we expect a bounded number of queries
        # Without the fix, this would be 2*N queries (COUNT + SELECT per team)
        # We use 25 as a reasonable upper bound (includes auth, session, etc.)
        self.assertLessEqual(
            query_count,
            25,
            f"Too many queries ({query_count}) - possible N+1 issue",
        )


class RemoveSelfFromParticipantTeamTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()

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
            is_registration_open=True,
            enable_forum=True,
            leaderboard_description="Fusce quis sapien eget sem accumsan euismod",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.url = reverse_lazy(
            "participants:remove_self_from_participant_team",
            kwargs={"participant_team_pk": self.participant_team.pk},
        )

    def test_when_participant_team_does_not_exist(self):
        self.url = reverse_lazy(
            "participants:remove_self_from_participant_team",
            kwargs={"participant_team_pk": self.participant_team.pk + 1},
        )

        expected = {"error": "ParticipantTeam does not exist!"}

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_a_participant_is_successfully_removed_from_team(self):
        self.url = reverse_lazy(
            "participants:remove_self_from_participant_team",
            kwargs={"participant_team_pk": self.participant_team.pk},
        )
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_when_participant_team_has_taken_part_in_challenges(self):
        self.challenge.participant_teams.add(self.participant_team)

        expected = {
            "error": "Sorry, you cannot delete this team since it has taken part in challenge(s)!"
        }

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_participant_team_remove_when_no_participants_exists(self):
        self.url = reverse_lazy(
            "participants:remove_self_from_participant_team",
            kwargs={"participant_team_pk": self.participant_team.pk},
        )

        self.client.delete(self.url, {})
        participant_teams = ParticipantTeam.objects.all()
        self.assertEqual(participant_teams.count(), 0)


class RemoveParticipantTeamFromChallengeTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.user1 = User.objects.create(
            username="user1",
            email="user1@platform.com",
            password="user1_password",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@platform.com",
            primary=True,
            verified=True,
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Host Team 1", created_by=self.user1
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge 2",
            short_description="Short description for test challenge 1",
            description="Description for test challenge 1",
            terms_and_conditions="Terms and conditions for test challenge 1",
            submission_guidelines="Submission guidelines for test challenge 1",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            banned_email_ids=["user1@platform.com"],
            leaderboard_description="Lorem ipsum dolor sit amet, consectetur adipiscing elit",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        self.challenge.slug = (
            f"{self.challenge.title.replace(' ', '-').lower()}-"
            f"{self.challenge.pk}"
        )[:199]
        self.challenge.save()

        self.challenge.participant_teams.add(self.participant_team)

        self.url = reverse_lazy(
            "participants:remove_participant_team_from_challenge",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team.pk,
            },
        )

    def test_remove_participant_team_success(self):
        self.client.force_authenticate(user=self.participant_team.created_by)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_remove_participant_team_when_user_is_not_authorized(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(self.url, {})
        expected = {
            "error": "Sorry, you do not have permissions to remove this participant team"
        }
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_remove_participant_team_when_not_participated(self):
        self.challenge.participant_teams.remove(self.participant_team)
        self.client.force_authenticate(user=self.participant_team.created_by)
        response = self.client.post(self.url, {})
        expected = {"error": "Team has not participated in the challenge"}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_participant_team_when_team_has_submissions(self):
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                max_submissions_per_day=100000,
                max_submissions_per_month=100000,
                max_submissions=100000,
                codename="Phase Code Name",
                is_restricted_to_select_one_submission=True,
                is_partial_submission_evaluation_enabled=False,
            )

            self.submission = Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=challenge_phase,
                created_by=self.participant_team.created_by,
                status="submitted",
                input_file=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                method_name="Test Method",
                method_description="Test Description",
                project_url="http://testserver/",
                publication_url="http://testserver/",
                is_public=True,
            )

        self.client.force_authenticate(user=self.participant_team.created_by)
        response = self.client.post(self.url, {})
        expected = {
            "error": "Unable to remove team as you have already made submission to the challenge"
        }
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
