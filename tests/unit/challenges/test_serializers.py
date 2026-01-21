import os
from datetime import timedelta
from unittest import TestCase
from unittest.mock import MagicMock, Mock
from unittest.mock import patch as mockpatch

import pytest
from allauth.account.models import EmailAddress
from challenges.models import (
    Challenge,
    ChallengePhase,
    DatasetSplit,
    Leaderboard,
)
from challenges.serializers import (
    ChallengeConfigSerializer,
    ChallengePhaseCreateSerializer,
    ChallengePhaseSerializer,
    ChallengeSerializer,
    DatasetSplitSerializer,
    LeaderboardDataSerializer,
    LeaderboardSerializer,
    PWCChallengeLeaderboardSerializer,
    StarChallengeSerializer,
    UserInvitationSerializer,
    ZipChallengePhaseSplitSerializer,
    ZipChallengeSerializer,
)
from challenges.utils import add_sponsors_to_challenge
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase as DjangoTestCase
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from participants.models import ParticipantTeam
from rest_framework.test import APIClient, APITestCase


class BaseTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description for test challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge", created_by=self.user
        )

        self.client.force_authenticate(user=self.user)


class ChallengePhaseCreateSerializerTest(BaseTestCase):
    def setUp(self):
        super(ChallengePhaseCreateSerializerTest, self).setUp()

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                is_public=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                max_submissions_per_day=100000,
                max_submissions=100000,
                max_submissions_per_month=100000,
                codename="Phase Code Name",
                is_restricted_to_select_one_submission=True,
                is_partial_submission_evaluation_enabled=False,
            )
            self.challenge_phase.slug = "{}-{}-{}".format(
                self.challenge.title.split(" ")[0].lower(),
                self.challenge_phase.codename.replace(" ", "-").lower(),
                self.challenge.pk,
            )[:198]
            self.challenge_phase.save()

            self.serializer_data = {
                "id": self.challenge_phase.pk,
                "name": "Challenge Phase",
                "description": "Description for Challenge Phase",
                "leaderboard_public": False,
                "is_public": False,
                "start_date": "{0}{1}".format(
                    self.challenge_phase.start_date.isoformat(), "Z"
                ).replace("+00:00", ""),
                "end_date": "{0}{1}".format(
                    self.challenge_phase.end_date.isoformat(), "Z"
                ).replace("+00:00", ""),
                "challenge": self.challenge.pk,
                "test_annotation": self.challenge_phase.test_annotation.url,
                "max_submissions_per_day": 100000,
                "max_submissions": 100000,
                "max_submissions_per_month": 100000,
                "codename": self.challenge_phase.codename,
                "is_active": self.challenge_phase.is_active,
                "slug": self.challenge_phase.slug,
                "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,
                "environment_image": self.challenge_phase.environment_image,
                "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,
                "is_partial_submission_evaluation_enabled": (
                    self.challenge_phase.is_partial_submission_evaluation_enabled
                ),
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,
                "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,
                "allowed_email_ids": self.challenge_phase.allowed_email_ids,
            }
            self.challenge_phase_create_serializer = (
                ChallengePhaseCreateSerializer(instance=self.challenge_phase)
            )

            self.serializer_data_wihout_max_submissions_per_month = {
                "id": self.challenge_phase.pk,
                "name": "Challenge Phase",
                "description": "Description for Challenge Phase",
                "leaderboard_public": False,
                "is_public": False,
                "start_date": "{0}{1}".format(
                    self.challenge_phase.start_date.isoformat(), "Z"
                ).replace("+00:00", ""),
                "end_date": "{0}{1}".format(
                    self.challenge_phase.end_date.isoformat(), "Z"
                ).replace("+00:00", ""),
                "challenge": self.challenge.pk,
                "test_annotation": self.challenge_phase.test_annotation.url,
                "max_submissions_per_day": 100,
                "max_submissions": 500,
                "codename": self.challenge_phase.codename,
                "is_active": self.challenge_phase.is_active,
                "slug": self.challenge_phase.slug,
                "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,
                "environment_image": self.challenge_phase.environment_image,
                "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,
                "is_partial_submission_evaluation_enabled": (
                    self.challenge_phase.is_partial_submission_evaluation_enabled
                ),
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,
                "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,
                "allowed_email_ids": self.challenge_phase.allowed_email_ids,
            }
            self.challenge_phase_create_serializer_without_max_submissions_per_month = ChallengePhaseCreateSerializer(
                instance=self.challenge_phase
            )

            self.serializer_data_without_max_concurrent_submissions_allowed = {
                "id": self.challenge_phase.pk,
                "name": "Challenge Phase",
                "description": "Description for Challenge Phase",
                "leaderboard_public": False,
                "is_public": False,
                "start_date": "{0}{1}".format(
                    self.challenge_phase.start_date.isoformat(), "Z"
                ).replace("+00:00", ""),
                "end_date": "{0}{1}".format(
                    self.challenge_phase.end_date.isoformat(), "Z"
                ).replace("+00:00", ""),
                "challenge": self.challenge.pk,
                "test_annotation": self.challenge_phase.test_annotation.url,
                "max_submissions_per_day": 100000,
                "max_submissions": 100000,
                "max_submissions_per_month": 100000,
                "codename": self.challenge_phase.codename,
                "is_active": self.challenge_phase.is_active,
                "slug": self.challenge_phase.slug,
                "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,
                "is_partial_submission_evaluation_enabled": (
                    self.challenge_phase.is_partial_submission_evaluation_enabled
                ),
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,
                "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,
                "allowed_email_ids": self.challenge_phase.allowed_email_ids,
            }
            self.challenge_phase_create_serializer_without_max_concurrent_submissions_allowed = ChallengePhaseCreateSerializer(
                instance=self.challenge_phase
            )

    def test_phase_create_serializer_exclude_fields(self):
        ser = ChallengePhaseCreateSerializer(
            instance=self.challenge_phase,
            context={"exclude_fields": ["slug", "nonexistent"]},
        )
        self.assertNotIn("slug", ser.fields)

    def test_challenge_phase_create_serializer(self):
        data = self.challenge_phase_create_serializer.data

        self.assertEqual(
            sorted(list(data.keys())),
            sorted(
                [
                    "id",
                    "name",
                    "description",
                    "leaderboard_public",
                    "start_date",
                    "end_date",
                    "challenge",
                    "max_submissions_per_day",
                    "max_submissions_per_month",
                    "max_submissions",
                    "is_public",
                    "is_active",
                    "codename",
                    "test_annotation",
                    "is_submission_public",
                    "annotations_uploaded_using_cli",
                    "slug",
                    "max_concurrent_submissions_allowed",
                    "environment_image",
                    "is_restricted_to_select_one_submission",
                    "submission_meta_attributes",
                    "is_partial_submission_evaluation_enabled",
                    "config_id",
                    "allowed_submission_file_types",
                    "default_submission_meta_attributes",
                    "allowed_email_ids",
                    "disable_logs",
                ]
            ),
        )

        self.assertEqual(data["id"], self.serializer_data["id"])
        self.assertEqual(data["name"], self.serializer_data["name"])
        self.assertEqual(
            data["description"], self.serializer_data["description"]
        )
        self.assertEqual(
            data["leaderboard_public"],
            self.serializer_data["leaderboard_public"],
        )
        self.assertEqual(
            data["start_date"], self.serializer_data["start_date"]
        )
        self.assertEqual(data["end_date"], self.serializer_data["end_date"])
        self.assertEqual(data["challenge"], self.serializer_data["challenge"])
        self.assertEqual(
            data["max_submissions_per_day"],
            self.serializer_data["max_submissions_per_day"],
        )
        self.assertEqual(
            data["max_submissions_per_month"],
            self.serializer_data["max_submissions_per_month"],
        )
        self.assertEqual(
            data["max_submissions"], self.serializer_data["max_submissions"]
        )
        self.assertEqual(data["is_public"], self.serializer_data["is_public"])
        self.assertEqual(data["codename"], self.serializer_data["codename"])
        self.assertEqual(
            data["test_annotation"], self.serializer_data["test_annotation"]
        )
        self.assertEqual(data["is_active"], self.serializer_data["is_active"])
        self.assertEqual(data["slug"], self.serializer_data["slug"])
        self.assertEqual(
            data["environment_image"],
            self.serializer_data["environment_image"],
        )

        self.assertEqual(
            data["max_concurrent_submissions_allowed"],
            self.serializer_data["max_concurrent_submissions_allowed"],
        )

    def test_challenge_phase_create_serializer_wihout_max_submissions_per_month(
        self,
    ):
        data = (
            self.challenge_phase_create_serializer_without_max_submissions_per_month.data
        )

        self.assertEqual(
            sorted(list(data.keys())),
            sorted(
                [
                    "id",
                    "name",
                    "description",
                    "leaderboard_public",
                    "start_date",
                    "end_date",
                    "challenge",
                    "max_submissions_per_day",
                    "max_submissions",
                    "max_submissions_per_month",
                    "is_public",
                    "is_active",
                    "codename",
                    "test_annotation",
                    "is_submission_public",
                    "annotations_uploaded_using_cli",
                    "slug",
                    "max_concurrent_submissions_allowed",
                    "environment_image",
                    "is_restricted_to_select_one_submission",
                    "submission_meta_attributes",
                    "is_partial_submission_evaluation_enabled",
                    "config_id",
                    "allowed_submission_file_types",
                    "default_submission_meta_attributes",
                    "allowed_email_ids",
                    "disable_logs",
                ]
            ),
        )

        self.assertEqual(data["id"], self.serializer_data["id"])
        self.assertEqual(data["name"], self.serializer_data["name"])
        self.assertEqual(
            data["description"], self.serializer_data["description"]
        )
        self.assertEqual(
            data["leaderboard_public"],
            self.serializer_data["leaderboard_public"],
        )
        self.assertEqual(
            data["start_date"], self.serializer_data["start_date"]
        )
        self.assertEqual(data["end_date"], self.serializer_data["end_date"])
        self.assertEqual(data["challenge"], self.serializer_data["challenge"])
        self.assertEqual(
            data["max_submissions_per_day"],
            self.serializer_data["max_submissions_per_day"],
        )
        self.assertEqual(
            data["max_submissions_per_month"],
            self.serializer_data["max_submissions_per_month"],
        )
        self.assertEqual(
            data["max_submissions"], self.serializer_data["max_submissions"]
        )
        self.assertEqual(data["is_public"], self.serializer_data["is_public"])
        self.assertEqual(data["codename"], self.serializer_data["codename"])
        self.assertEqual(
            data["test_annotation"], self.serializer_data["test_annotation"]
        )
        self.assertEqual(data["is_active"], self.serializer_data["is_active"])
        self.assertEqual(data["slug"], self.serializer_data["slug"])

        self.assertEqual(
            data["max_concurrent_submissions_allowed"],
            self.serializer_data["max_concurrent_submissions_allowed"],
        )

    def test_challenge_phase_create_serializer_without_max_concurrent_submissions_allowed(
        self,
    ):
        data = (
            self.challenge_phase_create_serializer_without_max_concurrent_submissions_allowed.data
        )

        self.assertEqual(
            sorted(list(data.keys())),
            sorted(
                [
                    "id",
                    "name",
                    "description",
                    "leaderboard_public",
                    "start_date",
                    "end_date",
                    "challenge",
                    "max_submissions_per_day",
                    "max_submissions_per_month",
                    "max_submissions",
                    "is_public",
                    "is_active",
                    "codename",
                    "test_annotation",
                    "is_submission_public",
                    "annotations_uploaded_using_cli",
                    "slug",
                    "max_concurrent_submissions_allowed",
                    "environment_image",
                    "is_restricted_to_select_one_submission",
                    "submission_meta_attributes",
                    "is_partial_submission_evaluation_enabled",
                    "config_id",
                    "allowed_submission_file_types",
                    "default_submission_meta_attributes",
                    "allowed_email_ids",
                    "disable_logs",
                ]
            ),
        )

        self.assertEqual(data["id"], self.serializer_data["id"])
        self.assertEqual(data["name"], self.serializer_data["name"])
        self.assertEqual(
            data["description"], self.serializer_data["description"]
        )
        self.assertEqual(
            data["leaderboard_public"],
            self.serializer_data["leaderboard_public"],
        )
        self.assertEqual(
            data["start_date"], self.serializer_data["start_date"]
        )
        self.assertEqual(data["end_date"], self.serializer_data["end_date"])
        self.assertEqual(data["challenge"], self.serializer_data["challenge"])
        self.assertEqual(
            data["max_submissions_per_day"],
            self.serializer_data["max_submissions_per_day"],
        )
        self.assertEqual(
            data["max_submissions_per_month"],
            self.serializer_data["max_submissions_per_month"],
        )
        self.assertEqual(
            data["max_submissions"], self.serializer_data["max_submissions"]
        )
        self.assertEqual(data["is_public"], self.serializer_data["is_public"])
        self.assertEqual(data["codename"], self.serializer_data["codename"])
        self.assertEqual(
            data["test_annotation"], self.serializer_data["test_annotation"]
        )
        self.assertEqual(data["is_active"], self.serializer_data["is_active"])
        self.assertEqual(data["slug"], self.serializer_data["slug"])
        self.assertEqual(
            data["environment_image"],
            self.serializer_data["environment_image"],
        )

    def test_challenge_phase_create_serializer_with_invalid_data(self):
        serializer = ChallengePhaseCreateSerializer(data=self.serializer_data)
        self.assertFalse(serializer.is_valid())
        self.assertEqual(
            set(serializer.errors), set(["test_annotation", "slug"])
        )


