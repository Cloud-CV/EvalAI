from django.contrib.auth.models import User
from django.db.models import Prefetch
from django.test import RequestFactory, TestCase
from participants.models import Participant, ParticipantTeam
from participants.serializers import (
    ChallengeParticipantSerializer,
    InviteParticipantToTeamSerializer,
    ParticipantSerializer,
    ParticipantTeamDetailSerializer,
)
from rest_framework import serializers


class TestChallengeParticipantSerializer(TestCase):
    """Tests for ChallengeParticipantSerializer (expects ParticipantTeam with participants)."""

    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            email="test@example.com",
        )
        self.empty_team = ParticipantTeam.objects.create(
            team_name="Empty Team",
            created_by=self.user,
        )

    def test_get_team_members_empty_team(self):
        """Team with no participants returns empty list."""
        serializer = ChallengeParticipantSerializer()
        result = serializer.get_team_members(self.empty_team)
        self.assertEqual(result, [])

    def test_get_team_members_email_ids_empty_team(self):
        """Team with no participants returns empty email list."""
        serializer = ChallengeParticipantSerializer()
        result = serializer.get_team_members_email_ids(self.empty_team)
        self.assertEqual(result, [])

    def test_get_team_members_with_participants(self):
        """Team with participants returns usernames."""
        participant_user = User.objects.create(
            username="member1",
            email="member1@example.com",
        )
        Participant.objects.create(
            user=participant_user,
            status=Participant.SELF,
            team=self.empty_team,
        )
        serializer = ChallengeParticipantSerializer()
        result = serializer.get_team_members(self.empty_team)
        self.assertEqual(result, ["member1"])

    def test_get_team_members_email_ids_with_participants(self):
        """Team with participants returns emails."""
        participant_user = User.objects.create(
            username="member1",
            email="member1@example.com",
        )
        Participant.objects.create(
            user=participant_user,
            status=Participant.SELF,
            team=self.empty_team,
        )
        serializer = ChallengeParticipantSerializer()
        result = serializer.get_team_members_email_ids(self.empty_team)
        self.assertEqual(result, ["member1@example.com"])


class TestInviteParticipantToTeamSerializer(TestCase):
    def test_validate_email_user_does_not_exist(self):
        user = User.objects.create(
            username="testuser", email="test@example.com"
        )
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user
        context = {"request": request, "participant_team": None}
        serializer = InviteParticipantToTeamSerializer(context=context)

        with self.assertRaisesMessage(Exception, "User does not exist"):
            serializer.validate_email("notfound@example.com")

    def test_validate_email_self_invite(self):
        user = User.objects.create(
            username="testuser", email="test@example.com"
        )
        factory = RequestFactory()
        request = factory.get("/")
        request.user = user
        context = {"request": request, "participant_team": None}
        serializer = InviteParticipantToTeamSerializer(context=context)
        with self.assertRaisesMessage(
            serializers.ValidationError, "A participant cannot invite himself"
        ):
            serializer.validate_email("test@example.com")


class TestParticipantTeamDetailSerializer(TestCase):
    def setUp(self):
        self.user1 = User.objects.create(
            username="user1",
            email="user1@test.com",
            first_name="First1",
            last_name="Last1",
        )
        self.user2 = User.objects.create(
            username="user2",
            email="user2@test.com",
            first_name="First2",
            last_name="Last2",
        )

        self.team = ParticipantTeam.objects.create(
            team_name="Test Team",
            created_by=self.user1,
        )

        self.participant1 = Participant.objects.create(
            user=self.user1,
            status=Participant.SELF,
            team=self.team,
        )
        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.team,
        )

    def test_get_members_returns_all_team_members(self):
        """Test that get_members returns all participants of a team."""
        serializer = ParticipantTeamDetailSerializer(self.team)
        data = serializer.data

        self.assertEqual(len(data["members"]), 2)
        member_names = [m["member_name"] for m in data["members"]]
        self.assertIn("user1", member_names)
        self.assertIn("user2", member_names)

    def test_get_members_with_prefetched_data(self):
        """
        Test that get_members works correctly with prefetched participants.
        This verifies the N+1 query fix works when data is prefetched.
        """
        # Query with prefetch_related (as done in the fixed view)
        team_with_prefetch = (
            ParticipantTeam.objects.filter(pk=self.team.pk)
            .prefetch_related(
                Prefetch(
                    "participants",
                    queryset=Participant.objects.select_related(
                        "user", "user__profile"
                    ),
                )
            )
            .first()
        )

        serializer = ParticipantTeamDetailSerializer(team_with_prefetch)
        data = serializer.data

        self.assertEqual(len(data["members"]), 2)
        member_names = [m["member_name"] for m in data["members"]]
        self.assertIn("user1", member_names)
        self.assertIn("user2", member_names)

    def test_serializer_includes_all_expected_fields(self):
        """Test that the serializer includes all expected fields."""
        serializer = ParticipantTeamDetailSerializer(self.team)
        data = serializer.data

        self.assertIn("id", data)
        self.assertIn("team_name", data)
        self.assertIn("created_by", data)
        self.assertIn("members", data)
        self.assertIn("team_url", data)

        # Check member fields
        member = data["members"][0]
        self.assertIn("member_name", member)
        self.assertIn("first_name", member)
        self.assertIn("last_name", member)
        self.assertIn("email", member)
        self.assertIn("status", member)
        self.assertIn("profile", member)


class TestParticipantSerializer(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="testuser",
            email="testuser@test.com",
            first_name="Test",
            last_name="User",
        )
        self.team = ParticipantTeam.objects.create(
            team_name="Test Team",
            created_by=self.user,
        )
        self.participant = Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.team,
        )

    def test_get_profile_returns_user_profile(self):
        """
        Test that get_profile correctly returns the user's profile.
        Profile is auto-created by a signal when User is created.
        """
        serializer = ParticipantSerializer(self.participant)
        data = serializer.data

        self.assertIn("profile", data)
        self.assertIsInstance(data["profile"], dict)
        # Profile should have these fields from UserProfileSerializer
        self.assertIn("affiliation", data["profile"])
        self.assertIn("github_url", data["profile"])
        self.assertIn("google_scholar_url", data["profile"])
        self.assertIn("linkedin_url", data["profile"])

    def test_get_profile_with_prefetched_profile(self):
        """
        Test that get_profile works correctly when profile is prefetched
        via select_related on user__profile.
        """
        # Query participant with select_related (as done in the fixed view)
        participant_with_prefetch = Participant.objects.select_related(
            "user", "user__profile"
        ).get(pk=self.participant.pk)

        serializer = ParticipantSerializer(participant_with_prefetch)
        data = serializer.data

        self.assertIn("profile", data)
        self.assertIsInstance(data["profile"], dict)

    def test_member_fields_are_correct(self):
        """Test that member fields return correct values."""
        serializer = ParticipantSerializer(self.participant)
        data = serializer.data

        self.assertEqual(data["member_name"], "testuser")
        self.assertEqual(data["first_name"], "Test")
        self.assertEqual(data["last_name"], "User")
        self.assertEqual(data["email"], "testuser@test.com")
        self.assertEqual(data["status"], Participant.SELF)
