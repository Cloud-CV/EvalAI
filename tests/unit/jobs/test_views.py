import collections
import json
import os
import shutil

from datetime import timedelta

from django.core.urlresolvers import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import (
    Challenge,
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
)
from hosts.models import ChallengeHostTeam, ChallengeHost
from jobs.models import Submission
from participants.models import ParticipantTeam, Participant


class BaseAPITestClass(APITestCase):
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

        self.user1 = User.objects.create(
            username="someuser1",
            email="user1@test.com",
            password="secret_password1",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.host_participant_team = ParticipantTeam.objects.create(
            team_name="Host Participant Team for Challenge",
            created_by=self.user,
        )

        self.host_participant = Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.host_participant_team,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge", created_by=self.user1
        )

        self.participant = Participant.objects.create(
            user=self.user1,
            status=Participant.SELF,
            team=self.participant_team,
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
        )

        self.leaderboard_schema = {
            "labels": ["score", "test-score"],
            "default_order_by": "score",
        }
        self.leaderboard = Leaderboard.objects.create(
            schema=self.leaderboard_schema
        )

        self.private_leaderboard = Leaderboard.objects.create(
            schema=self.leaderboard_schema
        )

        self.challenge.participant_teams.add(self.host_participant_team)

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                max_submissions_per_day=10,
                max_submissions_per_month=20,
                max_submissions=100,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                codename="Phase Code name",
                max_concurrent_submissions_allowed=5,
            )

            self.private_challenge_phase = ChallengePhase.objects.create(
                name="Private Challenge Phase",
                description="Description for Private Challenge Phase",
                leaderboard_public=False,
                max_submissions_per_day=10,
                max_submissions=100,
                is_public=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                codename="Private Phase Code name",
            )

            self.challenge_phase_restricted_to_one_submission = ChallengePhase.objects.create(
                name="Restrict One Public Submission Challenge Phase",
                description="Description for Restrict One Public Submission Challenge Phase",
                leaderboard_public=False,
                max_submissions_per_day=10,
                max_submissions_per_month=20,
                max_submissions=100,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                codename="Restrict One Public Submission Phase Code name",
                max_concurrent_submissions_allowed=5,
                is_restricted_to_select_one_submission=True,
            )

        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.client.force_authenticate(user=self.user1)

        self.input_file = SimpleUploadedFile(
            "dummy_input.txt", b"file_content", content_type="text/plain"
        )

        self.rl_submission_file = SimpleUploadedFile(
            "submission.json", b'{"submitted_image_uri": "evalai-repo.com"}'
        )

    def tearDown(self):
        shutil.rmtree("/tmp/evalai")

    def test_challenge_submission_when_challenge_does_not_exist(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge.delete()

        expected = {"error": "Challenge does not exist"}

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_challenge_is_not_active(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge.end_date = timezone.now() - timedelta(days=1)
        self.challenge.save()

        expected = {"error": "Challenge is not active"}

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_challenge_submission_when_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge_phase.delete()

        expected = {"error": "Challenge Phase does not exist"}

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_challenge_phase_is_not_public(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge_phase.is_public = False
        self.challenge_phase.save()
        expected = {
            "error": "Sorry, cannot accept submissions since challenge phase is not public"
        }

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_submission_when_user_does_not_exist_in_allowed_emails(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge_phase.allowed_email_ids = ["abc@test.com"]
        self.challenge_phase.save()
        expected = {
            "error": "Sorry, you are not allowed to participate in this challenge phase"
        }
        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_submission_when_user_exist_in_allowed_emails(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge_phase.allowed_email_ids = [
            "abc@test.com",
            "user1@test.com",
        ]
        self.challenge_phase.save()
        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_challenge_submission_when_user_does_not_exist_in_allowed_emails_and_is_host(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge_phase.allowed_email_ids = ["abc@test.com"]
        self.challenge_phase.save()
        self.client.force_authenticate(user=self.user)
        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_challenge_submission_when_challenge_phase_is_private_and_user_is_host(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge_phase.is_public = False
        self.challenge_phase.save()
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_challenge_submission_when_challenge_phase_is_private_and_user_is_not_host(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge_phase.is_public = False
        self.challenge_phase.save()
        expected = {
            "error": "Sorry, cannot accept submissions since challenge phase is not public"
        }

        self.client.force_authenticate(user=self.user1)

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_submission_when_participant_team_is_none(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.participant_team.delete()

        expected = {"error": "You haven't participated in the challenge"}

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_submission_when_participant_team_hasnt_participated_in_challenge(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        # Note that we haven't added the self.participant_team to Challenge
        expected = {"error": "You haven't participated in the challenge"}

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_submission_when_status_is_not_correct(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()

        expected = {"status": ['"XYZ" is not a valid choice.']}

        response = self.client.post(
            self.url,
            {"status": "XYZ", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_challenge_submission_for_successful_submission(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_challenge_submission_when_maximum_limit_exceeded(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )
        actual_maxinmum_submissions = self.challenge_phase.max_submissions
        self.challenge_phase.max_submissions = 0
        self.challenge_phase.save()
        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.input_file},
            format="multipart",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.challenge_phase.max_submissions = actual_maxinmum_submissions
        self.challenge_phase.save()

    def test_challenge_submission_for_docker_based_challenges(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.is_docker_based = True
        self.challenge.save()

        response = self.client.post(
            self.url,
            {"status": "submitting", "input_file": self.rl_submission_file},
            format="multipart",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_challenge_submission_when_file_url_is_none(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()

        expected = {"error": "The file URL is missing!"}

        response = self.client.post(
            self.url,
            {"status": "submitting"},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetChallengeSubmissionTest(BaseAPITestClass):
    def setUp(self):
        super(GetChallengeSubmissionTest, self).setUp()
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
            is_flagged=True,
        )

    def test_challenge_submission_when_challenge_does_not_exist(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge.delete()

        expected = {"error": "Challenge does not exist"}

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.challenge_phase.delete()

        expected = {"error": "Challenge Phase does not exist"}

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_challenge_submission_when_participant_team_is_none(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        self.participant_team.delete()

        expected = {"error": "You haven't participated in the challenge"}

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_challenge_submission_when_participant_team_hasnt_participated_in_challenge(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

        # Note that we haven't added the self.participant_team to Challenge
        expected = {"error": "You haven't participated in the challenge"}

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_challenge_submissions(self):
        self.url = reverse_lazy(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )
        expected = [
            {
                "id": self.submission.id,
                "participant_team": self.submission.participant_team.pk,
                "participant_team_name": self.submission.participant_team.team_name,
                "execution_time": self.submission.execution_time,
                "challenge_phase": self.submission.challenge_phase.pk,
                "created_by": self.submission.created_by.pk,
                "status": self.submission.status,
                "input_file": "http://testserver%s"
                % (self.submission.input_file.url),
                "method_name": self.submission.method_name,
                "method_description": self.submission.method_description,
                "project_url": self.submission.project_url,
                "publication_url": self.submission.publication_url,
                "stdout_file": None,
                "stderr_file": None,
                "submission_result_file": None,
                "started_at": self.submission.started_at,
                "completed_at": self.submission.completed_at,
                "submitted_at": "{0}{1}".format(
                    self.submission.submitted_at.isoformat(), "Z"
                ).replace("+00:00", ""),
                "is_public": self.submission.is_public,
                "is_flagged": self.submission.is_flagged,
                "ignore_submission": False,
                "when_made_public": self.submission.when_made_public,
                "is_baseline": self.submission.is_baseline,
                "job_name": self.submission.job_name,
                "submission_metadata": None,
            }
        ]
        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GetRemainingSubmissionTest(BaseAPITestClass):
    def setUp(self):
        super(GetRemainingSubmissionTest, self).setUp()
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={
                "challenge_phase_id": self.challenge_phase.pk,
                "challenge_id": self.challenge.pk,
            },
        )

        self.submission1 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission2 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission3 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

    def test_get_remaining_submission_when_challenge_does_not_exist(self):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk + 1},
        )
        expected = {
            "detail": "Challenge {} does not exist".format(
                self.challenge.pk + 1
            )
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_remaining_submission_when_participant_team_hasnt_participated_in_challenge(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )

        expected = {"error": "You haven't participated in the challenge"}

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_remaining_submission_when_submission_made_three_days_back(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.submission3.status = "cancelled"
        self.submission3.save()
        self.submission2.status = "failed"
        self.submission2.save()
        self.submission1.submitted_at = timezone.now() - timedelta(days=3)
        self.submission1.save()
        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()

        monthly_count = (
            0
            if self.submission1.submitted_at.month != timezone.now().month
            else 1
        )
        remaining_monthly_submissions = (
            self.challenge_phase.max_submissions_per_month - monthly_count
        )

        expected = {
            "remaining_submissions_today_count": 10,
            "remaining_submissions_this_month_count": remaining_monthly_submissions,
            "remaining_submissions_count": 99,
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data["phases"][0]["limits"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_remaining_submission_when_submission_made_one_month_back(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {
            "remaining_submissions_today_count": 10,
            "remaining_submissions_this_month_count": 20,
            "remaining_submissions_count": 99,
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        self.submission1.submitted_at = timezone.now() - timedelta(days=32)
        self.submission1.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["phases"][0]["limits"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_remaining_submission_when_submission_is_done(self):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()
        expected = {
            "remaining_submissions_today_count": 9,
            "remaining_submissions_this_month_count": 19,
            "remaining_submissions_count": 99,
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["phases"][0]["limits"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def get_remaining_submission_time_when_max_limit_is_exhausted(self):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions", 1)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {
            "message": "You have exhausted maximum submission limit!",
            "submission_limit_exceeded": True,
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["phases"][0]["limits"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def get_remaining_submission_time_when_monthly_limit_is_exhausted(self):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions_per_month", 1)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {
            "message": "You have exhausted this month's submission limit!"
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(
            response.data["phases"][0]["limits"]["message"],
            expected["message"],
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def get_remaining_submission_time_when_both_monthly_and_daily_limit_is_exhausted(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions_per_month", 1)
        setattr(self.challenge_phase, "max_submissions_per_day", 1)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {
            "message": "Both daily and monthly submission limits are exhausted!"
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(
            response.data["phases"][0]["limits"]["message"],
            expected["message"],
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_remaining_submission_time_when_daily_limit_is_exhausted(self):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions_per_day", 1)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {"message": "You have exhausted today's submission limit!"}

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(
            response.data["phases"][0]["limits"]["message"],
            expected["message"],
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_remaining_submissions_when_todays_is_greater_than_monthly_and_total(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions_per_day", 20)
        setattr(self.challenge_phase, "max_submissions_per_month", 10)
        setattr(self.challenge_phase, "max_submissions", 15)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {
            "remaining_submissions_today_count": 9,
            "remaining_submissions_this_month_count": 9,
            "remaining_submissions_count": 14,
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["phases"][0]["limits"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_remaining_submissions_when_total_less_than_monthly(self):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions_per_day", 5)
        setattr(self.challenge_phase, "max_submissions_per_month", 20)
        setattr(self.challenge_phase, "max_submissions", 15)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {
            "remaining_submissions_today_count": 4,
            "remaining_submissions_this_month_count": 14,
            "remaining_submissions_count": 14,
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["phases"][0]["limits"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_remaining_submission_when_total_less_than_monthly_and_monthly_equal_daily(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions_per_day", 20)
        setattr(self.challenge_phase, "max_submissions_per_month", 20)
        setattr(self.challenge_phase, "max_submissions", 15)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {
            "remaining_submissions_today_count": 14,
            "remaining_submissions_this_month_count": 14,
            "remaining_submissions_count": 14,
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["phases"][0]["limits"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_remaining_submission_when_total_less_than_monthly_and_monthly_less_than_daily(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions_per_day", 30)
        setattr(self.challenge_phase, "max_submissions_per_month", 20)
        setattr(self.challenge_phase, "max_submissions", 15)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {
            "remaining_submissions_today_count": 14,
            "remaining_submissions_this_month_count": 14,
            "remaining_submissions_count": 14,
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["phases"][0]["limits"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_remaining_submissions_when_monthly_remaining_less_than_todays(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions_per_day", 15)
        setattr(self.challenge_phase, "max_submissions_per_month", 13)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()

        expected = {
            "remaining_submissions_today_count": 12,
            "remaining_submissions_this_month_count": 12,
            "remaining_submissions_count": 99,
        }

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["phases"][0]["limits"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_all_phases_remaining(self):
        self.maxDiff = None
        self.url = reverse_lazy(
            "jobs:get_remaining_submissions",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        setattr(self.challenge_phase, "max_submissions_per_day", 15)
        setattr(self.challenge_phase, "max_submissions_per_month", 13)
        self.challenge_phase.save()
        self.submission3.status = "cancelled"
        self.submission2.status = "failed"
        self.submission3.save()
        self.submission2.save()
        expected = {
            "participant_team": self.participant_team.team_name,
            "participant_team_id": self.participant_team.id,
            "phases": [
                {
                    "id": self.challenge_phase.id,
                    "name": self.challenge_phase.name,
                    "slug": self.challenge_phase.slug,
                    "start_date": "{0}{1}".format(
                        self.challenge_phase.start_date.isoformat(), "Z"
                    ).replace("+00:00", ""),
                    "end_date": "{0}{1}".format(
                        self.challenge_phase.end_date.isoformat(), "Z"
                    ).replace("+00:00", ""),
                    "limits": {
                        "remaining_submissions_today_count": 12,
                        "remaining_submissions_this_month_count": 12,
                        "remaining_submissions_count": 99,
                    },
                },
                {
                    "id": self.challenge_phase_restricted_to_one_submission.id,
                    "name": self.challenge_phase_restricted_to_one_submission.name,
                    "slug": self.challenge_phase_restricted_to_one_submission.slug,
                    "start_date": "{0}{1}".format(
                        self.challenge_phase_restricted_to_one_submission.start_date.isoformat(),
                        "Z",
                    ).replace("+00:00", ""),
                    "end_date": "{0}{1}".format(
                        self.challenge_phase_restricted_to_one_submission.end_date.isoformat(),
                        "Z",
                    ).replace("+00:00", ""),
                    "limits": {
                        "remaining_submissions_today_count": 10,
                        "remaining_submissions_this_month_count": 20,
                        "remaining_submissions_count": 100,
                    },
                },
            ],
        }
        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChangeSubmissionDataAndVisibilityTest(BaseAPITestClass):
    def setUp(self):
        super(ChangeSubmissionDataAndVisibilityTest, self).setUp()

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
            is_flagged=True,
            when_made_public=timezone.now(),
        )

        self.private_submission = Submission.objects.create(
            participant_team=self.host_participant_team,
            challenge_phase=self.private_challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
            is_flagged=True,
            when_made_public=timezone.now(),
        )

        self.host_participant_team_submission = Submission.objects.create(
            participant_team=self.host_participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
            is_flagged=True,
            when_made_public=timezone.now(),
        )

        self.submission_restricted_to_one_for_leaderboard = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase_restricted_to_one_submission,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
            is_flagged=True,
            when_made_public=timezone.now(),
        )

        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )

    def test_change_submission_data_and_visibility_when_challenge_does_not_exist(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk + 10,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )

        expected = {
            "detail": "Challenge {} does not exist".format(
                self.challenge.pk + 10
            )
        }

        response = self.client.patch(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_submission_data_and_visibility_when_challenge_phase_does_not_exist(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk + 10,
                "submission_pk": self.submission.pk,
            },
        )

        expected = {
            "detail": "ChallengePhase {} does not exist".format(
                self.challenge_phase.pk + 10
            )
        }

        response = self.client.patch(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_change_submission_data_and_visibility_when_challenge_is_not_active(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )
        self.data = {"method_name": "Updated Method Name"}
        self.challenge.end_date = timezone.now() - timedelta(days=1)
        self.challenge.save()

        expected = {"error": "Challenge is not active"}
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_submission_data_and_visibility_when_challenge_is_not_public(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )

        self.challenge_phase.is_public = False
        self.challenge_phase.save()
        self.data = {"method_name": "Updated Method Name"}

        expected = {
            "error": "Sorry, cannot accept submissions since challenge phase is not public"
        }

        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_submission_data_and_visibility_when_participant_team_is_none(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )

        self.participant_team.delete()

        expected = {"error": "You haven't participated in the challenge"}
        self.data = {"method_name": "Updated Method Name"}

        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_submission_data_and_visibility_when_participant_team_hasnt_participated_in_challenge(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )

        # Note that we haven't added the self.participant_team to Challenge
        expected = {"error": "You haven't participated in the challenge"}
        self.data = {"method_name": "Updated Method Name"}

        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_change_submission_data_and_visibility_when_submission_exist(self):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )
        self.data = {"method_name": "Updated Method Name"}
        expected = {
            "id": self.submission.id,
            "participant_team": self.submission.participant_team.pk,
            "participant_team_name": self.submission.participant_team.team_name,
            "execution_time": self.submission.execution_time,
            "challenge_phase": self.submission.challenge_phase.pk,
            "created_by": self.submission.created_by.pk,
            "status": self.submission.status,
            "input_file": "http://testserver%s"
            % (self.submission.input_file.url),
            "method_name": self.data["method_name"],
            "method_description": self.submission.method_description,
            "project_url": self.submission.project_url,
            "publication_url": self.submission.publication_url,
            "stdout_file": None,
            "stderr_file": None,
            "submission_result_file": None,
            "started_at": self.submission.started_at,
            "completed_at": self.submission.completed_at,
            "submitted_at": "{0}{1}".format(
                self.submission.submitted_at.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_public": self.submission.is_public,
            "is_flagged": self.submission.is_flagged,
            "ignore_submission": False,
            "when_made_public": "{0}{1}".format(
                self.submission.when_made_public.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_baseline": self.submission.is_baseline,
            "job_name": self.submission.job_name,
            "submission_metadata": None,
        }
        self.challenge.participant_teams.add(self.participant_team)
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_submission_data_and_visibility_when_challenge_phase_is_private_and_user_is_host(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.private_challenge_phase.pk,
                "submission_pk": self.private_submission.pk,
            },
        )
        self.data = {"method_name": "Updated Method Name"}

        expected = {
            "id": self.private_submission.id,
            "participant_team": self.private_submission.participant_team.pk,
            "participant_team_name": self.private_submission.participant_team.team_name,
            "execution_time": self.private_submission.execution_time,
            "challenge_phase": self.private_submission.challenge_phase.pk,
            "created_by": self.private_submission.created_by.pk,
            "status": self.private_submission.status,
            "input_file": "http://testserver%s"
            % (self.private_submission.input_file.url),
            "method_name": self.data["method_name"],
            "method_description": self.private_submission.method_description,
            "project_url": self.private_submission.project_url,
            "publication_url": self.private_submission.publication_url,
            "stdout_file": None,
            "stderr_file": None,
            "submission_result_file": None,
            "started_at": self.submission.started_at,
            "completed_at": self.submission.completed_at,
            "submitted_at": "{0}{1}".format(
                self.private_submission.submitted_at.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_public": self.private_submission.is_public,
            "is_flagged": self.private_submission.is_flagged,
            "ignore_submission": False,
            "when_made_public": "{0}{1}".format(
                self.private_submission.when_made_public.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_baseline": self.submission.is_baseline,
            "job_name": self.submission.job_name,
            "submission_metadata": None,
        }

        self.client.force_authenticate(user=self.user)

        self.challenge.participant_teams.add(self.host_participant_team)
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_submission_data_and_visibility_when_is_public_is_true(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )
        self.data = {"is_public": True}
        self.challenge.participant_teams.add(self.participant_team)
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_submission_data_and_visibility_when_is_public_is_false(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )
        self.data = {"is_public": False}
        expected = {
            "id": self.submission.id,
            "participant_team": self.submission.participant_team.pk,
            "participant_team_name": self.submission.participant_team.team_name,
            "execution_time": self.submission.execution_time,
            "challenge_phase": self.submission.challenge_phase.pk,
            "created_by": self.submission.created_by.pk,
            "status": self.submission.status,
            "input_file": "http://testserver%s"
            % (self.submission.input_file.url),
            "method_name": self.submission.method_name,
            "method_description": self.submission.method_description,
            "project_url": self.submission.project_url,
            "publication_url": self.submission.publication_url,
            "stdout_file": None,
            "stderr_file": None,
            "submission_result_file": None,
            "started_at": self.submission.started_at,
            "completed_at": self.submission.completed_at,
            "submitted_at": "{0}{1}".format(
                self.submission.submitted_at.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_public": self.data["is_public"],
            "is_flagged": self.submission.is_flagged,
            "ignore_submission": False,
            "when_made_public": "{0}{1}".format(
                self.submission.when_made_public.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_baseline": self.submission.is_baseline,
            "job_name": self.submission.job_name,
            "submission_metadata": None,
        }
        self.challenge.participant_teams.add(self.participant_team)
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_submission_data_and_visibility_when_is_restricted_to_select_one_submission_true(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase_restricted_to_one_submission.pk,
                "submission_pk": self.submission_restricted_to_one_for_leaderboard.pk,
            },
        )
        self.data = {"is_public": True}
        self.challenge.participant_teams.add(self.participant_team)
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_toggle_baseline_when_user_is_not_a_host(self):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )
        self.data = {"is_baseline": True}
        self.challenge.save()
        self.client.force_authenticate(user=self.user1)
        expected = {
            "error": "Sorry, you are not authorized to make this request"
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_toggle_baseline_when_user_is_host(self):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.host_participant_team_submission.pk,
            },
        )
        self.data = {"is_baseline": True}
        self.challenge.save()
        self.client.force_authenticate(user=self.user)
        expected = {
            "id": self.host_participant_team_submission.id,
            "participant_team": self.host_participant_team_submission.participant_team.pk,
            "participant_team_name": self.host_participant_team_submission.participant_team.team_name,
            "execution_time": self.host_participant_team_submission.execution_time,
            "challenge_phase": self.host_participant_team_submission.challenge_phase.pk,
            "created_by": self.host_participant_team_submission.created_by.pk,
            "status": self.host_participant_team_submission.status,
            "input_file": "http://testserver%s"
            % (self.host_participant_team_submission.input_file.url),
            "method_name": self.host_participant_team_submission.method_name,
            "method_description": self.host_participant_team_submission.method_description,
            "project_url": self.host_participant_team_submission.project_url,
            "publication_url": self.host_participant_team_submission.publication_url,
            "stdout_file": None,
            "stderr_file": None,
            "submission_result_file": None,
            "started_at": self.host_participant_team_submission.started_at,
            "completed_at": self.host_participant_team_submission.completed_at,
            "submitted_at": "{0}{1}".format(
                self.host_participant_team_submission.submitted_at.isoformat(),
                "Z",
            ).replace("+00:00", ""),
            "is_public": self.host_participant_team_submission.is_public,
            "is_flagged": self.host_participant_team_submission.is_flagged,
            "ignore_submission": False,
            "when_made_public": "{0}{1}".format(
                self.host_participant_team_submission.when_made_public.isoformat(),
                "Z",
            ).replace("+00:00", ""),
            "is_baseline": True,
            "job_name": self.host_participant_team_submission.job_name,
            "submission_metadata": None,
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_change_submission_data_and_visibility_when_submission_doesnt_exist(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:change_submission_data_and_visibility",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_pk": self.submission.pk,
            },
        )

        expected = {"error": "Submission does not exist"}
        self.data = {"method_name": "Updated Method Name"}
        self.submission.delete()
        self.challenge.participant_teams.add(self.participant_team)
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_submission_by_pk_when_submission_doesnt_exist(self):
        self.url = reverse_lazy(
            "jobs:get_submission_by_pk",
            kwargs={"submission_id": self.submission.id + 5},
        )

        expected = {
            "error": "Submission {} does not exist".format(
                self.submission.id + 5
            )
        }

        self.challenge.participant_teams.add(self.participant_team)
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_submission_by_pk_when_user_created_the_submission(self):
        self.url = reverse_lazy(
            "jobs:get_submission_by_pk",
            kwargs={"submission_id": self.submission.id},
        )
        expected = {
            "id": self.submission.id,
            "participant_team": self.submission.participant_team.pk,
            "participant_team_name": self.submission.participant_team.team_name,
            "execution_time": self.submission.execution_time,
            "challenge_phase": self.submission.challenge_phase.pk,
            "created_by": self.submission.created_by.pk,
            "status": self.submission.status,
            "input_file": "http://testserver%s"
            % (self.submission.input_file.url),
            "method_name": self.submission.method_name,
            "method_description": self.submission.method_description,
            "project_url": self.submission.project_url,
            "publication_url": self.submission.publication_url,
            "stdout_file": None,
            "stderr_file": None,
            "submission_result_file": None,
            "started_at": self.submission.started_at,
            "completed_at": self.submission.completed_at,
            "submitted_at": "{0}{1}".format(
                self.submission.submitted_at.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_public": self.submission.is_public,
            "is_flagged": self.submission.is_flagged,
            "ignore_submission": False,
            "when_made_public": "{0}{1}".format(
                self.submission.when_made_public.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_baseline": self.submission.is_baseline,
            "job_name": self.submission.job_name,
            "submission_metadata": None,
        }

        self.client.force_authenticate(user=self.submission.created_by)

        self.challenge.participant_teams.add(self.participant_team)
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_submission_by_pk_when_user_is_challenge_host(self):
        self.url = reverse_lazy(
            "jobs:get_submission_by_pk",
            kwargs={"submission_id": self.submission.id},
        )
        expected = {
            "id": self.submission.id,
            "participant_team": self.submission.participant_team.pk,
            "participant_team_name": self.submission.participant_team.team_name,
            "execution_time": self.submission.execution_time,
            "challenge_phase": self.submission.challenge_phase.pk,
            "created_by": self.submission.created_by.pk,
            "status": self.submission.status,
            "input_file": "http://testserver%s"
            % (self.submission.input_file.url),
            "method_name": self.submission.method_name,
            "method_description": self.submission.method_description,
            "project_url": self.submission.project_url,
            "publication_url": self.submission.publication_url,
            "stdout_file": None,
            "stderr_file": None,
            "submission_result_file": None,
            "started_at": self.submission.started_at,
            "completed_at": self.submission.completed_at,
            "submitted_at": "{0}{1}".format(
                self.submission.submitted_at.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_public": self.submission.is_public,
            "is_flagged": self.submission.is_flagged,
            "ignore_submission": False,
            "when_made_public": "{0}{1}".format(
                self.submission.when_made_public.isoformat(), "Z"
            ).replace("+00:00", ""),
            "is_baseline": self.submission.is_baseline,
            "job_name": self.submission.job_name,
            "submission_metadata": None,
        }

        self.client.force_authenticate(user=self.user)

        self.challenge.participant_teams.add(self.participant_team)
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_submission_by_pk_when_user_is_neither_challenge_host_nor_submission_owner(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:get_submission_by_pk",
            kwargs={"submission_id": self.submission.id},
        )

        expected = {
            "error": "Sorry, you are not authorized to access this submission."
        }

        self.challenge.participant_teams.add(self.participant_team)
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ChallengeLeaderboardTest(BaseAPITestClass):
    def setUp(self):
        super(ChallengeLeaderboardTest, self).setUp()

        self.dataset_split = DatasetSplit.objects.create(
            name="Split 1", codename="split1"
        )

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            challenge_phase=self.challenge_phase,
            dataset_split=self.dataset_split,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC,
        )

        self.private_challenge_phase_split = ChallengePhaseSplit.objects.create(
            challenge_phase=self.private_challenge_phase,
            dataset_split=self.dataset_split,
            leaderboard=self.private_leaderboard,
            visibility=ChallengePhaseSplit.HOST,
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user1,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission_2 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user1,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=False,
        )

        self.private_submission = Submission.objects.create(
            participant_team=self.host_participant_team,
            challenge_phase=self.private_challenge_phase,
            created_by=self.user1,
            status="submitted",
            input_file=self.private_challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
        )

        self.host_participant_team_submission = Submission.objects.create(
            participant_team=self.host_participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
            when_made_public=timezone.now(),
        )

        self.host_participant_team_submission_2 = Submission.objects.create(
            participant_team=self.host_participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
            when_made_public=timezone.now(),
        )

        self.submission.is_public = True
        self.submission.status = Submission.FINISHED
        self.submission.save()

        self.submission_2.is_public = False
        self.submission_2.status = Submission.FINISHED
        self.submission_2.save()

        self.private_submission.is_public = False
        self.private_submission.status = Submission.FINISHED
        self.private_submission.save()

        self.host_participant_team_submission.is_public = True
        self.host_participant_team_submission.status = Submission.FINISHED
        self.host_participant_team_submission.save()

        self.host_participant_team_submission_2.is_public = True
        self.host_participant_team_submission_2.status = Submission.FINISHED
        self.host_participant_team_submission_2.save()

        self.result_json = {"score": 50.0, "test-score": 75.0}

        self.result_json_2 = {"score": 10.0, "test-score": 20.0}

        self.result_json_host_participant_team = {
            "score": 52.0,
            "test-score": 80.0,
        }

        self.result_json_host_participant_team_2 = {
            "score": 20.0,
            "test-score": 60.0,
        }

        self.expected_results = [
            self.result_json["score"],
            self.result_json["test-score"],
        ]

        self.expected_results_host_participant_team = [
            self.result_json_host_participant_team["score"],
            self.result_json_host_participant_team["test-score"],
        ]

        self.expected_results_host_participant_team_2 = [
            self.result_json_host_participant_team_2["score"],
            self.result_json_host_participant_team_2["test-score"],
        ]

        self.filtering_score = self.result_json[
            self.leaderboard.schema["default_order_by"]
        ]

        self.filtering_score_host_participant_team = self.result_json_host_participant_team[
            self.leaderboard.schema["default_order_by"]
        ]

        self.filtering_score_host_participant_team_2 = self.result_json_host_participant_team_2[
            self.leaderboard.schema["default_order_by"]
        ]

        self.leaderboard_data = LeaderboardData.objects.create(
            challenge_phase_split=self.challenge_phase_split,
            submission=self.submission,
            leaderboard=self.leaderboard,
            result=self.result_json,
        )

        self.leaderboard_data_2 = LeaderboardData.objects.create(
            challenge_phase_split=self.challenge_phase_split,
            submission=self.submission,
            leaderboard=self.leaderboard,
            result=self.result_json_2,
        )

        self.private_leaderboard_data = LeaderboardData.objects.create(
            challenge_phase_split=self.private_challenge_phase_split,
            submission=self.private_submission,
            leaderboard=self.leaderboard,
            result=self.result_json,
        )

        self.host_participant_leaderboard_data = LeaderboardData.objects.create(
            challenge_phase_split=self.challenge_phase_split,
            submission=self.host_participant_team_submission,
            leaderboard=self.leaderboard,
            result=self.result_json_host_participant_team,
        )

        self.host_participant_leaderboard_data_2 = LeaderboardData.objects.create(
            challenge_phase_split=self.challenge_phase_split,
            submission=self.host_participant_team_submission_2,
            leaderboard=self.leaderboard,
            result=self.result_json_host_participant_team_2,
        )

    def test_get_leaderboard(self):
        self.url = reverse_lazy(
            "jobs:leaderboard",
            kwargs={"challenge_phase_split_id": self.challenge_phase_split.id},
        )

        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": self.leaderboard_data.id,
                    "submission__participant_team": self.submission.participant_team.id,
                    "submission__participant_team__team_name": self.submission.participant_team.team_name,
                    "submission__participant_team__team_url": self.submission.participant_team.team_url,
                    "challenge_phase_split": self.challenge_phase_split.id,
                    "error": None,
                    "filtering_error": 0,
                    "result": self.expected_results,
                    "filtering_score": self.filtering_score,
                    "leaderboard__schema": {
                        "default_order_by": "score",
                        "labels": ["score", "test-score"],
                    },
                    "submission__submitted_at": self.submission.submitted_at,
                    "submission__is_baseline": False,
                    "submission__method_name": self.submission.method_name,
                    "submission__is_public": self.submission.is_public,
                    "submission__id": self.submission.id,
                    "submission__submission_metadata": self.submission.submission_metadata,
                }
            ],
        }
        expected = collections.OrderedDict(expected)

        response = self.client.get(self.url, {})
        self.assertEqual(response.data["count"], expected["count"])
        self.assertEqual(response.data["next"], expected["next"])
        self.assertEqual(response.data["previous"], expected["previous"])
        self.assertEqual(response.data["results"], expected["results"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_leaderboard_with_baseline_entry(self):
        self.url = reverse_lazy(
            "jobs:leaderboard",
            kwargs={"challenge_phase_split_id": self.challenge_phase_split.id},
        )
        self.maxDiff = None
        self.host_participant_team_submission.is_baseline = True
        self.host_participant_team_submission.save()

        expected = {
            "count": 2,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": self.host_participant_leaderboard_data.id,
                    "submission__participant_team": self.host_participant_team_submission.participant_team.id,
                    "submission__participant_team__team_name": self.host_participant_team_submission.participant_team.team_name,
                    "submission__participant_team__team_url": self.host_participant_team_submission.participant_team.team_url,
                    "challenge_phase_split": self.challenge_phase_split.id,
                    "result": self.expected_results_host_participant_team,
                    "filtering_score": self.filtering_score_host_participant_team,
                    "leaderboard__schema": {
                        "default_order_by": "score",
                        "labels": ["score", "test-score"],
                    },
                    "error": None,
                    "filtering_error": 0,
                    "submission__submitted_at": self.host_participant_team_submission.submitted_at,
                    "submission__is_baseline": True,
                    "submission__method_name": self.host_participant_team_submission.method_name,
                    "submission__is_public": self.submission.is_public,
                    "submission__id": self.host_participant_team_submission.id,
                    "submission__submission_metadata": self.host_participant_team_submission.submission_metadata,
                },
                {
                    "id": self.leaderboard_data.id,
                    "submission__participant_team": self.submission.participant_team.id,
                    "submission__participant_team__team_name": self.submission.participant_team.team_name,
                    "submission__participant_team__team_url": self.submission.participant_team.team_url,
                    "challenge_phase_split": self.challenge_phase_split.id,
                    "result": self.expected_results,
                    "filtering_score": self.filtering_score,
                    "leaderboard__schema": {
                        "default_order_by": "score",
                        "labels": ["score", "test-score"],
                    },
                    "error": None,
                    "filtering_error": 0,
                    "submission__submitted_at": self.submission.submitted_at,
                    "submission__is_baseline": False,
                    "submission__method_name": self.submission.method_name,
                    "submission__is_public": self.submission.is_public,
                    "submission__id": self.submission.id,
                    "submission__submission_metadata": self.submission.submission_metadata,
                },
            ],
        }
        expected = collections.OrderedDict(expected)
        response = self.client.get(self.url, {})

        # Teardown
        self.host_participant_team_submission.is_baseline = False
        self.host_participant_team_submission.save()

        self.assertEqual(response.data["count"], expected["count"])
        self.assertEqual(response.data["next"], expected["next"])
        self.assertEqual(response.data["previous"], expected["previous"])
        self.assertEqual(response.data["results"], expected["results"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_leaderboard_with_multiple_baseline_entries(self):
        self.url = reverse_lazy(
            "jobs:leaderboard",
            kwargs={"challenge_phase_split_id": self.challenge_phase_split.id},
        )
        self.maxDiff = None
        self.host_participant_team_submission.is_baseline = True
        self.host_participant_team_submission.save()

        self.host_participant_team_submission_2.is_baseline = True
        self.host_participant_team_submission_2.save()

        expected = {
            "count": 3,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": self.host_participant_leaderboard_data.id,
                    "submission__participant_team": self.host_participant_team_submission.participant_team.id,
                    "submission__participant_team__team_name": self.host_participant_team_submission.participant_team.team_name,
                    "submission__participant_team__team_url": self.host_participant_team_submission.participant_team.team_url,
                    "challenge_phase_split": self.challenge_phase_split.id,
                    "result": self.expected_results_host_participant_team,
                    "filtering_score": self.filtering_score_host_participant_team,
                    "leaderboard__schema": {
                        "default_order_by": "score",
                        "labels": ["score", "test-score"],
                    },
                    "error": None,
                    "filtering_error": 0,
                    "submission__submitted_at": self.host_participant_team_submission.submitted_at,
                    "submission__is_baseline": True,
                    "submission__method_name": self.host_participant_team_submission.method_name,
                    "submission__is_public": self.submission.is_public,
                    "submission__id": self.host_participant_team_submission.id,
                    "submission__submission_metadata": self.host_participant_team_submission.submission_metadata,
                },
                {
                    "id": self.leaderboard_data.id,
                    "submission__participant_team": self.submission.participant_team.id,
                    "submission__participant_team__team_name": self.submission.participant_team.team_name,
                    "submission__participant_team__team_url": self.submission.participant_team.team_url,
                    "challenge_phase_split": self.challenge_phase_split.id,
                    "result": self.expected_results,
                    "filtering_score": self.filtering_score,
                    "leaderboard__schema": {
                        "default_order_by": "score",
                        "labels": ["score", "test-score"],
                    },
                    "error": None,
                    "filtering_error": 0,
                    "submission__submitted_at": self.submission.submitted_at,
                    "submission__is_baseline": False,
                    "submission__method_name": self.submission.method_name,
                    "submission__is_public": self.submission.is_public,
                    "submission__id": self.submission.id,
                    "submission__submission_metadata": self.submission.submission_metadata,
                },
                {
                    "id": self.host_participant_leaderboard_data_2.id,
                    "submission__participant_team": self.host_participant_team_submission_2.participant_team.id,
                    "submission__participant_team__team_name": self.host_participant_team_submission_2.participant_team.team_name,
                    "submission__participant_team__team_url": self.host_participant_team_submission_2.participant_team.team_url,
                    "challenge_phase_split": self.challenge_phase_split.id,
                    "result": self.expected_results_host_participant_team_2,
                    "filtering_score": self.filtering_score_host_participant_team_2,
                    "leaderboard__schema": {
                        "default_order_by": "score",
                        "labels": ["score", "test-score"],
                    },
                    "error": None,
                    "filtering_error": 0,
                    "submission__submitted_at": self.host_participant_team_submission_2.submitted_at,
                    "submission__is_baseline": True,
                    "submission__method_name": self.host_participant_team_submission_2.method_name,
                    "submission__is_public": self.submission.is_public,
                    "submission__id": self.host_participant_team_submission_2.id,
                    "submission__submission_metadata": self.host_participant_team_submission_2.submission_metadata,
                },
            ],
        }
        expected = collections.OrderedDict(expected)
        response = self.client.get(self.url, {})
        # Teardown
        self.host_participant_team_submission.is_baseline = False
        self.host_participant_team_submission.save()
        self.host_participant_team_submission_2.is_baseline = False
        self.host_participant_team_submission_2.save()

        self.assertEqual(response.data["count"], expected["count"])
        self.assertEqual(response.data["next"], expected["next"])
        self.assertEqual(response.data["previous"], expected["previous"])
        self.assertEqual(response.data["results"], expected["results"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_leaderboard_with_invalid_challenge_phase_split_id(self):
        self.url = reverse_lazy(
            "jobs:leaderboard",
            kwargs={
                "challenge_phase_split_id": self.challenge_phase_split.id + 2
            },
        )

        expected = {
            "detail": f"ChallengePhaseSplit {self.challenge_phase_split.id + 2} does not exist"
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_leaderboard_with_default_order_by_key_missing(self):
        self.url = reverse_lazy(
            "jobs:leaderboard",
            kwargs={"challenge_phase_split_id": self.challenge_phase_split.id},
        )

        expected = {
            "error": "Sorry, default_order_by key is missing in leaderboard schema!"
        }

        leaderboard_schema = {"labels": ["score", "test-score"]}
        self.leaderboard.schema = leaderboard_schema
        self.leaderboard.save()

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_leaderboard_for_host_submissions_on_private_challenge_phase(
        self,
    ):
        self.url = reverse_lazy(
            "jobs:leaderboard",
            kwargs={
                "challenge_phase_split_id": self.private_challenge_phase_split.id
            },
        )

        expected = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [
                {
                    "id": self.private_leaderboard_data.id,
                    "submission__participant_team": self.private_submission.participant_team.id,
                    "submission__participant_team__team_name": self.private_submission.participant_team.team_name,
                    "submission__participant_team__team_url": self.private_submission.participant_team.team_url,
                    "challenge_phase_split": self.private_challenge_phase_split.id,
                    "result": self.expected_results,
                    "error": None,
                    "filtering_error": 0,
                    "filtering_score": self.filtering_score,
                    "leaderboard__schema": {
                        "default_order_by": "score",
                        "labels": ["score", "test-score"],
                    },
                    "submission__submitted_at": self.private_submission.submitted_at,
                    "submission__is_baseline": False,
                    "submission__method_name": self.private_submission.method_name,
                    "submission__is_public": self.private_submission.is_public,
                    "submission__id": self.private_submission.id,
                    "submission__submission_metadata": self.private_submission.submission_metadata,
                }
            ],
        }

        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.url, {})
        self.assertEqual(response.data["count"], expected["count"])
        self.assertEqual(response.data["next"], expected["next"])
        self.assertEqual(response.data["previous"], expected["previous"])
        self.assertEqual(response.data["results"], expected["results"])
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_private_leaderboard_when_user_is_participant(self):
        self.url = reverse_lazy(
            "jobs:leaderboard",
            kwargs={
                "challenge_phase_split_id": self.private_challenge_phase_split.id
            },
        )

        expected = {"error": "Sorry, the leaderboard is not public!"}

        self.client.force_authenticate(user=self.user1)

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class UpdateSubmissionTest(BaseAPITestClass):
    def setUp(self):
        super(UpdateSubmissionTest, self).setUp()

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
            when_made_public=timezone.now(),
        )
        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )
        self.datasetSplit = DatasetSplit.objects.create(
            name="Test", codename="Test"
        )
        self.leaderboard = Leaderboard.objects.create(
            schema={"labels": ["metric1", "metric2"]}
        )
        self.challengephasesplit = ChallengePhaseSplit.objects.create(
            challenge_phase=self.challenge_phase,
            dataset_split=self.datasetSplit,
            leaderboard=self.leaderboard,
            visibility=3,
        )

    def test_update_submission_data_when_user_is_not_a_host(self):
        self.url = reverse_lazy(
            "jobs:update_submission",
            kwargs={"challenge_pk": self.challenge.pk},
        )

        expected = {
            "error": "Sorry, you are not authorized to make this request!"
        }
        self.client.force_authenticate(user=self.user1)
        response = self.client.put(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_submission_for_invalid_submission_status(self):
        self.url = reverse_lazy(
            "jobs:update_submission",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.data = {
            "challenge_phase": self.challenge_phase.id,
            "submission": self.submission.id,
            "submission_status": "XYZ",
            "stdout": "qwerty",
            "stderr": "qwerty",
            "result": json.dumps(
                [
                    {
                        "split": self.datasetSplit.codename,
                        "show_to_participant": True,
                        "accuracies": {"metric1": 60, "metric2": 30},
                    }
                ]
            ),
        }

        expected = {"error": "Sorry, submission status is invalid"}
        self.client.force_authenticate(user=self.challenge_host.user)
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_submission_for_False_submission_status(self):
        self.url = reverse_lazy(
            "jobs:update_submission",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.data = {
            "challenge_phase": self.challenge_phase.id,
            "submission": self.submission.id,
            "submission_status": "CANCELLED",
            "stdout": "qwerty",
            "stderr": "qwerty",
            "result": json.dumps(
                [
                    {
                        "split": self.datasetSplit.codename,
                        "show_to_participant": True,
                        "accuracies": {"metric1": 60, "metric2": 30},
                    }
                ]
            ),
        }

        expected = {
            "success": "Submission result has been successfully updated"
        }
        self.client.force_authenticate(user=self.challenge_host.user)
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_submission_for_submission_status_not_provided(self):
        self.url = reverse_lazy(
            "jobs:update_submission",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.data = {
            "challenge_phase": self.challenge_phase.id,
            "submission": self.submission.id,
            "stdout": "qwerty",
            "stderr": "qwerty",
            "result": json.dumps(
                [
                    {
                        "split": self.datasetSplit.codename,
                        "show_to_participant": True,
                        "accuracies": {"metric1": 60, "metric2": 30},
                    }
                ]
            ),
        }

        expected = {"error": "Sorry, submission status is invalid"}
        self.client.force_authenticate(user=self.challenge_host.user)
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_submission_for_successful_submission(self):
        self.url = reverse_lazy(
            "jobs:update_submission",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.data = {
            "challenge_phase": self.challenge_phase.id,
            "submission": self.submission.id,
            "submission_status": "FINISHED",
            "stdout": "qwerty",
            "stderr": "qwerty",
            "result": json.dumps(
                [
                    {
                        "split": self.datasetSplit.codename,
                        "show_to_participant": True,
                        "accuracies": {"metric1": 60, "metric2": 30},
                    }
                ]
            ),
        }
        expected = {
            "success": "Submission result has been successfully updated"
        }
        self.client.force_authenticate(user=self.challenge_host.user)
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_submission_for_invalid_data_in_result_key(self):
        self.url = reverse_lazy(
            "jobs:update_submission",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.data = {
            "challenge_phase": self.challenge_phase.id,
            "submission": self.submission.id,
            "submission_status": "FINISHED",
            "stdout": "qwerty",
            "stderr": "qwerty",
            "result": [
                {
                    "split": "split1",
                    "accuracies": {"score": 100},
                    "show_to_participant": True,
                }
            ],
        }

        # expected = {
        #     "error": "`result` key contains invalid data with error "
        #     "the JSON object must be str, bytes or bytearray, not list."
        #     "Please try again with correct format."
        # }
        self.client.force_authenticate(user=self.challenge_host.user)
        response = self.client.put(self.url, self.data)
        # Fix the travis build by un-commenting this line.
        # self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_submission_when_challenge_phase_split_not_exist(self):
        self.url = reverse_lazy(
            "jobs:update_submission",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.data = {
            "challenge_phase": self.challenge_phase.id,
            "submission": self.submission.id,
            "submission_status": "FINISHED",
            "stdout": "qwerty",
            "stderr": "qwerty",
            "result": json.dumps(
                [
                    {
                        "split": "split1-codename",
                        "show_to_participant": True,
                        "accuracies": {"metric1": 60, "metric2": 30},
                    }
                ]
            ),
        }
        expected = {
            "error": "Challenge Phase Split does not exist with phase_id: {} and"
            "split codename: split1-codename".format(self.challenge_phase.pk)
        }
        self.client.force_authenticate(user=self.challenge_host.user)
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_submission_for_missing_metrics(self):
        self.url = reverse_lazy(
            "jobs:update_submission",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.data = {
            "challenge_phase": self.challenge_phase.id,
            "submission": self.submission.id,
            "submission_status": "FINISHED",
            "stdout": "qwerty",
            "stderr": "qwerty",
            "result": json.dumps(
                [
                    {
                        "split": self.datasetSplit.codename,
                        "show_to_participant": True,
                        "accuracies": {"metric": 60, "metric1": 30},
                    }
                ]
            ),
        }
        expected = {
            "error": "Following metrics are missing in the"
            "leaderboard data: ['metric']"
        }
        self.client.force_authenticate(user=self.challenge_host.user)
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_submission_for_malformed_metrics(self):
        self.url = reverse_lazy(
            "jobs:update_submission",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.data = {
            "challenge_phase": self.challenge_phase.id,
            "submission": self.submission.id,
            "submission_status": "FINISHED",
            "stdout": "qwerty",
            "stderr": "qwerty",
            "result": json.dumps(
                [
                    {
                        "split": self.datasetSplit.codename,
                        "show_to_participant": True,
                        "accuracies": {"metric1": "60", "metric2": 30},
                    }
                ]
            ),
        }
        malformed_metrics = []
        malformed_metrics.append(("metric1", type("60")))
        expected = {
            "error": "Values for following metrics are not of"
            "float/int: {}".format(malformed_metrics)
        }
        self.client.force_authenticate(user=self.challenge_host.user)
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