class ChallengeLeaderboardSerializerTests(TestCase):
    def setUp(self):
        self.obj = MagicMock()
        self.serializer = PWCChallengeLeaderboardSerializer()

    def test_get_challenge_id(self):
        """Test case for get_challenge_id function."""
        self.obj.phase_split.challenge_phase.challenge.id = 1
        result = self.serializer.get_challenge_id(self.obj)
        self.assertEqual(result, 1)

    def test_get_leaderboard_decimal_precision(self):
        """Test case for get_leaderboard_decimal_precision function."""
        self.obj.phase_split.leaderboard_decimal_precision = 2
        result = self.serializer.get_leaderboard_decimal_precision(self.obj)
        self.assertEqual(result, 2)

    def test_get_is_leaderboard_order_descending(self):
        """Test case for get_is_leaderboard_order_descending function."""
        self.obj.phase_split.is_leaderboard_order_descending = True
        result = self.serializer.get_is_leaderboard_order_descending(self.obj)
        self.assertTrue(result)

    def test_get_leaderboard(self):
        """Test case for get_leaderboard function."""
        leaderboard_schema = {
            "default_order_by": "accuracy",
            "labels": ["accuracy", "loss", "f1_score"],
        }
        self.obj.phase_split.leaderboard.schema = leaderboard_schema

        result = self.serializer.get_leaderboard(self.obj)
        self.assertEqual(result, ["accuracy", "loss", "f1_score"])


