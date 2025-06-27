from django.contrib.auth.models import User
from django.test import RequestFactory, TestCase
from participants.serializers import (
    ChallengeParticipantSerializer,
    InviteParticipantToTeamSerializer,
)
from rest_framework import serializers


class DummyObj:
    team_name = "nonexistent_team"


class TestChallengeParticipantSerializer(TestCase):
    def test_get_team_members_team_does_not_exist(self):
        serializer = ChallengeParticipantSerializer()
        obj = DummyObj()
        result = serializer.get_team_members(obj)
        self.assertEqual(result, "Participant team does not exist")

    def test_get_team_members_email_ids_team_does_not_exist(self):
        serializer = ChallengeParticipantSerializer()
        obj = DummyObj()
        result = serializer.get_team_members_email_ids(obj)
        self.assertEqual(result, "Participant team does not exist")


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
        # Use an email that does not exist in the User table
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
