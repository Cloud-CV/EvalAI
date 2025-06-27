from challenges.models import Challenge
from django.contrib.auth.models import User
from django.core.exceptions import FieldError
from django.test import TestCase
from hosts.models import ChallengeHostTeam
from participants.models import ParticipantTeam
from participants.utils import has_participant_team_participated_in_challenge


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
