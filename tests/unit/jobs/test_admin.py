import os
import shutil
from datetime import timedelta
from unittest.mock import patch

from allauth.account.models import EmailAddress
from challenges.models import Challenge, ChallengePhase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from hosts.models import ChallengeHostTeam
from jobs.admin import SubmissionAdmin
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam
from rest_framework.test import APIClient, APITestCase


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
        )

        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        shutil.rmtree("/tmp/evalai")


class MockRequest(object):
    pass


request = MockRequest()


class SubmissionAdminTest(BaseAPITestClass):
    """
    Test case for re-running submissions from admin
    """

    def setUp(self):
        super(SubmissionAdminTest, self).setUp()
        self.app_admin = SubmissionAdmin(Submission, AdminSite())

    def test_submit_job_to_worker(self):
        Submission.objects.filter(status=self.submission.status).update(
            status="finished"
        )
        queryset = Submission.objects.filter(status="finished")
        self.app_admin.submit_job_to_worker(request, queryset)
        self.assertEqual(
            Submission.objects.filter(status="submitted").count(), 1
        )

    def test_make_submission_public(self):
        # make all submissions private before test
        Submission.objects.filter(is_public=self.submission.is_public).update(
            is_public=False
        )
        queryset = Submission.objects.filter(is_public=False)
        self.app_admin.make_submission_public(request, queryset)
        self.assertEqual(Submission.objects.filter(is_public=True).count(), 1)

    def test_make_submission_private(self):
        # make all submissions public before test
        Submission.objects.filter(is_public=False).update(is_public=True)
        queryset = Submission.objects.filter(is_public=True)
        self.app_admin.make_submission_private(request, queryset)
        self.assertEqual(Submission.objects.filter(is_public=False).count(), 1)

    def test_change_submission_status_to_cancel(self):
        Submission.objects.all().update(status="submitted")
        queryset = Submission.objects.filter(status="submitted")
        self.app_admin.change_submission_status_to_cancel(request, queryset)
        self.assertEqual(
            Submission.objects.filter(status=Submission.CANCELLED).count(),
            queryset.count(),
        )

    def test_change_submission_status_to_cancel_only_selected(self):
        other_submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="finished",
            input_file=self.challenge_phase.test_annotation,
            method_name="Other Method",
            method_description="Other Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=False,
        )
        other_submission.status = "finished"
        other_submission.save()
        queryset = Submission.objects.filter(id=self.submission.id)
        self.app_admin.change_submission_status_to_cancel(request, queryset)
        self.assertEqual(
            Submission.objects.get(id=self.submission.id).status,
            Submission.CANCELLED,
        )
        self.assertEqual(
            Submission.objects.get(id=other_submission.id).status,
            "finished",
        )

    def test_get_challenge_name_and_id(self):
        result = self.app_admin.get_challenge_name_and_id(self.submission)
        expected = f"{self.challenge.title} - {self.challenge.id}"
        self.assertEqual(result, expected)

    @patch("jobs.admin.publish_submission_message")
    @patch("jobs.admin.handle_submission_rerun")
    @patch("jobs.admin.ensure_workers_for_host_submission")
    def test_submit_job_calls_ensure_workers(
        self, mock_ensure_workers, mock_rerun, mock_publish
    ):
        """ensure_workers_for_host_submission should be called for
        each unique challenge when re-running submissions."""
        mock_rerun.return_value = {"challenge_pk": self.challenge.pk}
        queryset = Submission.objects.filter(pk=self.submission.pk)

        self.app_admin.submit_job_to_worker(request, queryset)

        mock_ensure_workers.assert_called_once_with(self.challenge)
        mock_rerun.assert_called_once()
        mock_publish.assert_called_once()

    @patch("jobs.admin.publish_submission_message")
    @patch("jobs.admin.handle_submission_rerun")
    @patch("jobs.admin.ensure_workers_for_host_submission")
    def test_submit_job_calls_ensure_workers_once_per_challenge(
        self, mock_ensure_workers, mock_rerun, mock_publish
    ):
        """ensure_workers_for_host_submission should only be called once
        per challenge even when re-running multiple submissions."""
        second_submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="finished",
            input_file=self.challenge_phase.test_annotation,
            method_name="Second Method",
            method_description="Second Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )
        mock_rerun.return_value = {"challenge_pk": self.challenge.pk}
        queryset = Submission.objects.filter(
            pk__in=[self.submission.pk, second_submission.pk]
        )

        self.app_admin.submit_job_to_worker(request, queryset)

        mock_ensure_workers.assert_called_once_with(self.challenge)
        self.assertEqual(mock_rerun.call_count, 2)
        self.assertEqual(mock_publish.call_count, 2)

    @patch("jobs.admin.publish_submission_message")
    @patch("jobs.admin.handle_submission_rerun")
    @patch("jobs.admin.ensure_workers_for_host_submission")
    def test_submit_job_calls_ensure_workers_per_distinct_challenge(
        self, mock_ensure_workers, mock_rerun, mock_publish
    ):
        """ensure_workers_for_host_submission should be called once per
        distinct challenge when submissions span multiple challenges."""
        second_challenge = Challenge.objects.create(
            title="Second Challenge",
            description="Description",
            terms_and_conditions="Terms",
            submission_guidelines="Guidelines",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
        )
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            second_phase = ChallengePhase.objects.create(
                name="Second Phase",
                description="Description",
                leaderboard_public=False,
                is_public=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=second_challenge,
                test_annotation=SimpleUploadedFile(
                    "test_file2.txt",
                    b"Dummy content",
                    content_type="text/plain",
                ),
            )
        second_submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=second_phase,
            created_by=self.challenge_host_team.created_by,
            status="finished",
            input_file=second_phase.test_annotation,
            method_name="Other Method",
            method_description="Other Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )
        mock_rerun.return_value = {"challenge_pk": self.challenge.pk}
        queryset = Submission.objects.filter(
            pk__in=[self.submission.pk, second_submission.pk]
        )

        self.app_admin.submit_job_to_worker(request, queryset)

        self.assertEqual(mock_ensure_workers.call_count, 2)
        self.assertEqual(mock_rerun.call_count, 2)
        self.assertEqual(mock_publish.call_count, 2)
