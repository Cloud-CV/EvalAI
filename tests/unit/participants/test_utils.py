from challenges.models import Challenge
from django.contrib.auth.models import User
from django.core.exceptions import FieldError
from django.test import TestCase
from hosts.models import ChallengeHostTeam
from participants.models import Participant, ParticipantTeam
from participants.utils import (
    get_participant_team_id_of_user_for_a_challenge,
    has_participant_team_participated_in_challenge,
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