class DatasetSplitSerializerInitTests(DjangoTestCase):
    def test_dataset_split_serializer_sets_config_id(self):
        ser = DatasetSplitSerializer(data={}, context={"config_id": 7})
        self.assertEqual(ser.initial_data.get("config_id"), 7)


class ChallengeConfigAndLeaderboardSerializerInitTests(DjangoTestCase):
    def test_challenge_config_serializer_sets_user(self):
        user = User.objects.create(username="u3")

        class Req:
            pass

        req = Req()
        req.user = user

        ser = ChallengeConfigSerializer(data={}, context={"request": req})
        self.assertEqual(ser.initial_data.get("user"), user.pk)

    def test_leaderboard_serializer_sets_config_id(self):
        ser = LeaderboardSerializer(data={}, context={"config_id": 5})
        self.assertEqual(ser.initial_data.get("config_id"), 5)


class ZipSerializersInitTests(DjangoTestCase):
    def test_zip_challenge_serializer_sets_optional_fields_from_context(self):
        img = object()
        eval_script = object()

        class Req:
            method = "GET"

        ser = ZipChallengeSerializer(
            data={},
            context={
                "request": Req(),
                "image": img,
                "evaluation_script": eval_script,
                "github_repository": "org/repo",
                "github_branch": "main",
                "github_token": "tok",
            },
        )
        self.assertIs(ser.initial_data.get("image"), img)
        self.assertIs(ser.initial_data.get("evaluation_script"), eval_script)
        self.assertEqual(ser.initial_data.get("github_repository"), "org/repo")
        self.assertEqual(ser.initial_data.get("github_branch"), "main")
        self.assertEqual(ser.initial_data.get("github_token"), "tok")

    def test_zip_challenge_phase_split_serializer_excludes_fields(self):
        ser = ZipChallengePhaseSplitSerializer(
            instance=None,
            context={"exclude_fields": ["leaderboard", "nonexistent"]},
        )
        self.assertNotIn("leaderboard", ser.fields)


