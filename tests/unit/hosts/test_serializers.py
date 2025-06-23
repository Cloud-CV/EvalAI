import pytest
from django.contrib.auth.models import User
from hosts.serializers import ChallengeHostSerializer, ChallengeHostTeamSerializer, HostTeamDetailSerializer, InviteHostToTeamSerializer
from hosts.models import ChallengeHost, ChallengeHostTeam
from rest_framework.exceptions import ValidationError
from rest_framework.test import APIRequestFactory


@pytest.mark.django_db
class TestInviteHostToTeamSerializer:

    @pytest.fixture
    def setup_data(self):
       
        host_user = User.objects.create_user(username="hostuser", email="host@example.com", password="testpass")
        team = ChallengeHostTeam.objects.create(team_name="Test Team", created_by=host_user)
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
        invited_user = User.objects.create_user(username="guest", email="guest@example.com", password="guestpass")
        data = {"email": invited_user.email}
        context = {"request": request, "challenge_host_team": team}
        serializer = InviteHostToTeamSerializer(data=data, context=context)

        assert serializer.is_valid(), serializer.errors
        host_obj, created = serializer.save()
        assert host_obj.user == invited_user
        assert host_obj.team_name == team


