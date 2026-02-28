from datetime import timedelta

from accounts.serializers import (
    CustomPasswordResetSerializer,
    ProfileSerializer,
)
from challenges.models import Challenge
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from participants.models import Participant, ParticipantTeam
from rest_framework.exceptions import ValidationError


class TestCustomPasswordResetSerializer(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.active_user = self.user_model.objects.create_user(
            username="active_user",
            email="active@example.com",
            password="password",
        )
        self.inactive_user = self.user_model.objects.create_user(
            username="inactive_user",
            email="inactive@example.com",
            password="password",
        )
        self.inactive_user.is_active = False
        self.inactive_user.save()

    def test_get_email_options_try_block(self):
        serializer = CustomPasswordResetSerializer(
            data={"email": self.active_user.email}
        )
        self.assertEqual(serializer.is_valid(), True)
        expected_email_options = super(
            CustomPasswordResetSerializer, serializer
        ).get_email_options()
        self.assertEqual(
            serializer.get_email_options(), expected_email_options
        )

    def test_get_email_options_except_block(self):
        serializer = CustomPasswordResetSerializer(
            data={"email": "nonexistent@example.com"}
        )
        serializer.is_valid()  # Ensure data is validated
        with self.assertRaises(ValidationError) as e:
            serializer.get_email_options()
        self.assertEqual(
            e.exception.detail,
            {"details": "User with the given email does not exist."},
        )

    def test_get_email_options_inactive_user(self):
        serializer = CustomPasswordResetSerializer(
            data={"email": self.inactive_user.email}
        )
        serializer.is_valid()  # Ensure data is validated
        with self.assertRaises(ValidationError) as e:
            serializer.get_email_options()
        self.assertEqual(
            e.exception.detail,
            {
                "details": "Account is not active. Please contact the administrator."
            },
        )


class TestProfileSerializer(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="test_user", email="test@example.com", password="password"
        )

    def test_profile_serializer_fields(self):
        serializer = ProfileSerializer(self.user)
        expected_fields = [
            "pk",
            "email",
            "username",
            "first_name",
            "last_name",
            "affiliation",
            "github_url",
            "google_scholar_url",
            "linkedin_url",
            "address_street",
            "address_city",
            "address_state",
            "address_country",
            "university",
            "is_profile_complete",
            "is_profile_fields_locked",
            "email_bounced",
        ]
        self.assertEqual(set(serializer.data.keys()), set(expected_fields))

    def test_profile_serializer_update(self):
        serializer = ProfileSerializer(
            self.user,
            data={
                "first_name": "Test",
                "last_name": "User",
                "affiliation": "Test Affiliation",
                "github_url": "https://github.com/test",
                "google_scholar_url": "https://scholar.google.com/citations?user=test",
                "linkedin_url": "https://www.linkedin.com/in/test",
                "address_street": "123 Test St",
                "address_city": "Test City",
                "address_state": "Test State",
                "address_country": "Test Country",
                "university": "Test University",
            },
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.affiliation, "Test Affiliation")
        self.assertEqual(
            self.user.profile.github_url, "https://github.com/test"
        )
        self.assertEqual(
            self.user.profile.google_scholar_url,
            "https://scholar.google.com/citations?user=test",
        )
        self.assertEqual(
            self.user.profile.linkedin_url, "https://www.linkedin.com/in/test"
        )
        self.assertEqual(self.user.profile.address_city, "Test City")
        self.assertEqual(self.user.profile.address_state, "Test State")

    def test_profile_serializer_rejects_blank_required_fields(self):
        """Required profile fields cannot be blank."""
        data = {
            "first_name": "Test",
            "last_name": "User",
            "affiliation": "Test Affiliation",
            "github_url": "https://github.com/test",
            "google_scholar_url": "",
            "linkedin_url": "",
            "address_street": "",
            "address_city": "",
            "address_state": "",
            "address_country": "India",
            "university": "IIT Roorkee",
        }
        serializer = ProfileSerializer(self.user, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("address_street", serializer.errors)
        self.assertIn("address_city", serializer.errors)
        self.assertIn("address_state", serializer.errors)

    def test_profile_serializer_rejects_edit_when_profile_fields_locked(self):
        """Cannot edit locked fields after participating in require_complete_profile."""
        host_team = ChallengeHostTeam.objects.create(
            team_name="Host Team", created_by=self.user
        )
        ChallengeHost.objects.create(
            user=self.user,
            team_name=host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )
        participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user
        )
        Participant.objects.create(
            user=self.user, team=participant_team, status=Participant.SELF
        )
        self.user.first_name = "Original"
        self.user.last_name = "Name"
        self.user.save()
        self.user.profile.address_city = "Original City"
        self.user.profile.address_state = "Original State"
        self.user.profile.save()

        challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=30),
        )
        challenge.participant_teams.add(participant_team)

        data = {
            "first_name": "Changed",
            "last_name": "Name",
            "affiliation": "Test",
            "github_url": "",
            "google_scholar_url": "",
            "linkedin_url": "",
            "address_city": "New City",
            "address_state": "New State",
            "address_country": "India",
            "address_street": "123 St",
            "university": "Test Univ",
        }
        serializer = ProfileSerializer(self.user, data=data)
        self.assertFalse(serializer.is_valid())
        self.assertIn("first_name", serializer.errors)
        self.assertIn("address_city", serializer.errors)
        self.assertIn("address_state", serializer.errors)

    def test_profile_serializer_is_profile_fields_locked_when_participated(
        self,
    ):
        """is_profile_fields_locked is True when user participated in require_complete_profile challenge."""
        host_team = ChallengeHostTeam.objects.create(
            team_name="Host Team", created_by=self.user
        )
        ChallengeHost.objects.create(
            user=self.user,
            team_name=host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )
        participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user
        )
        Participant.objects.create(
            user=self.user, team=participant_team, status=Participant.SELF
        )
        challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=30),
        )
        challenge.participant_teams.add(participant_team)

        serializer = ProfileSerializer(self.user)
        self.assertTrue(serializer.data["is_profile_fields_locked"])

    def test_profile_serializer_is_profile_fields_locked_false_when_not_participated(
        self,
    ):
        """is_profile_fields_locked is False when user has not participated."""
        serializer = ProfileSerializer(self.user)
        self.assertFalse(serializer.data["is_profile_fields_locked"])

    def test_profile_serializer_allows_non_locked_updates_when_locked(self):
        """When locked, can still update non-locked fields (affiliation, github_url)."""
        host_team = ChallengeHostTeam.objects.create(
            team_name="Host Team", created_by=self.user
        )
        ChallengeHost.objects.create(
            user=self.user,
            team_name=host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )
        participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user
        )
        Participant.objects.create(
            user=self.user, team=participant_team, status=Participant.SELF
        )
        self.user.first_name = "Original"
        self.user.last_name = "Name"
        self.user.save()
        self.user.profile.address_street = "123 St"
        self.user.profile.address_city = "Original City"
        self.user.profile.address_state = "Original State"
        self.user.profile.address_country = "India"
        self.user.profile.university = "Test Univ"
        self.user.profile.affiliation = "Old Affiliation"
        self.user.profile.save()

        challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=host_team,
            require_complete_profile=True,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() + timedelta(days=30),
        )
        challenge.participant_teams.add(participant_team)

        # Send same values for locked fields, new values for non-locked
        data = {
            "first_name": "Original",
            "last_name": "Name",
            "affiliation": "New Affiliation",
            "github_url": "https://github.com/new",
            "google_scholar_url": "",
            "linkedin_url": "",
            "address_city": "Original City",
            "address_state": "Original State",
            "address_country": "India",
            "address_street": "123 St",
            "university": "Test Univ",
        }
        serializer = ProfileSerializer(self.user, data=data)
        self.assertTrue(
            serializer.is_valid(),
            "Expected valid but got errors: %s" % serializer.errors,
        )
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.affiliation, "New Affiliation")
        self.assertEqual(
            self.user.profile.github_url, "https://github.com/new"
        )
        self.assertEqual(self.user.first_name, "Original")
        self.assertEqual(self.user.profile.address_city, "Original City")