class StarChallengeSerializerInitTests(DjangoTestCase):
    def test_star_challenge_serializer_sets_fields_from_context(self):
        user = User.objects.create(username="u6")
        team = ChallengeHostTeam.objects.create(
            team_name="t6", created_by=user
        )
        chal = Challenge.objects.create(title="T6", creator=team)

        class Req:
            pass

        req = Req()
        req.user = user

        ser = StarChallengeSerializer(
            data={},
            context={
                "challenge": chal,
                "request": req,
                "is_starred": True,
            },
        )
        self.assertEqual(ser.initial_data.get("challenge"), chal.pk)
        self.assertEqual(ser.initial_data.get("user"), user.pk)
        self.assertTrue(ser.initial_data.get("is_starred"))


class LeaderboardDataSerializerInitTests(DjangoTestCase):
    def test_leaderboard_data_serializer_sets_foreign_keys_from_context(self):
        user = User.objects.create(username="u7")
        team = ChallengeHostTeam.objects.create(
            team_name="t7", created_by=user
        )
        chal = Challenge.objects.create(title="T7", creator=team)
        phase = ChallengePhase.objects.create(
            name="P", description="d", challenge=chal
        )
        ds = DatasetSplit.objects.create(name="N", codename="C")
        lb = Leaderboard.objects.create(schema={})
        from challenges.models import ChallengePhaseSplit

        cps = ChallengePhaseSplit.objects.create(
            challenge_phase=phase, dataset_split=ds, leaderboard=lb
        )

        class Sub:
            pk = 101

        ser = LeaderboardDataSerializer(
            data={},
            context={"challenge_phase_split": cps, "submission": Sub()},
        )
        self.assertEqual(ser.initial_data.get("challenge_phase_split"), cps.pk)
        self.assertEqual(ser.initial_data.get("submission"), 101)


