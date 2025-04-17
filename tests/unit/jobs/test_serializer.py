import pytest
from unittest.mock import MagicMock

from jobs.serializers import (
    ChallengeSubmissionManagementSerializer,
    LeaderboardDataSerializer,
)


@pytest.mark.django_db
def test_leaderboard_data_serializer_init():
    serializer = LeaderboardDataSerializer()
    assert isinstance(serializer, LeaderboardDataSerializer)


@pytest.mark.django_db
def test_leaderboard_data_serializer_get_participant_team_name():
    submission = MagicMock(participant_team=MagicMock(team_name="Team A"))
    leaderboard_data = MagicMock(submission=submission)
    serializer = LeaderboardDataSerializer()
    team_name = serializer.get_participant_team_name(leaderboard_data)
    assert team_name == "Team A"


@pytest.mark.django_db
def test_leaderboard_data_serializer_get_leaderboard_schema():
    leaderboard = MagicMock(schema="Schema A")
    leaderboard_data = MagicMock(leaderboard=leaderboard)
    serializer = LeaderboardDataSerializer()
    schema = serializer.get_leaderboard_schema(leaderboard_data)
    assert schema == "Schema A"


@pytest.mark.django_db
def test_challenge_submission_management_serializer_get_participant_team_members_email_ids_non_existent_team():
    obj = MagicMock(participant_team=MagicMock(team_name="NonExistentTeam"))
    serializer = ChallengeSubmissionManagementSerializer()
    email_ids = serializer.get_participant_team_members_email_ids(obj)
    assert email_ids == "Participant team does not exist"


@pytest.mark.django_db
def test_challenge_submission_management_serializer_get_participant_team_members_non_existent_team():
    obj = MagicMock(participant_team=MagicMock(team_name="NonExistentTeam"))
    serializer = ChallengeSubmissionManagementSerializer()
    members = serializer.get_participant_team_members(obj)
    assert members == "Participant team does not exist"


@pytest.mark.django_db
def test_challenge_submission_management_serializer_get_participant_team_members_affiliations_non_existent_team():
    obj = MagicMock(participant_team=MagicMock(team_name="NonExistentTeam"))
    serializer = ChallengeSubmissionManagementSerializer()
    affiliations = serializer.get_participant_team_members_affiliations(obj)
    assert affiliations == "Participant team does not exist"
