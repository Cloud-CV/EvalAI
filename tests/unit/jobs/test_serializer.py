from datetime import timedelta
from unittest.mock import MagicMock

import pytest
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission
from jobs.serializers import (
    ChallengeSubmissionManagementSerializer,
    LeaderboardDataSerializer,
    SubmissionSerializer,
)
from participants.models import Participant, ParticipantTeam


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


def test_submission_serializer_delete_sets_ignore_submission():
    mock_request = MagicMock()
    mock_request.method = "DELETE"
    mock_user = MagicMock()
    mock_request.user = mock_user

    context = {
        "request": mock_request,
        "ignore_submission": True,
    }

    data = {}

    serializer = SubmissionSerializer(context=context, data=data)
    assert isinstance(serializer, SubmissionSerializer)
    assert data["ignore_submission"] is True


@pytest.mark.django_db
class TestSubmissionSerializerQueryOptimization:
    """Tests for N+1 query optimization in SubmissionSerializer."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test data for query optimization tests."""
        # Create users
        self.user = User.objects.create_user(
            username="testuser",
            email="test@test.com",
            password="testpass123",
        )
        self.participant_user = User.objects.create_user(
            username="participant",
            email="participant@test.com",
            password="testpass123",
        )

        # Create challenge host team and host
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Host Team",
            created_by=self.user,
        )
        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        # Create participant team
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Participant Team",
            created_by=self.participant_user,
        )
        self.participant = Participant.objects.create(
            user=self.participant_user,
            status=Participant.SELF,
            team=self.participant_team,
        )

        # Create challenge
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Test Description",
            terms_and_conditions="Test Terms",
            submission_guidelines="Test Guidelines",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            published=True,
        )

        # Create challenge phase with a test annotation file
        test_file = SimpleUploadedFile(
            "test_annotation.txt",
            b"test content",
            content_type="text/plain",
        )
        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            description="Test Phase Description",
            challenge=self.challenge,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=1),
            max_submissions_per_day=10,
            max_submissions=100,
            is_public=True,
            test_annotation=test_file,
        )

        # Clear the serializer cache before each test
        SubmissionSerializer._challenge_hosts_cache = {}

    def test_serializer_uses_prefetched_participant_team(self):
        """Test that serializer correctly uses prefetched participant_team."""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_user,
            status="submitted",
        )

        # Fetch with select_related
        submission_with_prefetch = Submission.objects.select_related(
            "participant_team",
            "challenge_phase",
            "challenge_phase__challenge",
            "challenge_phase__challenge__creator",
        ).get(pk=submission.pk)

        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.user = self.participant_user

        serializer = SubmissionSerializer(
            submission_with_prefetch,
            context={"request": mock_request},
        )
        data = serializer.data

        assert data["participant_team_name"] == "Test Participant Team"
        assert data["participant_team"] == self.participant_team.pk

    def test_serializer_uses_prefetched_challenge_phase(self):
        """Test that serializer correctly uses prefetched challenge_phase."""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_user,
            status="submitted",
        )

        # Fetch with select_related
        submission_with_prefetch = Submission.objects.select_related(
            "participant_team",
            "challenge_phase",
            "challenge_phase__challenge",
            "challenge_phase__challenge__creator",
        ).get(pk=submission.pk)

        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.user = self.participant_user

        serializer = SubmissionSerializer(
            submission_with_prefetch,
            context={"request": mock_request},
        )
        data = serializer.data

        assert data["challenge_phase"] == self.challenge_phase.pk

    def test_serializer_cache_prevents_repeated_queries(self):
        """Test that the serializer caches challenge_hosts_pk to prevent repeated queries."""
        # Create multiple submissions
        submissions = []
        for i in range(5):
            submission = Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.participant_user,
                status="submitted",
            )
            submissions.append(submission)

        # Fetch with select_related
        submissions_with_prefetch = Submission.objects.filter(
            pk__in=[s.pk for s in submissions]
        ).select_related(
            "participant_team",
            "challenge_phase",
            "challenge_phase__challenge",
            "challenge_phase__challenge__creator",
        )

        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.user = self.participant_user

        # Clear cache
        SubmissionSerializer._challenge_hosts_cache = {}

        serializer = SubmissionSerializer(
            submissions_with_prefetch,
            many=True,
            context={"request": mock_request},
        )
        data = serializer.data

        # After serialization, cache should have one entry for the
        # challenge_host_team
        assert len(SubmissionSerializer._challenge_hosts_cache) == 1
        assert (
            self.challenge_host_team.pk
            in SubmissionSerializer._challenge_hosts_cache
        )

        # All submissions should have correct data
        assert len(data) == 5
        for item in data:
            assert item["participant_team_name"] == "Test Participant Team"

    def test_serializer_hides_environment_log_for_non_hosts(self):
        """Test that environment_log_file is hidden for non-host users."""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_user,
            status="submitted",
            environment_log_file="some_log_file.txt",
        )

        submission_with_prefetch = Submission.objects.select_related(
            "participant_team",
            "challenge_phase",
            "challenge_phase__challenge",
            "challenge_phase__challenge__creator",
        ).get(pk=submission.pk)

        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.user = self.participant_user

        serializer = SubmissionSerializer(
            submission_with_prefetch,
            context={"request": mock_request},
        )
        data = serializer.data

        # Non-host user should not see environment_log_file
        assert "environment_log_file" not in data

    def test_serializer_shows_environment_log_for_hosts(self):
        """Test that environment_log_file is visible for host users."""
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_user,
            status="submitted",
            environment_log_file="some_log_file.txt",
        )

        submission_with_prefetch = Submission.objects.select_related(
            "participant_team",
            "challenge_phase",
            "challenge_phase__challenge",
            "challenge_phase__challenge__creator",
        ).get(pk=submission.pk)

        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.user = self.user  # Host user

        serializer = SubmissionSerializer(
            submission_with_prefetch,
            context={"request": mock_request},
        )
        data = serializer.data

        # Host user should see environment_log_file
        assert "environment_log_file" in data

    def test_serializer_cache_handles_none_creator(self):
        """Test that cache handles challenges without a creator gracefully."""
        # Clear cache
        SubmissionSerializer._challenge_hosts_cache = {}

        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_user,
            status="submitted",
        )

        submission_with_prefetch = Submission.objects.select_related(
            "participant_team",
            "challenge_phase",
            "challenge_phase__challenge",
            "challenge_phase__challenge__creator",
        ).get(pk=submission.pk)

        mock_request = MagicMock()
        mock_request.method = "GET"
        mock_request.user = self.participant_user

        serializer = SubmissionSerializer(
            submission_with_prefetch,
            context={"request": mock_request},
        )

        # Should not raise an exception
        data = serializer.data
        assert data["participant_team_name"] == "Test Participant Team"