class ChallengeSerializerInitTests(DjangoTestCase):
    def test_challenge_serializer_sets_creator_and_token_on_non_get(self):
        user = User.objects.create(username="u")
        team = ChallengeHostTeam.objects.create(team_name="t", created_by=user)

        class Req:
            pass

        req = Req()
        req.method = "POST"
        req.user = user

        context = {
            "request": req,
            "challenge_host_team": team,
            "github_token": "tok",
        }
        data = {"title": "T"}
        ser = ChallengeSerializer(data=data, context=context)
        self.assertEqual(ser.initial_data.get("creator"), team.pk)
        self.assertEqual(ser.initial_data.get("github_token"), "tok")

    def test_challenge_serializer_exposes_creator_field_on_get(self):
        user = User.objects.create(username="u2")
        team = ChallengeHostTeam.objects.create(
            team_name="t2", created_by=user
        )
        chal = Challenge.objects.create(title="TT", creator=team)

        class Req:
            method = "GET"

        ser = ChallengeSerializer(instance=chal, context={"request": Req()})
        self.assertIn("creator", ser.fields)


@pytest.mark.django_db
class UserInvitationSerializerTests(TestCase):
    def setUp(self):
        # Set up any common objects you need
        self.user = User.objects.create(username="testuser")
        self.challengeHostTeam = ChallengeHostTeam.objects.create(
            team_name="Test Team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=self.challengeHostTeam,
        )
        self.obj = Mock(challenge=self.challenge, user=self.user)
        self.serializer = UserInvitationSerializer()

    def test_get_challenge_title(self):
        result = self.serializer.get_challenge_title(self.obj)
        self.assertEqual(result, "Test Challenge")

    def test_get_challenge_host_team_name(self):
        # Assuming creator has a team_name attribute
        self.user.team_name = "Test Team"
        result = self.serializer.get_challenge_host_team_name(self.obj)
        self.assertEqual(result, "Test Team")

    def test_get_user_details(self):
        # Mock the serializer output
        with mockpatch(
            "challenges.serializers.UserDetailsSerializer"
        ) as mock_serializer:
            mock_serializer.return_value.data = {"username": "testuser"}
            result = self.serializer.get_user_details(self.obj)
            self.assertEqual(result, {"username": "testuser"})


