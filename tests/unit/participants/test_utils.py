from datetime import timedelta

from challenges.models import Challenge
from django.contrib.auth.models import User
from django.core.exceptions import FieldError
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from participants.models import Participant, ParticipantTeam
from participants.utils import (
    get_participant_team_id_of_user_for_a_challenge,
    has_participant_team_participated_in_challenge,
    has_participated_in_require_complete_profile_challenge,
)


class TestHasParticipantTeamParticipatedInChallenge(TestCase):
    def test_field_error_for_wrong_related_name(self):
        user = User.objects.create(
            username="testuser", email="test@example.com"
        )
        team = ParticipantTeam.objects.create(
            team_name="team1", created_by=user
        )
        host_team = ChallengeHostTeam.objects.create(
            team_name="hostteam1", created_by=user
        )
        challenge = Challenge.objects.create(
            title="challenge1", creator=host_team
        )

        with self.assertRaises(FieldError):
            has_participant_team_participated_in_challenge(
                team.id, challenge.id
            )


class TestGetParticipantTeamIdOfUserForAChallenge(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="testuser", email="test@example.com"
        )
        self.other_user = User.objects.create(
            username="otheruser", email="other@example.com"
        )
        self.host_team = ChallengeHostTeam.objects.create(
            team_name="hostteam1", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="challenge1", creator=self.host_team
        )
        self.team = ParticipantTeam.objects.create(
            team_name="team1", created_by=self.user
        )

    def test_returns_team_id_when_user_participated_in_challenge(self):
        """Test that the function returns the team ID when user is part of a team that participated"""
        # Add user to participant team
        Participant.objects.create(
            user=self.user, team=self.team, status=Participant.ACCEPTED
        )
        # Add team to challenge
        self.challenge.participant_teams.add(self.team)

        result = get_participant_team_id_of_user_for_a_challenge(
            self.user, self.challenge.id
        )

        self.assertEqual(result, self.team.id)

    def test_returns_none_when_user_team_not_in_challenge(self):
        """Test that the function returns None when user's team did not participate"""
        # Add user to participant team but don't add team to challenge
        Participant.objects.create(
            user=self.user, team=self.team, status=Participant.ACCEPTED
        )

        result = get_participant_team_id_of_user_for_a_challenge(
            self.user, self.challenge.id
        )

        self.assertIsNone(result)

    def test_returns_none_when_user_has_no_teams(self):
        """Test that the function returns None when user is not part of any team"""
        result = get_participant_team_id_of_user_for_a_challenge(
            self.user, self.challenge.id
        )

        self.assertIsNone(result)

    def test_returns_correct_team_when_user_has_multiple_teams(self):
        """Test that the function returns the correct team when user has multiple teams"""
        # Create another team
        team2 = ParticipantTeam.objects.create(
            team_name="team2", created_by=self.user
        )

        # Add user to both teams
        Participant.objects.create(
            user=self.user, team=self.team, status=Participant.ACCEPTED
        )
        Participant.objects.create(
            user=self.user, team=team2, status=Participant.ACCEPTED
        )

        # Only add team2 to challenge
        self.challenge.participant_teams.add(team2)

        result = get_participant_team_id_of_user_for_a_challenge(
            self.user, self.challenge.id
        )

        self.assertEqual(result, team2.id)

    def test_returns_none_for_different_user(self):
        """Test that function returns None for a user who didn't participate"""
        # Add original user to team and challenge
        Participant.objects.create(
            user=self.user, team=self.team, status=Participant.ACCEPTED
        )
        self.challenge.participant_teams.add(self.team)

        # Query for different user
        result = get_participant_team_id_of_user_for_a_challenge(
            self.other_user, self.challenge.id
        )

        self.assertIsNone(result)

    def test_uses_single_query(self):
        """Test that the function uses a single database query (N+1 fix verification)"""
        # Create multiple teams for the user
        teams = []
        for i in range(5):
            team = ParticipantTeam.objects.create(
                team_name=f"team_{i}", created_by=self.user
            )
            Participant.objects.create(
                user=self.user, team=team, status=Participant.ACCEPTED
            )
            teams.append(team)

        # Add only the last team to challenge
        self.challenge.participant_teams.add(teams[-1])

        # Verify single query is used
        with self.assertNumQueries(1):
            result = get_participant_team_id_of_user_for_a_challenge(
                self.user, self.challenge.id
            )

        self.assertEqual(result, teams[-1].id)


class TestHasParticipatedInRequireCompleteProfileChallenge(TestCase):
    """Tests for has_participated_in_require_complete_profile_challenge."""

    def setUp(self):
        self.user = User.objects.create(
            username="testuser", email="test@example.com"
        )
        self.host_team = ChallengeHostTeam.objects.create(
            team_name="hostteam1", created_by=self.user
        )
        ChallengeHost.objects.create(
            user=self.user,
            team_name=self.host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="team1", created_by=self.user
        )
        Participant.objects.create(
            user=self.user,
            team=self.participant_team,
            status=Participant.SELF,
        )

    def test_returns_true_when_participated_in_active_require_complete_profile_challenge(
        self,
    ):
        """Returns True when user participated in an active challenge with require_complete_profile."""
        challenge = Challenge.objects.create(
            title="challenge1",
            creator=self.host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=30),
        )
        challenge.participant_teams.add(self.participant_team)

        self.assertTrue(
            has_participated_in_require_complete_profile_challenge(self.user)
        )

    def test_returns_false_when_challenge_has_ended(self):
        """Returns False when the require_complete_profile challenge has ended,
        allowing the user to edit profile fields again."""
        challenge = Challenge.objects.create(
            title="challenge1",
            creator=self.host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now() - timedelta(days=1),
        )
        challenge.participant_teams.add(self.participant_team)

        self.assertFalse(
            has_participated_in_require_complete_profile_challenge(self.user)
        )

    def test_returns_true_when_one_active_and_one_ended(self):
        """Returns True if at least one active require_complete_profile challenge exists."""
        ended_challenge = Challenge.objects.create(
            title="ended_challenge",
            creator=self.host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=60),
            end_date=timezone.now() - timedelta(days=1),
        )
        ended_challenge.participant_teams.add(self.participant_team)

        active_challenge = Challenge.objects.create(
            title="active_challenge",
            creator=self.host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=30),
        )
        active_challenge.participant_teams.add(self.participant_team)

        self.assertTrue(
            has_participated_in_require_complete_profile_challenge(self.user)
        )

    def test_returns_false_when_participated_in_normal_challenge(self):
        """Returns False when user participated in challenge without require_complete_profile."""
        challenge = Challenge.objects.create(
            title="challenge1",
            creator=self.host_team,
            require_complete_profile=False,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=30),
        )
        challenge.participant_teams.add(self.participant_team)

        self.assertFalse(
            has_participated_in_require_complete_profile_challenge(self.user)
        )

    def test_returns_false_when_not_participated(self):
        """Returns False when user has not participated in any challenge."""
        Challenge.objects.create(
            title="challenge1",
            creator=self.host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=30),
        )
        # Don't add participant_team to challenge

        self.assertFalse(
            has_participated_in_require_complete_profile_challenge(self.user)
        )
