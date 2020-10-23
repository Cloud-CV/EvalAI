import os

from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge, ChallengePhase
from challenges.serializers import ChallengePhaseCreateSerializer
from participants.models import ParticipantTeam
from hosts.models import ChallengeHost, ChallengeHostTeam


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
                "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,
            }
            self.challenge_phase_create_serializer = ChallengePhaseCreateSerializer(
                instance=self.challenge_phase
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
                "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,
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
                "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,
            }
            self.challenge_phase_create_serializer_without_max_concurrent_submissions_allowed = ChallengePhaseCreateSerializer(
                instance=self.challenge_phase
            )

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
                    "slug",
                    "max_concurrent_submissions_allowed",
                    "environment_image",
                    "is_restricted_to_select_one_submission",
                    "submission_meta_attributes",
                    "is_partial_submission_evaluation_enabled",
                    "config_id",
                    "allowed_submission_file_types",
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
                    "slug",
                    "max_concurrent_submissions_allowed",
                    "environment_image",
                    "is_restricted_to_select_one_submission",
                    "submission_meta_attributes",
                    "is_partial_submission_evaluation_enabled",
                    "config_id",
                    "allowed_submission_file_types",
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
                    "slug",
                    "max_concurrent_submissions_allowed",
                    "environment_image",
                    "is_restricted_to_select_one_submission",
                    "submission_meta_attributes",
                    "is_partial_submission_evaluation_enabled",
                    "config_id",
                    "allowed_submission_file_types"
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
