import pytest
from django.contrib.auth.models import User
from hosts.models import ChallengeHostTeam, ChallengeHostTeamInvitation
from hosts.serializers import (
    ChallengeHostTeamInvitationSerializer,
    InviteHostToTeamSerializer,
)
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory


@pytest.mark.django_db
class TestInviteHostToTeamSerializer:
    @pytest.fixture
    def setup_data(self):
        host_user = User.objects.create_user(
            username="hostuser", email="host@example.com", password="testpass"
        )
        team = ChallengeHostTeam.objects.create(
            team_name="Test Team", created_by=host_user
        )
        request = APIRequestFactory().get("/")
        request.user = host_user

        return host_user, team, request

    def test_invite_self_raises_error(self, setup_data):
        host_user, team, request = setup_data
        data = {"email": host_user.email}
        context = {"request": request, "challenge_host_team": team}
        serializer = InviteHostToTeamSerializer(data=data, context=context)

        with pytest.raises(ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)

        assert "A host cannot invite himself" in str(excinfo.value)

    def test_invite_non_existent_user_raises_error(self, setup_data):
        host_user, team, request = setup_data
        data = {"email": "nonexistent@example.com"}
        context = {"request": request, "challenge_host_team": team}
        serializer = InviteHostToTeamSerializer(data=data, context=context)

        with pytest.raises(ValidationError) as excinfo:
            serializer.is_valid(raise_exception=True)

        assert "User does not exist" in str(excinfo.value)

    def test_valid_invite(self, setup_data):
        host_user, team, request = setup_data
        invited_user = User.objects.create_user(
            username="guest", email="guest@example.com", password="guestpass"
        )
        data = {"email": invited_user.email}
        context = {"request": request, "challenge_host_team": team}
        serializer = InviteHostToTeamSerializer(data=data, context=context)

        assert serializer.is_valid(), serializer.errors
        host_obj, created = serializer.save()
        assert host_obj.user == invited_user
        assert host_obj.team_name == team


@pytest.mark.django_db
class TestChallengeHostTeamInvitationSerializer:
    @pytest.fixture
    def setup_data(self):
        host_user = User.objects.create_user(
            username="hostuser", email="host@example.com", password="testpass"
        )
        team = ChallengeHostTeam.objects.create(
            team_name="Test Team", created_by=host_user
        )
        return host_user, team

    def test_create_invitation_with_valid_data(self, setup_data):
        host_user, team = setup_data
        data = {"email": "invitee@example.com", "team": team.id}
        serializer = ChallengeHostTeamInvitationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        invitation = serializer.save(invited_by=host_user)

        assert invitation.email == "invitee@example.com"
        assert invitation.team == team
        assert invitation.invited_by == host_user
        assert invitation.status == "pending"
        assert invitation.invitation_key is not None
        assert len(invitation.invitation_key) == 32

    def test_create_invitation_without_team(self, setup_data):
        host_user, team = setup_data
        data = {"email": "invitee@example.com"}
        serializer = ChallengeHostTeamInvitationSerializer(data=data)

        assert not serializer.is_valid()
        assert "team" in serializer.errors

    def test_create_invitation_without_email(self, setup_data):
        host_user, team = setup_data
        data = {"team": team.id}
        serializer = ChallengeHostTeamInvitationSerializer(data=data)

        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_create_invitation_with_invalid_email(self, setup_data):
        host_user, team = setup_data
        data = {"email": "invalid-email", "team": team.id}
        serializer = ChallengeHostTeamInvitationSerializer(data=data)

        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_create_invitation_with_nonexistent_team(self, setup_data):
        host_user, team = setup_data
        data = {
            "email": "invitee@example.com",
            "team": 99999,  # Non-existent team ID
        }
        serializer = ChallengeHostTeamInvitationSerializer(data=data)

        assert not serializer.is_valid()
        assert "team" in serializer.errors

    def test_serialize_existing_invitation(self, setup_data):
        host_user, team = setup_data
        invitation = ChallengeHostTeamInvitation.objects.create(
            email="invitee@example.com",
            team=team,
            invited_by=host_user,
            status="pending",
        )

        serializer = ChallengeHostTeamInvitationSerializer(invitation)
        data = serializer.data

        assert data["id"] == invitation.id
        assert data["email"] == "invitee@example.com"
        assert data["invitation_key"] == invitation.invitation_key
        assert data["status"] == "pending"
        # team field is write_only, so it won't be in serialized output
        assert "team" not in data
        assert data["invited_by"] == host_user.username
        assert "team_detail" in data
        assert "created_at" in data

    def test_read_only_fields_are_not_writable(self, setup_data):
        host_user, team = setup_data
        data = {
            "email": "invitee@example.com",
            "team": team.id,
            "invitation_key": "custom-key",
            "status": "accepted",
            "invited_by": "someuser",
            "team_detail": {"some": "data"},
        }
        serializer = ChallengeHostTeamInvitationSerializer(data=data)

        assert serializer.is_valid(), serializer.errors
        invitation = serializer.save(invited_by=host_user)

        # Read-only fields should be ignored or set to their proper values
        assert (
            invitation.invitation_key != "custom-key"
        )  # Should be auto-generated
        assert invitation.status == "pending"  # Should be default
        assert (
            invitation.invited_by == host_user
        )  # Should be set by save method

    def test_team_detail_serialization(self, setup_data):
        host_user, team = setup_data
        invitation = ChallengeHostTeamInvitation.objects.create(
            email="invitee@example.com",
            team=team,
            invited_by=host_user,
            status="pending",
        )

        serializer = ChallengeHostTeamInvitationSerializer(invitation)
        data = serializer.data

        assert "team_detail" in data
        team_detail = data["team_detail"]
        assert team_detail["id"] == team.id
        assert team_detail["team_name"] == team.team_name
        assert team_detail["created_by"] == team.created_by.username