@pytest.mark.django_db
class AddSponsorsToChallengeTests(TestCase):
    def setUp(self):
        self.User = User.objects.create(username="testuser")
        self.challengeHostTeam = ChallengeHostTeam.objects.create(
            team_name="Test Team", created_by=self.User
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge", creator=self.challengeHostTeam
        )
        self.yaml_file_data = {
            "sponsors": [
                {"name": "Test Sponsor", "website": "https://testsponsor.com"}
            ]
        }

    @mockpatch(
        "challenges.utils.ChallengeSponsorSerializer"
    )  # Mock the serializer
    def test_serializer_valid(self, MockChallengeSponsorSerializer):
        # Mocking the serializer instance and its methods
        mock_serializer = MockChallengeSponsorSerializer.return_value
        mock_serializer.is_valid.return_value = (
            True  # Simulate a valid serializer
        )

        # Call the function with the real challenge object
        result = add_sponsors_to_challenge(self.yaml_file_data, self.challenge)

        # Assertions
        mock_serializer.save.assert_called_once()  # Ensure save is called on the serializer
        self.assertTrue(
            self.challenge.has_sponsors
        )  # Ensure has_sponsors is set to True
        self.challenge.refresh_from_db()  # Refresh the challenge instance from the database
        self.assertTrue(
            self.challenge.has_sponsors
        )  # Check again after refreshing

        # Ensure the function does not return any error response (meaning it worked correctly)
        self.assertIsNone(result)


class TestChallengePhaseSerializer(TestCase):
    def test_challenge_phase_serializer_sets_challenge_in_data(self):
        mock_challenge = MagicMock()
        mock_challenge.pk = 123

        context = {"challenge": mock_challenge}
        data = {}

        serializer = ChallengePhaseSerializer(data=data, context=context)
        assert serializer.initial_data["challenge"] == 123
