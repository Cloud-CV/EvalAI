import csv
import io
import json
import os
import shutil
from datetime import timedelta
from os.path import join
from smtplib import SMTPException

import boto3
import mock
import requests
import responses
from allauth.account.models import EmailAddress
from challenges.models import (
    Challenge,
    ChallengeConfiguration,
    ChallengePhase,
    ChallengePhaseSplit,
    ChallengePrize,
    ChallengeSponsor,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
    StarChallenge,
)
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse_lazy
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission
from jobs.serializers import ChallengeSubmissionManagementSerializer
from moto import mock_s3
from participants.models import Participant, ParticipantTeam
from rest_framework import status
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

        self.participant_user = User.objects.create(
            username="someparticipantuser",
            email="participantuser@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.participant_user,
            email="participantuser@test.com",
            primary=True,
            verified=True,
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
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=False,
            is_registration_open=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
            github_repository="challenge/github_repo",
        )
        self.challenge.slug = (
            f"{self.challenge.title.replace(' ', '-').lower()}-{self.challenge.pk}"
        )[:199]
        self.challenge.save()

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


class GetChallengeTest(BaseAPITestClass):
    url = reverse_lazy("challenges:get_challenge_list")

    def setUp(self):
        super().setUp()

        self.disabled_challenge = Challenge.objects.create(
            title="Disabled Challenge",
            short_description="Short description for disabled challenge",
            description="Description for disabled challenge",
            terms_and_conditions="Terms and conditions for disabled challenge",
            submission_guidelines="Submission guidelines for disabled challenge",  # noqa: C0301
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            is_disabled=True,
            leaderboard_description=None,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
        )

        self.url = reverse_lazy(
            "challenges:get_challenge_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )

    def test_get_challenge(self):
        expected = [
            {
                "id": self.challenge.pk,
                "title": self.challenge.title,
                "description": self.challenge.description,
                "short_description": self.challenge.short_description,
                "terms_and_conditions": self.challenge.terms_and_conditions,
                "submission_guidelines": self.challenge.submission_guidelines,
                "evaluation_details": self.challenge.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge.creator.pk,
                    "team_name": self.challenge.creator.team_name,
                    "created_by": self.challenge.creator.created_by.username,
                    "team_url": self.challenge.creator.team_url,
                },
                "domain": self.challenge.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge.list_tags,
                "has_prize": self.challenge.has_prize,
                "has_sponsors": self.challenge.has_sponsors,
                "published": self.challenge.published,
                "submission_time_limit": self.challenge.submission_time_limit,
                "is_registration_open": self.challenge.is_registration_open,
                "enable_forum": self.challenge.enable_forum,
                "leaderboard_description": self.challenge.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
                "manual_participant_approval": self.challenge.manual_participant_approval,  # noqa: C0301
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": False,
                "forum_url": self.challenge.forum_url,
                "is_docker_based": self.challenge.is_docker_based,
                "is_static_dataset_code_upload": self.challenge.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge.slug,
                "max_docker_image_size": self.challenge.max_docker_image_size,
                "cli_version": self.challenge.cli_version,
                "remote_evaluation": self.challenge.remote_evaluation,
                "allow_resuming_submissions": self.challenge.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge.workers,
                "created_at": f"{self.challenge.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge.cpu_only_jobs,
                "job_cpu_cores": self.challenge.job_cpu_cores,
                "job_memory": self.challenge.job_memory,
                "uses_ec2_worker": self.challenge.uses_ec2_worker,
                "evaluation_module_error": self.challenge.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge.ec2_storage,
                "ephemeral_storage": self.challenge.ephemeral_storage,
                "worker_image_url": self.challenge.worker_image_url,
                "worker_instance_type": self.challenge.worker_instance_type,
                "sqs_retention_period": self.challenge.sqs_retention_period,
                "github_repository": self.challenge.github_repository,
                "github_branch": self.challenge.github_branch,
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(
            response.data["results"], json.loads(json.dumps(expected))
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_for_challenge_does_not_exist(self):
        self.url = reverse_lazy(
            "challenges:get_challenge_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk + 1},
        )
        expected = {"error": "ChallengeHostTeam does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class GetParticipantTeamNameTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()

        self.participant = Participant.objects.create(
            user=self.user,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

        self.challenge.participant_teams.add(self.participant_team)

    def test_team_name_for_challenge(self):
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:participant_team_detail_for_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )

        expected = "Participant Team for Challenge"
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["participant_team"]["team_name"], expected
        )

    def test_team_name_for_challenge_with_participant_team_does_not_exist(
        self,
    ):
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:participant_team_detail_for_challenge",
            kwargs={"challenge_pk": self.challenge.pk + 2},
        )
        expected = {"error": "You are not a participant!"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class GetApprovedParticipantTeamNameTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()

        self.participant = Participant.objects.create(
            user=self.user,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

    def test_add_participant_team_to_approved_list_when_not_in_participant_team(  # noqa: C0301
        self,
    ):
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_approved_list",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team.pk,
            },
        )
        expected = {"error": "Participant isn't interested in challenge"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_participant_team_to_approved_list_when_team_doesnt_exist(
        self,
    ):
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_approved_list",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team.pk + 1,
            },
        )
        expected = {"error": "Participant Team does not exist"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

        self.challenge.participant_teams.add(self.participant_team)

    def test_team_in_approved_participant_team(self):
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:get_participant_teams_for_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_add_participant_team_already_approved(self):
        # pylint: disable=attribute-defined-outside-init
        self.challenge.approved_participant_teams.add(self.participant_team)
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_approved_list",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team.pk,
            },
        )
        expected = {"error": "Participant Team already approved"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_remove_participant_team_doesnt_exist(self):
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:remove_participant_team_from_approved_list",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team.pk + 1,
            },
        )
        expected = {"error": "Participant Team does not exist"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_remove_participant_team(self):
        # pylint: disable=attribute-defined-outside-init
        self.challenge.approved_participant_teams.add(self.participant_team)
        self.url = reverse_lazy(
            "challenges:remove_participant_team_from_approved_list",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team.pk,
            },
        )
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class DeregisterParticipantTeamTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()

        self.user5 = User.objects.create(
            username="otheruser",
            password="other_secret_password",
            email="user5@test.com",
        )

        EmailAddress.objects.create(
            user=self.user5,
            email="user5@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Other Test Challenge Host Team", created_by=self.user5
        )

        self.participant = Participant.objects.create(
            user=self.user,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

        self.challenge.participant_teams.add(self.participant_team)

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user5,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

    def create_submission(self):
        # pylint: disable=attribute-defined-outside-init
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase1 = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
            )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.submission1 = Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase1,
                created_by=self.challenge_host_team.created_by,
                status="submitted",
                input_file=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                method_name="Test Method 1",
                method_description="Test Description 1",
                project_url="http://testserver1/",
                publication_url="http://testserver1/",
                is_public=True,
                is_flagged=True,
            )

    def test_deregister_participant_team(self):
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:deregister_participant_team_from_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )

        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data["success"], "Successfully deregistered!"
        )

    def test_deregister_participant_team_with_challenge_does_not_exist(
        self,
    ):
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:deregister_participant_team_from_challenge",
            kwargs={"challenge_pk": self.challenge.pk + 2},
        )
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_deregister_participant_team_with_submission_exist(self):
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:deregister_participant_team_from_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.create_submission()
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class CreateChallengeTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )
        self.data = {
            "title": "New Test Challenge",
            "short_description": "Short description for new test challenge",
            "description": "Description for new test challenge",
            "terms_and_conditions": "Terms and conditions for new test challenge",  # noqa: C0301
            "submission_guidelines": "Submission guidelines for new test challenge",  # noqa: C0301
            "creator": {
                "id": self.challenge_host_team.pk,
                "team_name": self.challenge_host_team.team_name,
                "created_by": self.challenge_host_team.created_by.pk,
            },
            "published": False,
            "is_registration_open": True,
            "enable_forum": True,
            "leaderboard_description": "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",  # noqa: C0301
            "anonymous_leaderboard": False,
            "start_date": timezone.now() - timedelta(days=2),
            "end_date": timezone.now() + timedelta(days=1),
        }

    def test_create_challenge_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_with_no_data(self):
        del self.data["title"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_challenge_host_team_ownership(self):
        del self.data["creator"]
        self.challenge_host.delete()
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetParticularChallenge(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_detail",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "challenge_pk": self.challenge.pk,
            },
        )

    def test_get_particular_challenge(self):
        expected = {
            "id": self.challenge.pk,
            "title": self.challenge.title,
            "short_description": self.challenge.short_description,
            "description": self.challenge.description,
            "terms_and_conditions": self.challenge.terms_and_conditions,
            "submission_guidelines": self.challenge.submission_guidelines,
            "evaluation_details": self.challenge.evaluation_details,
            "image": None,
            "start_date": f"{self.challenge.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "creator": {
                "id": self.challenge.creator.pk,
                "team_name": self.challenge.creator.team_name,
                "created_by": self.challenge.creator.created_by.username,
                "team_url": self.challenge.creator.team_url,
            },
            "domain": self.challenge.domain,
            "domain_name": "Computer Vision",
            "list_tags": self.challenge.list_tags,
            "has_prize": self.challenge.has_prize,
            "has_sponsors": self.challenge.has_sponsors,
            "published": self.challenge.published,
            "submission_time_limit": self.challenge.submission_time_limit,
            "is_registration_open": self.challenge.is_registration_open,
            "enable_forum": self.challenge.enable_forum,
            "leaderboard_description": self.challenge.leaderboard_description,
            "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
            "manual_participant_approval": self.challenge.manual_participant_approval,  # noqa: C0301
            "is_active": True,
            "allowed_email_domains": [],
            "blocked_email_domains": [],
            "banned_email_ids": [],
            "approved_by_admin": False,
            "forum_url": self.challenge.forum_url,
            "is_docker_based": self.challenge.is_docker_based,
            "is_static_dataset_code_upload": self.challenge.is_static_dataset_code_upload,  # noqa: C0301
            "slug": self.challenge.slug,
            "max_docker_image_size": self.challenge.max_docker_image_size,
            "cli_version": self.challenge.cli_version,
            "remote_evaluation": self.challenge.remote_evaluation,
            "allow_resuming_submissions": self.challenge.allow_resuming_submissions,  # noqa: C0301
            "allow_host_cancel_submissions": self.challenge.allow_host_cancel_submissions,  # noqa: C0301
            "allow_cancel_running_submissions": self.challenge.allow_cancel_running_submissions,  # noqa: C0301
            "allow_participants_resubmissions": self.challenge.allow_participants_resubmissions,  # noqa: C0301
            "workers": self.challenge.workers,
            "created_at": f"{self.challenge.created_at.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "queue": self.challenge.queue,
            "worker_cpu_cores": 512,
            "worker_memory": 1024,
            "cpu_only_jobs": self.challenge.cpu_only_jobs,
            "job_cpu_cores": self.challenge.job_cpu_cores,
            "job_memory": self.challenge.job_memory,
            "uses_ec2_worker": self.challenge.uses_ec2_worker,
            "evaluation_module_error": self.challenge.evaluation_module_error,
            "ec2_storage": self.challenge.ec2_storage,
            "ephemeral_storage": self.challenge.ephemeral_storage,
            "worker_image_url": self.challenge.worker_image_url,
            "worker_instance_type": self.challenge.worker_instance_type,
            "sqs_retention_period": self.challenge.sqs_retention_period,
            "github_repository": self.challenge.github_repository,
            "github_branch": self.challenge.github_branch,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_challenge_when_user_is_not_its_creator(self):
        # pylint: disable=attribute-defined-outside-init
        self.user1 = User.objects.create(
            username="someuser1",
            email="user1@test.com",
            password="secret_psassword",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@test.com",
            primary=True,
            verified=True,
        )

        self.client.force_authenticate(user=self.user1)

        expected = {
            "detail": "Sorry, you are not allowed to perform this operation!"
        }

        response = self.client.put(
            self.url, {"title": "Rose Challenge", "description": "Version 2.0"}
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_challenge_when_user_is_its_creator(self):
        new_title = "Rose Challenge"
        new_description = "New description."
        expected = {
            "id": self.challenge.pk,
            "title": new_title,
            "short_description": self.challenge.short_description,
            "description": new_description,
            "terms_and_conditions": self.challenge.terms_and_conditions,
            "submission_guidelines": self.challenge.submission_guidelines,
            "evaluation_details": self.challenge.evaluation_details,
            "image": None,
            "start_date": f"{self.challenge.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "creator": {
                "id": self.challenge.creator.pk,
                "team_name": self.challenge.creator.team_name,
                "created_by": self.challenge.creator.created_by.username,
                "team_url": self.challenge.creator.team_url,
            },
            "domain": self.challenge.domain,
            "domain_name": "Computer Vision",
            "list_tags": self.challenge.list_tags,
            "has_prize": self.challenge.has_prize,
            "has_sponsors": self.challenge.has_sponsors,
            "published": self.challenge.published,
            "submission_time_limit": self.challenge.submission_time_limit,
            "is_registration_open": self.challenge.is_registration_open,
            "enable_forum": self.challenge.enable_forum,
            "leaderboard_description": self.challenge.leaderboard_description,
            "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
            "manual_participant_approval": self.challenge.manual_participant_approval,  # noqa: C0301
            "is_active": True,
            "allowed_email_domains": [],
            "blocked_email_domains": [],
            "banned_email_ids": [],
            "approved_by_admin": False,
            "forum_url": self.challenge.forum_url,
            "is_docker_based": self.challenge.is_docker_based,
            "is_static_dataset_code_upload": self.challenge.is_static_dataset_code_upload,  # noqa: C0301
            "slug": f"{new_title.replace(' ', '-').lower()}-{self.challenge.pk}"[
                :199
            ],
            "max_docker_image_size": self.challenge.max_docker_image_size,
            "cli_version": self.challenge.cli_version,
            "remote_evaluation": self.challenge.remote_evaluation,
            "allow_resuming_submissions": self.challenge.allow_resuming_submissions,  # noqa: C0301
            "allow_host_cancel_submissions": self.challenge.allow_host_cancel_submissions,  # noqa: C0301
            "allow_cancel_running_submissions": self.challenge.allow_cancel_running_submissions,  # noqa: C0301
            "allow_participants_resubmissions": self.challenge.allow_participants_resubmissions,  # noqa: C0301
            "workers": self.challenge.workers,
            "created_at": f"{self.challenge.created_at.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "queue": self.challenge.queue,
            "worker_cpu_cores": 512,
            "worker_memory": 1024,
            "cpu_only_jobs": self.challenge.cpu_only_jobs,
            "job_cpu_cores": self.challenge.job_cpu_cores,
            "job_memory": self.challenge.job_memory,
            "uses_ec2_worker": self.challenge.uses_ec2_worker,
            "evaluation_module_error": self.challenge.evaluation_module_error,
            "ec2_storage": self.challenge.ec2_storage,
            "ephemeral_storage": self.challenge.ephemeral_storage,
            "worker_image_url": self.challenge.worker_image_url,
            "worker_instance_type": self.challenge.worker_instance_type,
            "sqs_retention_period": self.challenge.sqs_retention_period,
            "github_repository": self.challenge.github_repository,
            "github_branch": self.challenge.github_branch,
        }
        response = self.client.put(
            self.url, {"title": new_title, "description": new_description}
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_does_not_exist(self):
        self.url = reverse_lazy(
            "challenges:get_challenge_detail",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "challenge_pk": self.challenge.pk + 1,
            },
        )
        expected = {"error": "Challenge does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_host_team_for_challenge_does_not_exist(self):
        self.url = reverse_lazy(
            "challenges:get_challenge_detail",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk + 1,
                "challenge_pk": self.challenge.pk,
            },
        )
        expected = {"error": "ChallengeHostTeam does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class UpdateParticularChallenge(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_detail",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "challenge_pk": self.challenge.pk,
            },
        )

        self.partial_update_challenge_title = "Partial Update Test Challenge"
        self.update_challenge_title = "Update Test Challenge"
        self.update_submission_guidelines = "Update Submission Guidelines"
        self.data = {
            "title": self.update_challenge_title,
            "submission_guidelines": self.update_submission_guidelines,
        }

    def test_particular_challenge_partial_update(self):
        # pylint: disable=attribute-defined-outside-init
        self.partial_update_data = {
            "title": self.partial_update_challenge_title
        }
        expected = {
            "id": self.challenge.pk,
            "title": self.partial_update_challenge_title,
            "short_description": self.challenge.short_description,
            "description": self.challenge.description,
            "terms_and_conditions": self.challenge.terms_and_conditions,
            "submission_guidelines": self.challenge.submission_guidelines,
            "evaluation_details": self.challenge.evaluation_details,
            "image": None,
            "start_date": f"{self.challenge.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "creator": {
                "id": self.challenge.creator.pk,
                "team_name": self.challenge.creator.team_name,
                "created_by": self.challenge.creator.created_by.username,
                "team_url": self.challenge.creator.team_url,
            },
            "domain": self.challenge.domain,
            "domain_name": "Computer Vision",
            "list_tags": self.challenge.list_tags,
            "has_prize": self.challenge.has_prize,
            "has_sponsors": self.challenge.has_sponsors,
            "published": self.challenge.published,
            "submission_time_limit": self.challenge.submission_time_limit,
            "is_registration_open": self.challenge.is_registration_open,
            "enable_forum": self.challenge.enable_forum,
            "leaderboard_description": self.challenge.leaderboard_description,
            "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
            "manual_participant_approval": self.challenge.manual_participant_approval,  # noqa: C0301
            "is_active": True,
            "allowed_email_domains": [],
            "blocked_email_domains": [],
            "banned_email_ids": [],
            "approved_by_admin": False,
            "forum_url": self.challenge.forum_url,
            "is_docker_based": self.challenge.is_docker_based,
            "is_static_dataset_code_upload": self.challenge.is_static_dataset_code_upload,  # noqa: C0301
            "slug": (
                f"{self.partial_update_challenge_title.replace(' ', '-').lower()}-"
                f"{self.challenge.pk}"
            )[:199],
            "max_docker_image_size": self.challenge.max_docker_image_size,
            "cli_version": self.challenge.cli_version,
            "remote_evaluation": self.challenge.remote_evaluation,
            "allow_resuming_submissions": self.challenge.allow_resuming_submissions,  # noqa: C0301
            "allow_host_cancel_submissions": self.challenge.allow_host_cancel_submissions,  # noqa: C0301
            "allow_cancel_running_submissions": self.challenge.allow_cancel_running_submissions,  # noqa: C0301
            "allow_participants_resubmissions": self.challenge.allow_participants_resubmissions,  # noqa: C0301
            "workers": self.challenge.workers,
            "created_at": f"{self.challenge.created_at.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "queue": self.challenge.queue,
            "worker_cpu_cores": 512,
            "worker_memory": 1024,
            "cpu_only_jobs": self.challenge.cpu_only_jobs,
            "job_cpu_cores": self.challenge.job_cpu_cores,
            "job_memory": self.challenge.job_memory,
            "uses_ec2_worker": self.challenge.uses_ec2_worker,
            "evaluation_module_error": self.challenge.evaluation_module_error,
            "ec2_storage": self.challenge.ec2_storage,
            "ephemeral_storage": self.challenge.ephemeral_storage,
            "worker_image_url": self.challenge.worker_image_url,
            "worker_instance_type": self.challenge.worker_instance_type,
            "sqs_retention_period": self.challenge.sqs_retention_period,
            "github_repository": self.challenge.github_repository,
            "github_branch": self.challenge.github_branch,
        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_update(self):
        expected = {
            "id": self.challenge.pk,
            "title": self.update_challenge_title,
            "short_description": self.challenge.short_description,
            "description": self.challenge.description,
            "terms_and_conditions": self.challenge.terms_and_conditions,
            "submission_guidelines": self.update_submission_guidelines,
            "evaluation_details": self.challenge.evaluation_details,
            "image": None,
            "start_date": f"{self.challenge.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "creator": {
                "id": self.challenge.creator.pk,
                "team_name": self.challenge.creator.team_name,
                "created_by": self.challenge.creator.created_by.username,
                "team_url": self.challenge.creator.team_url,
            },
            "domain": self.challenge.domain,
            "domain_name": "Computer Vision",
            "list_tags": self.challenge.list_tags,
            "has_prize": self.challenge.has_prize,
            "has_sponsors": self.challenge.has_sponsors,
            "published": self.challenge.published,
            "submission_time_limit": self.challenge.submission_time_limit,
            "is_registration_open": self.challenge.is_registration_open,
            "enable_forum": self.challenge.enable_forum,
            "leaderboard_description": self.challenge.leaderboard_description,
            "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
            "manual_participant_approval": self.challenge.manual_participant_approval,  # noqa: C0301
            "is_active": True,
            "allowed_email_domains": [],
            "blocked_email_domains": [],
            "banned_email_ids": [],
            "approved_by_admin": False,
            "forum_url": self.challenge.forum_url,
            "is_docker_based": self.challenge.is_docker_based,
            "is_static_dataset_code_upload": self.challenge.is_static_dataset_code_upload,  # noqa: C0301
            "slug": (
                f"{self.update_challenge_title.replace(' ', '-').lower()}-"
                f"{self.challenge.pk}"
            )[:199],
            "max_docker_image_size": self.challenge.max_docker_image_size,
            "cli_version": self.challenge.cli_version,
            "remote_evaluation": self.challenge.remote_evaluation,
            "allow_resuming_submissions": self.challenge.allow_resuming_submissions,  # noqa: C0301
            "allow_host_cancel_submissions": self.challenge.allow_host_cancel_submissions,  # noqa: C0301
            "allow_cancel_running_submissions": self.challenge.allow_cancel_running_submissions,  # noqa: C0301
            "allow_participants_resubmissions": self.challenge.allow_participants_resubmissions,  # noqa: C0301
            "workers": self.challenge.workers,
            "created_at": f"{self.challenge.created_at.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "queue": self.challenge.queue,
            "worker_cpu_cores": 512,
            "worker_memory": 1024,
            "cpu_only_jobs": self.challenge.cpu_only_jobs,
            "job_cpu_cores": self.challenge.job_cpu_cores,
            "job_memory": self.challenge.job_memory,
            "uses_ec2_worker": self.challenge.uses_ec2_worker,
            "evaluation_module_error": self.challenge.evaluation_module_error,
            "ec2_storage": self.challenge.ec2_storage,
            "ephemeral_storage": self.challenge.ephemeral_storage,
            "worker_image_url": self.challenge.worker_image_url,
            "worker_instance_type": self.challenge.worker_instance_type,
            "sqs_retention_period": self.challenge.sqs_retention_period,
            "github_repository": self.challenge.github_repository,
            "github_branch": self.challenge.github_branch,
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_update_with_no_data(self):
        self.data = {"title": ""}
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteParticularChallenge(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_detail",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "challenge_pk": self.challenge.pk,
            },
        )

    def test_particular_challenge_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class MapChallengeAndParticipantTeam(
    BaseAPITestClass
):  # pylint: disable=too-many-instance-attributes
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team.pk,
            },
        )

        # user who create a challenge host team
        self.user2 = User.objects.create(
            username="someuser2",
            email="user@example2.com",
            password="some_secret_password",
        )
        # user who maps a participant team to a challenge
        self.user3 = User.objects.create(
            username="someuser3",
            email="user@example3.com",
            password="some_secret_password",
        )

        # user invited to the participant team
        self.user4 = User.objects.create(
            username="someuser4",
            email="user@test.com",
            password="some_secret_password",
        )

        EmailAddress.objects.create(
            user=self.user4,
            email="user4@test.com",
            primary=True,
            verified=True,
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@example2.com",
            primary=True,
            verified=True,
        )

        self.challenge_host_team2 = ChallengeHostTeam.objects.create(
            team_name="Some Test Challenge Host Team", created_by=self.user2
        )

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user2,
            team_name=self.challenge_host_team2,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.challenge_host3 = ChallengeHost.objects.create(
            user=self.user3,
            team_name=self.challenge_host_team2,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.challenge2 = Challenge.objects.create(
            title="Some Test Challenge",
            short_description="Short description for some test challenge",
            description="Description for some test challenge",
            terms_and_conditions="Terms and conditions for some test challenge",  # noqa: C0301
            submission_guidelines="Submission guidelines for some test challenge",  # noqa: C0301
            creator=self.challenge_host_team2,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            leaderboard_description="Pellentesque at dictum odio, sit amet fringilla sem",  # noqa: C0301
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            allowed_email_domains=[],
            blocked_email_domains=[],
            approved_by_admin=False,
        )

        self.participant_team2 = ParticipantTeam.objects.create(
            team_name="Some Participant Team", created_by=self.user3
        )

        self.participant_team3 = ParticipantTeam.objects.create(
            team_name="Some Participant Team by User 4", created_by=self.user4
        )

        self.participant2 = Participant.objects.create(
            user=self.user3,
            status=Participant.SELF,
            team=self.participant_team2,
        )

        self.participant3 = Participant.objects.create(
            user=self.user4,
            status=Participant.ACCEPTED,
            team=self.participant_team2,
        )

        self.participant4 = Participant.objects.create(
            user=self.user4,
            status=Participant.SELF,
            team=self.participant_team3,
        )

        self.participant_team4 = ParticipantTeam.objects.create(
            team_name="Some Participant Team 2 by User 2",
            created_by=self.user2,
        )

        self.participant5 = Participant.objects.create(
            user=self.user3,
            status=Participant.ACCEPTED,
            team=self.participant_team4,
        )

    def test_registration_is_closed_for_a_particular_challenge(self):
        self.challenge2.is_registration_open = False
        self.challenge2.save()
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge2.pk,
                "participant_team_pk": self.participant_team3.pk,
            },
        )
        expected = {"error": "Registration is closed for this challenge!"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_map_challenge_and_participant_team_together(self):
        self.client.force_authenticate(user=self.participant_team.created_by)
        response = self.client.post(self.url, {})
        self.client.force_authenticate(user=self.participant_team.created_by)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # to check when the api is hit again
        expected = {
            "error": "Team already exists",
            "challenge_id": self.challenge.pk,
            "participant_team_id": self.participant_team.pk,
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_for_mapping_with_participant_team_does_not_exist(  # noqa: C0301
        self,
    ):
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge.pk + 2,
                "participant_team_pk": self.participant_team.pk,
            },
        )
        expected = {"error": "Challenge does not exist"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_participant_team_for_mapping_with_past_challenge(self):
        self.challenge2.end_date = timezone.now() - timedelta(days=1)
        self.challenge2.save()
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge2.pk,
                "participant_team_pk": self.participant_team3.pk,
            },
        )
        expected = {
            "error": "Sorry, cannot accept participant team since challenge is not active."  # noqa: C0301
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_participant_team_for_mapping_with_future_challenge(self):
        self.challenge2.start_date = timezone.now() + timedelta(days=3)
        self.challenge2.save()
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge2.pk,
                "participant_team_pk": self.participant_team3.pk,
            },
        )
        expected = {
            "error": "Sorry, cannot accept participant team since challenge is not active."  # noqa: C0301
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_participant_team_for_mapping_with_challenge_does_not_exist(  # noqa: C0301
        self,
    ):
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team.pk + 4,
            },
        )
        expected = {"error": "ParticipantTeam does not exist"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_participant_team_to_challenge_when_some_members_have_already_participated(  # noqa: C0301
        self,
    ):
        self.client.force_authenticate(user=self.participant_team3.created_by)
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team2.pk,
            },
        )

        self.client.post(self.url, {})

        expected = {
            "error": "Sorry, other team member(s) have already participated in the Challenge."  # noqa: C0301
            " Please participate with a different team!",
            "challenge_id": self.challenge.pk,
            "participant_team_id": self.participant_team3.pk,
        }

        # submitting the request again as a new team
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "participant_team_pk": self.participant_team3.pk,
            },
        )

        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_participation_when_participant_is_in_blocked_list(self):
        self.challenge2.blocked_email_domains.extend(["test.com", "test1.com"])
        self.challenge2.save()
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge2.pk,
                "participant_team_pk": self.participant_team3.pk,
            },
        )

        response = self.client.post(self.url, {})
        message = "Sorry, users with {} email domain(s) are not allowed to participate in this challenge."  # noqa: C0301
        expected = {"error": message.format("test.com/test1.com")}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_participation_when_participant_is_not_in_allowed_list(self):
        self.client.force_authenticate(user=self.participant_team3.created_by)
        self.challenge2.allowed_email_domains.extend(["example1", "example2"])
        self.challenge2.save()
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge2.pk,
                "participant_team_pk": self.participant_team3.pk,
            },
        )

        response = self.client.post(self.url, {})
        message = "Sorry, team consisting of users with non-{} email domain(s) are not allowed \
                    to participate in this challenge."
        expected = {"error": message.format("example1/example2")}

        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_participation_when_participant_team_member_is_not_in_allowed_list(
        self,
    ):
        self.client.force_authenticate(user=self.participant_team4.created_by)
        self.challenge2.allowed_email_domains.extend(["example1", "example2"])
        self.challenge2.save()
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge2.pk,
                "participant_team_pk": self.participant_team4.pk,
            },
        )

        response = self.client.post(self.url, {})
        message = "Sorry, team consisting of users with non-{} email domain(s) are not allowed \
                    to participate in this challenge."
        expected = {"error": message.format("example1/example2")}

        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_participation_when_participant_is_in_allowed_list(self):
        self.challenge2.allowed_email_domains.append("test.com")
        self.challenge2.save()
        self.client.force_authenticate(user=self.participant_team3.created_by)
        self.url = reverse_lazy(
            "challenges:add_participant_team_to_challenge",
            kwargs={
                "challenge_pk": self.challenge2.pk,
                "participant_team_pk": self.participant_team3.pk,
            },
        )
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class DisableChallengeTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()

        self.user1 = User.objects.create(
            username="otheruser", password="other_secret_password"
        )

        self.challenge_host_team1 = ChallengeHostTeam.objects.create(
            team_name="Other Test Challenge Host Team", created_by=self.user1
        )

        self.challenge2 = Challenge.objects.create(
            title="Other Test Challenge",
            short_description="Short description for other test challenge",
            description="Description for other test challenge",
            terms_and_conditions="Terms and conditions for other test challenge",  # noqa: C0301
            submission_guidelines="Submission guidelines for other test challenge",  # noqa: C0301
            creator=self.challenge_host_team1,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.url = reverse_lazy(
            "challenges:disable_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )

    def test_disable_a_challenge(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_particular_challenge_for_disable_does_not_exist(self):
        self.url = reverse_lazy(
            "challenges:disable_challenge",
            kwargs={"challenge_pk": self.challenge.pk + 2},
        )
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_when_user_does_not_have_permission_to_disable_particular_challenge(  # noqa: C0301
        self,
    ):
        self.url = reverse_lazy(
            "challenges:disable_challenge",
            kwargs={"challenge_pk": self.challenge2.pk},
        )
        expected = {
            "error": "Sorry, you are not allowed to perform this operation!"
        }
        response = self.client.post(self.url, {})
        self.assertEqual(list(response.data.values())[0], expected["error"])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_disable_challenge_when_user_is_a_part_of_host_team(self):
        self.url = reverse_lazy(
            "challenges:disable_challenge",
            kwargs={"challenge_pk": self.challenge2.pk},
        )
        # Now allot self.user as also a host of self.challenge_host_team1
        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team1,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_disable_a_challenge_when_user_is_not_authenticated(self):
        self.client.force_authenticate(user=None)

        expected = {"error": "Authentication credentials were not provided."}

        response = self.client.post(self.url, {})
        self.assertEqual(list(response.data.values())[0], expected["error"])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetAllChallengesTest(BaseAPITestClass):
    url = reverse_lazy("challenges:get_all_challenges")

    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_all_challenges",
            kwargs={
                "challenge_time": "PAST",
                "challenge_approved": "APPROVED",
                "challenge_published": "PUBLIC",
            },
        )

        # Present challenge
        self.challenge2 = Challenge.objects.create(
            title="Test Challenge 2",
            short_description="Short description for test challenge 2",
            description="Description for test challenge 2",
            terms_and_conditions="Terms and conditions for test challenge 2",
            submission_guidelines="Submission guidelines for test challenge 2",
            creator=self.challenge_host_team,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            approved_by_admin=True,
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            github_repository="challenge2/github_repo",
        )

        # Past Challenge challenge
        self.challenge3 = Challenge.objects.create(
            title="Test Challenge 3",
            short_description="Short description for test challenge 3",
            description="Description for test challenge 3",
            terms_and_conditions="Terms and conditions for test challenge 3",
            submission_guidelines="Submission guidelines for test challenge 3",
            creator=self.challenge_host_team,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            approved_by_admin=True,
            leaderboard_description="Donec sollicitudin, nisi vel tempor semper, nulla odio dapibus felis",  # noqa: C0301
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() - timedelta(days=1),
            github_repository="challenge3/github_repo",
        )

        # Future challenge
        self.challenge4 = Challenge.objects.create(
            title="Test Challenge 4",
            short_description="Short description for test challenge 4",
            description="Description for test challenge 4",
            terms_and_conditions="Terms and conditions for test challenge 4",
            submission_guidelines="Submission guidelines for test challenge 4",
            creator=self.challenge_host_team,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            approved_by_admin=True,
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            github_repository="challenge4/github_repo",
        )

        # Disabled challenge
        self.challenge5 = Challenge.objects.create(
            title="Test Challenge 5",
            short_description="Short description for test challenge 5",
            description="Description for test challenge 5",
            terms_and_conditions="Terms and conditions for test challenge 5",
            submission_guidelines="Submission guidelines for test challenge 5",
            creator=self.challenge_host_team,
            published=True,
            is_registration_open=True,
            enable_forum=True,
            approved_by_admin=True,
            leaderboard_description=None,
            anonymous_leaderboard=False,
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            is_disabled=True,
        )

    def test_get_past_challenges(self):
        expected = [
            {
                "id": self.challenge3.pk,
                "title": self.challenge3.title,
                "short_description": self.challenge3.short_description,
                "description": self.challenge3.description,
                "terms_and_conditions": self.challenge3.terms_and_conditions,
                "submission_guidelines": self.challenge3.submission_guidelines,
                "evaluation_details": self.challenge3.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge3.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge3.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge3.creator.pk,
                    "team_name": self.challenge3.creator.team_name,
                    "created_by": self.challenge3.creator.created_by.username,
                    "team_url": self.challenge3.creator.team_url,
                },
                "domain": self.challenge3.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge3.list_tags,
                "has_prize": self.challenge3.has_prize,
                "has_sponsors": self.challenge3.has_sponsors,
                "published": self.challenge3.published,
                "submission_time_limit": self.challenge3.submission_time_limit,
                "is_registration_open": self.challenge3.is_registration_open,
                "enable_forum": self.challenge3.enable_forum,
                "leaderboard_description": self.challenge3.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge3.anonymous_leaderboard,
                "manual_participant_approval": self.challenge3.manual_participant_approval,  # noqa: C0301
                "is_active": False,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge3.forum_url,
                "is_docker_based": self.challenge3.is_docker_based,
                "is_static_dataset_code_upload": self.challenge3.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge3.slug,
                "max_docker_image_size": self.challenge3.max_docker_image_size,
                "cli_version": self.challenge3.cli_version,
                "remote_evaluation": self.challenge3.remote_evaluation,
                "allow_resuming_submissions": self.challenge3.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge3.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge3.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge3.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge3.workers,
                "created_at": f"{self.challenge3.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge3.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge3.cpu_only_jobs,
                "job_cpu_cores": self.challenge3.job_cpu_cores,
                "job_memory": self.challenge3.job_memory,
                "uses_ec2_worker": self.challenge3.uses_ec2_worker,
                "evaluation_module_error": self.challenge3.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge3.ec2_storage,
                "ephemeral_storage": self.challenge3.ephemeral_storage,
                "worker_image_url": self.challenge3.worker_image_url,
                "worker_instance_type": self.challenge3.worker_instance_type,
                "sqs_retention_period": self.challenge3.sqs_retention_period,
                "github_repository": self.challenge3.github_repository,
                "github_branch": self.challenge3.github_branch,
            }
        ]
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], expected)

    def test_get_present_challenges(self):
        self.url = reverse_lazy(
            "challenges:get_all_challenges",
            kwargs={
                "challenge_time": "PRESENT",
                "challenge_approved": "APPROVED",
                "challenge_published": "PUBLIC",
            },
        )

        expected = [
            {
                "id": self.challenge2.pk,
                "title": self.challenge2.title,
                "short_description": self.challenge2.short_description,
                "description": self.challenge2.description,
                "terms_and_conditions": self.challenge2.terms_and_conditions,
                "submission_guidelines": self.challenge2.submission_guidelines,
                "evaluation_details": self.challenge2.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge2.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge2.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge2.creator.pk,
                    "team_name": self.challenge2.creator.team_name,
                    "created_by": self.challenge2.creator.created_by.username,
                    "team_url": self.challenge2.creator.team_url,
                },
                "domain": self.challenge2.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge2.list_tags,
                "has_prize": self.challenge2.has_prize,
                "has_sponsors": self.challenge2.has_sponsors,
                "published": self.challenge2.published,
                "submission_time_limit": self.challenge2.submission_time_limit,
                "is_registration_open": self.challenge2.is_registration_open,
                "enable_forum": self.challenge2.enable_forum,
                "leaderboard_description": self.challenge2.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
                "manual_participant_approval": self.challenge2.manual_participant_approval,  # noqa: C0301
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge2.forum_url,
                "is_docker_based": self.challenge2.is_docker_based,
                "is_static_dataset_code_upload": self.challenge2.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge2.slug,
                "max_docker_image_size": self.challenge2.max_docker_image_size,
                "cli_version": self.challenge2.cli_version,
                "remote_evaluation": self.challenge2.remote_evaluation,
                "allow_resuming_submissions": self.challenge2.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge2.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge2.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge2.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge2.workers,
                "created_at": f"{self.challenge2.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge2.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge2.cpu_only_jobs,
                "job_cpu_cores": self.challenge2.job_cpu_cores,
                "job_memory": self.challenge2.job_memory,
                "uses_ec2_worker": self.challenge2.uses_ec2_worker,
                "evaluation_module_error": self.challenge2.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge2.ec2_storage,
                "ephemeral_storage": self.challenge2.ephemeral_storage,
                "worker_image_url": self.challenge2.worker_image_url,
                "worker_instance_type": self.challenge2.worker_instance_type,
                "sqs_retention_period": self.challenge2.sqs_retention_period,
                "github_repository": self.challenge2.github_repository,
                "github_branch": self.challenge2.github_branch,
            }
        ]
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], expected)

    def test_get_future_challenges(self):
        self.url = reverse_lazy(
            "challenges:get_all_challenges",
            kwargs={
                "challenge_time": "FUTURE",
                "challenge_approved": "APPROVED",
                "challenge_published": "PUBLIC",
            },
        )

        expected = [
            {
                "id": self.challenge4.pk,
                "title": self.challenge4.title,
                "short_description": self.challenge4.short_description,
                "description": self.challenge4.description,
                "terms_and_conditions": self.challenge4.terms_and_conditions,
                "submission_guidelines": self.challenge4.submission_guidelines,
                "evaluation_details": self.challenge4.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge4.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge4.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge4.creator.pk,
                    "team_name": self.challenge4.creator.team_name,
                    "created_by": self.challenge4.creator.created_by.username,
                    "team_url": self.challenge4.creator.team_url,
                },
                "domain": self.challenge4.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge4.list_tags,
                "has_prize": self.challenge4.has_prize,
                "has_sponsors": self.challenge4.has_sponsors,
                "published": self.challenge4.published,
                "submission_time_limit": self.challenge4.submission_time_limit,
                "is_registration_open": self.challenge4.is_registration_open,
                "enable_forum": self.challenge4.enable_forum,
                "leaderboard_description": self.challenge4.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge4.anonymous_leaderboard,
                "manual_participant_approval": self.challenge4.manual_participant_approval,  # noqa: C0301
                "is_active": False,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge4.forum_url,
                "is_docker_based": self.challenge4.is_docker_based,
                "is_static_dataset_code_upload": self.challenge4.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge4.slug,
                "max_docker_image_size": self.challenge4.max_docker_image_size,
                "cli_version": self.challenge4.cli_version,
                "remote_evaluation": self.challenge4.remote_evaluation,
                "allow_resuming_submissions": self.challenge4.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge4.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge4.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge4.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge4.workers,
                "created_at": f"{self.challenge4.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge4.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge4.cpu_only_jobs,
                "job_cpu_cores": self.challenge4.job_cpu_cores,
                "job_memory": self.challenge4.job_memory,
                "uses_ec2_worker": self.challenge4.uses_ec2_worker,
                "evaluation_module_error": self.challenge4.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge4.ec2_storage,
                "ephemeral_storage": self.challenge4.ephemeral_storage,
                "worker_image_url": self.challenge4.worker_image_url,
                "worker_instance_type": self.challenge4.worker_instance_type,
                "sqs_retention_period": self.challenge4.sqs_retention_period,
                "github_repository": self.challenge4.github_repository,
                "github_branch": self.challenge4.github_branch,
            }
        ]
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], expected)

    def test_get_all_challenges(self):
        self.url = reverse_lazy(
            "challenges:get_all_challenges",
            kwargs={
                "challenge_time": "ALL",
                "challenge_approved": "APPROVED",
                "challenge_published": "PUBLIC",
            },
        )

        expected = [
            {
                "id": self.challenge4.pk,
                "title": self.challenge4.title,
                "short_description": self.challenge4.short_description,
                "description": self.challenge4.description,
                "terms_and_conditions": self.challenge4.terms_and_conditions,
                "submission_guidelines": self.challenge4.submission_guidelines,
                "evaluation_details": self.challenge4.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge4.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge4.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge4.creator.pk,
                    "team_name": self.challenge4.creator.team_name,
                    "created_by": self.challenge4.creator.created_by.username,
                    "team_url": self.challenge4.creator.team_url,
                },
                "domain": self.challenge4.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge4.list_tags,
                "has_prize": self.challenge4.has_prize,
                "has_sponsors": self.challenge4.has_sponsors,
                "published": self.challenge4.published,
                "submission_time_limit": self.challenge4.submission_time_limit,
                "is_registration_open": self.challenge4.is_registration_open,
                "enable_forum": self.challenge4.enable_forum,
                "leaderboard_description": self.challenge4.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge4.anonymous_leaderboard,
                "manual_participant_approval": self.challenge4.manual_participant_approval,  # noqa: C0301
                "is_active": False,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge4.forum_url,
                "is_docker_based": self.challenge4.is_docker_based,
                "is_static_dataset_code_upload": self.challenge4.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge4.slug,
                "max_docker_image_size": self.challenge4.max_docker_image_size,
                "cli_version": self.challenge4.cli_version,
                "remote_evaluation": self.challenge4.remote_evaluation,
                "allow_resuming_submissions": self.challenge4.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge4.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge4.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge4.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge4.workers,
                "created_at": f"{self.challenge4.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge4.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge4.cpu_only_jobs,
                "job_cpu_cores": self.challenge4.job_cpu_cores,
                "job_memory": self.challenge4.job_memory,
                "uses_ec2_worker": self.challenge4.uses_ec2_worker,
                "evaluation_module_error": self.challenge4.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge4.ec2_storage,
                "ephemeral_storage": self.challenge4.ephemeral_storage,
                "worker_image_url": self.challenge4.worker_image_url,
                "worker_instance_type": self.challenge4.worker_instance_type,
                "sqs_retention_period": self.challenge4.sqs_retention_period,
                "github_repository": self.challenge4.github_repository,
                "github_branch": self.challenge4.github_branch,
            },
            {
                "id": self.challenge3.pk,
                "title": self.challenge3.title,
                "short_description": self.challenge3.short_description,
                "description": self.challenge3.description,
                "terms_and_conditions": self.challenge3.terms_and_conditions,
                "submission_guidelines": self.challenge3.submission_guidelines,
                "evaluation_details": self.challenge3.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge3.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge3.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge3.creator.pk,
                    "team_name": self.challenge3.creator.team_name,
                    "created_by": self.challenge3.creator.created_by.username,
                    "team_url": self.challenge3.creator.team_url,
                },
                "domain": self.challenge3.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge3.list_tags,
                "has_prize": self.challenge3.has_prize,
                "has_sponsors": self.challenge3.has_sponsors,
                "published": self.challenge3.published,
                "submission_time_limit": self.challenge3.submission_time_limit,
                "is_registration_open": self.challenge3.is_registration_open,
                "enable_forum": self.challenge3.enable_forum,
                "leaderboard_description": self.challenge3.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge3.anonymous_leaderboard,
                "manual_participant_approval": self.challenge3.manual_participant_approval,  # noqa: C0301
                "is_active": False,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge3.forum_url,
                "is_docker_based": self.challenge3.is_docker_based,
                "is_static_dataset_code_upload": self.challenge3.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge3.slug,
                "max_docker_image_size": self.challenge3.max_docker_image_size,
                "cli_version": self.challenge3.cli_version,
                "remote_evaluation": self.challenge3.remote_evaluation,
                "allow_resuming_submissions": self.challenge3.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge3.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge3.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge3.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge3.workers,
                "created_at": f"{self.challenge3.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge3.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge3.cpu_only_jobs,
                "job_cpu_cores": self.challenge3.job_cpu_cores,
                "job_memory": self.challenge3.job_memory,
                "uses_ec2_worker": self.challenge3.uses_ec2_worker,
                "evaluation_module_error": self.challenge3.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge3.ec2_storage,
                "ephemeral_storage": self.challenge3.ephemeral_storage,
                "worker_image_url": self.challenge3.worker_image_url,
                "worker_instance_type": self.challenge3.worker_instance_type,
                "sqs_retention_period": self.challenge3.sqs_retention_period,
                "github_repository": self.challenge3.github_repository,
                "github_branch": self.challenge3.github_branch,
            },
            {
                "id": self.challenge2.pk,
                "title": self.challenge2.title,
                "short_description": self.challenge2.short_description,
                "description": self.challenge2.description,
                "terms_and_conditions": self.challenge2.terms_and_conditions,
                "submission_guidelines": self.challenge2.submission_guidelines,
                "evaluation_details": self.challenge2.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge2.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge2.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge2.creator.pk,
                    "team_name": self.challenge2.creator.team_name,
                    "created_by": self.challenge2.creator.created_by.username,
                    "team_url": self.challenge2.creator.team_url,
                },
                "domain": self.challenge2.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge2.list_tags,
                "has_prize": self.challenge2.has_prize,
                "has_sponsors": self.challenge2.has_sponsors,
                "published": self.challenge2.published,
                "submission_time_limit": self.challenge2.submission_time_limit,
                "is_registration_open": self.challenge2.is_registration_open,
                "enable_forum": self.challenge2.enable_forum,
                "leaderboard_description": self.challenge2.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
                "manual_participant_approval": self.challenge2.manual_participant_approval,  # noqa: C0301
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge2.forum_url,
                "is_docker_based": self.challenge2.is_docker_based,
                "is_static_dataset_code_upload": self.challenge2.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge2.slug,
                "max_docker_image_size": self.challenge2.max_docker_image_size,
                "cli_version": self.challenge2.cli_version,
                "remote_evaluation": self.challenge2.remote_evaluation,
                "allow_resuming_submissions": self.challenge2.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge2.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge2.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge2.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge2.workers,
                "created_at": f"{self.challenge2.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge2.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge2.cpu_only_jobs,
                "job_cpu_cores": self.challenge2.job_cpu_cores,
                "job_memory": self.challenge2.job_memory,
                "uses_ec2_worker": self.challenge2.uses_ec2_worker,
                "evaluation_module_error": self.challenge2.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge2.ec2_storage,
                "ephemeral_storage": self.challenge2.ephemeral_storage,
                "worker_image_url": self.challenge2.worker_image_url,
                "worker_instance_type": self.challenge2.worker_instance_type,
                "sqs_retention_period": self.challenge2.sqs_retention_period,
                "github_repository": self.challenge2.github_repository,
                "github_branch": self.challenge2.github_branch,
            },
        ]
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], expected)

    def test_incorrent_url_pattern_challenges(self):
        self.url = reverse_lazy(
            "challenges:get_all_challenges",
            kwargs={
                "challenge_time": "INCORRECT",
                "challenge_approved": "APPROVED",
                "challenge_published": "PUBLIC",
            },
        )
        expected = {"error": "Wrong url pattern!"}
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.data, expected)


class GetFeaturedChallengesTest(BaseAPITestClass):
    url = reverse_lazy("challenges:get_featured_challenges")

    def setUp(self):
        super().setUp()
        self.url = reverse_lazy("challenges:get_featured_challenges")

        # Not a featured challenge
        self.challenge2 = Challenge.objects.create(
            title="Test Challenge 2",
            short_description="Short description for test challenge 2",
            description="Description for test challenge 2",
            terms_and_conditions="Terms and conditions for test challenge 2",
            submission_guidelines="Submission guidelines for test challenge 2",
            creator=self.challenge_host_team,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            approved_by_admin=True,
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        # Featured challenge
        self.challenge3 = Challenge.objects.create(
            title="Test Challenge 3",
            short_description="Short description for test challenge 3",
            description="Description for test challenge 3",
            terms_and_conditions="Terms and conditions for test challenge 3",
            submission_guidelines="Submission guidelines for test challenge 3",
            creator=self.challenge_host_team,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            approved_by_admin=True,
            leaderboard_description=None,
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() - timedelta(days=1),
            featured=True,
            github_repository="challenge3/github_repo",
        )

    def test_get_featured_challenges(self):
        expected = [
            {
                "id": self.challenge3.pk,
                "title": self.challenge3.title,
                "short_description": self.challenge3.short_description,
                "description": self.challenge3.description,
                "terms_and_conditions": self.challenge3.terms_and_conditions,
                "submission_guidelines": self.challenge3.submission_guidelines,
                "evaluation_details": self.challenge3.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge3.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge3.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge3.creator.pk,
                    "team_name": self.challenge3.creator.team_name,
                    "created_by": self.challenge3.creator.created_by.username,
                    "team_url": self.challenge3.creator.team_url,
                },
                "domain": self.challenge3.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge3.list_tags,
                "has_prize": self.challenge3.has_prize,
                "has_sponsors": self.challenge3.has_sponsors,
                "published": self.challenge3.published,
                "submission_time_limit": self.challenge3.submission_time_limit,
                "is_registration_open": self.challenge3.is_registration_open,
                "enable_forum": self.challenge3.enable_forum,
                "leaderboard_description": self.challenge3.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge3.anonymous_leaderboard,
                "manual_participant_approval": self.challenge3.manual_participant_approval,  # noqa: C0301
                "is_active": False,
                "allowed_email_domains": self.challenge3.allowed_email_domains,
                "blocked_email_domains": self.challenge3.blocked_email_domains,
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge3.forum_url,
                "is_docker_based": self.challenge3.is_docker_based,
                "is_static_dataset_code_upload": self.challenge3.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge3.slug,
                "max_docker_image_size": self.challenge3.max_docker_image_size,
                "cli_version": self.challenge3.cli_version,
                "remote_evaluation": self.challenge3.remote_evaluation,
                "allow_resuming_submissions": self.challenge3.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge3.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge3.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge3.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge3.workers,
                "created_at": f"{self.challenge3.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge3.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge3.cpu_only_jobs,
                "job_cpu_cores": self.challenge3.job_cpu_cores,
                "job_memory": self.challenge3.job_memory,
                "uses_ec2_worker": self.challenge3.uses_ec2_worker,
                "evaluation_module_error": self.challenge3.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge3.ec2_storage,
                "ephemeral_storage": self.challenge3.ephemeral_storage,
                "worker_image_url": self.challenge3.worker_image_url,
                "worker_instance_type": self.challenge3.worker_instance_type,
                "sqs_retention_period": self.challenge3.sqs_retention_period,
                "github_repository": self.challenge3.github_repository,
                "github_branch": self.challenge3.github_branch,
            }
        ]
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], expected)


class GetChallengeByPk(BaseAPITestClass):
    def setUp(self):
        super().setUp()

        self.user1 = User.objects.create(
            username="user1",
            email="user1@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@test.com",
            primary=True,
            verified=True,
        )

        self.challenge3 = Challenge.objects.create(
            title="Test Challenge 3",
            short_description="Short description for test challenge 3",
            description="Description for test challenge 3",
            terms_and_conditions="Terms and conditions for test challenge 3",
            submission_guidelines="Submission guidelines for test challenge 3",
            creator=self.challenge_host_team,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=False,
            is_registration_open=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
            github_repository="challenge3/github_repo",
        )

        self.challenge4 = Challenge.objects.create(
            title="Test Challenge 4",
            short_description="Short description for test challenge 4",
            description="Description for test challenge 4",
            terms_and_conditions="Terms and conditions for test challenge 4",
            submission_guidelines="Submission guidelines for test challenge 4",
            creator=self.challenge_host_team,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            leaderboard_description="Curabitur nec placerat libero.",
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            is_disabled=False,
            approved_by_admin=True,
            github_repository="challenge4/github_repo",
        )

        self.challenge5 = Challenge.objects.create(
            title="Test Challenge 5",
            short_description="Short description for test challenge 5",
            description="Description for test challenge 5",
            terms_and_conditions="Terms and conditions for test challenge 5",
            submission_guidelines="Submission guidelines for test challenge 5",
            creator=self.challenge_host_team,
            published=False,
            is_registration_open=True,
            enable_forum=True,
            leaderboard_description=None,
            anonymous_leaderboard=False,
            manual_participant_approval=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            is_disabled=True,
        )

    def test_get_challenge_by_pk_when_challenge_does_not_exists(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_challenge_by_pk",
                kwargs={"pk": self.challenge3.pk + 10},
            )
        )
        expected = {"error": "Challenge does not exist!"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_challenge_by_pk_when_user_is_challenge_host(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_challenge_by_pk",
                kwargs={"pk": self.challenge3.pk},
            )
        )
        expected = {
            "id": self.challenge3.pk,
            "title": self.challenge3.title,
            "short_description": self.challenge3.short_description,
            "description": self.challenge3.description,
            "terms_and_conditions": self.challenge3.terms_and_conditions,
            "submission_guidelines": self.challenge3.submission_guidelines,
            "evaluation_details": self.challenge3.evaluation_details,
            "image": None,
            "start_date": f"{self.challenge3.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge3.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "creator": {
                "id": self.challenge3.creator.pk,
                "team_name": self.challenge3.creator.team_name,
                "created_by": self.challenge3.creator.created_by.username,
                "team_url": self.challenge3.creator.team_url,
            },
            "domain": self.challenge3.domain,
            "domain_name": "Computer Vision",
            "list_tags": self.challenge3.list_tags,
            "has_prize": self.challenge3.has_prize,
            "has_sponsors": self.challenge3.has_sponsors,
            "published": self.challenge3.published,
            "submission_time_limit": self.challenge3.submission_time_limit,
            "is_registration_open": self.challenge3.is_registration_open,
            "enable_forum": self.challenge3.enable_forum,
            "leaderboard_description": self.challenge3.leaderboard_description,
            "anonymous_leaderboard": self.challenge3.anonymous_leaderboard,
            "manual_participant_approval": self.challenge3.manual_participant_approval,  # noqa: C0301
            "is_active": True,
            "allowed_email_domains": [],
            "blocked_email_domains": [],
            "banned_email_ids": [],
            "approved_by_admin": self.challenge3.approved_by_admin,
            "forum_url": self.challenge3.forum_url,
            "is_docker_based": self.challenge3.is_docker_based,
            "is_static_dataset_code_upload": self.challenge3.is_static_dataset_code_upload,  # noqa: C0301
            "slug": self.challenge3.slug,
            "max_docker_image_size": self.challenge3.max_docker_image_size,
            "cli_version": self.challenge3.cli_version,
            "remote_evaluation": self.challenge3.remote_evaluation,
            "allow_resuming_submissions": self.challenge3.allow_resuming_submissions,  # noqa: C0301
            "allow_host_cancel_submissions": self.challenge3.allow_host_cancel_submissions,  # noqa: C0301
            "allow_cancel_running_submissions": self.challenge3.allow_cancel_running_submissions,  # noqa: C0301
            "allow_participants_resubmissions": self.challenge3.allow_participants_resubmissions,  # noqa: C0301
            "workers": self.challenge3.workers,
            "created_at": f"{self.challenge3.created_at.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "queue": self.challenge3.queue,
            "worker_cpu_cores": 512,
            "worker_memory": 1024,
            "cpu_only_jobs": self.challenge3.cpu_only_jobs,
            "job_cpu_cores": self.challenge3.job_cpu_cores,
            "job_memory": self.challenge3.job_memory,
            "uses_ec2_worker": self.challenge3.uses_ec2_worker,
            "evaluation_module_error": self.challenge3.evaluation_module_error,
            "ec2_storage": self.challenge3.ec2_storage,
            "ephemeral_storage": self.challenge3.ephemeral_storage,
            "worker_image_url": self.challenge3.worker_image_url,
            "worker_instance_type": self.challenge3.worker_instance_type,
            "sqs_retention_period": self.challenge3.sqs_retention_period,
            "github_repository": self.challenge3.github_repository,
            "github_branch": self.challenge3.github_branch,
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_by_pk_when_user_is_not_challenge_host(self):
        """
        This is a corner case in which a user is not a challenge host
        but tries but access the challenge created by challenge host.
        """
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_challenge_by_pk",
                kwargs={"pk": self.challenge3.pk},
            )
        )
        self.client.force_authenticate(user=self.user1)
        expected = {"error": "Challenge does not exist!"}

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_challenge_by_pk_when_user_is_participant(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_challenge_by_pk",
                kwargs={"pk": self.challenge4.pk},
            )
        )
        expected = {
            "id": self.challenge4.pk,
            "title": self.challenge4.title,
            "short_description": self.challenge4.short_description,
            "description": self.challenge4.description,
            "terms_and_conditions": self.challenge4.terms_and_conditions,
            "submission_guidelines": self.challenge4.submission_guidelines,
            "evaluation_details": self.challenge4.evaluation_details,
            "image": None,
            "start_date": f"{self.challenge4.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge4.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "creator": {
                "id": self.challenge4.creator.pk,
                "team_name": self.challenge4.creator.team_name,
                "created_by": self.challenge4.creator.created_by.username,
                "team_url": self.challenge4.creator.team_url,
            },
            "domain": self.challenge4.domain,
            "domain_name": "Computer Vision",
            "list_tags": self.challenge4.list_tags,
            "has_prize": self.challenge4.has_prize,
            "has_sponsors": self.challenge4.has_sponsors,
            "published": self.challenge4.published,
            "submission_time_limit": self.challenge4.submission_time_limit,
            "is_registration_open": self.challenge4.is_registration_open,
            "enable_forum": self.challenge4.enable_forum,
            "leaderboard_description": self.challenge4.leaderboard_description,
            "anonymous_leaderboard": self.challenge4.anonymous_leaderboard,
            "manual_participant_approval": self.challenge4.manual_participant_approval,  # noqa: C0301
            "is_active": True,
            "allowed_email_domains": [],
            "blocked_email_domains": [],
            "banned_email_ids": [],
            "approved_by_admin": self.challenge4.approved_by_admin,
            "forum_url": self.challenge4.forum_url,
            "is_docker_based": self.challenge4.is_docker_based,
            "is_static_dataset_code_upload": self.challenge4.is_static_dataset_code_upload,  # noqa: C0301
            "slug": self.challenge4.slug,
            "max_docker_image_size": self.challenge4.max_docker_image_size,
            "cli_version": self.challenge4.cli_version,
            "remote_evaluation": self.challenge4.remote_evaluation,
            "allow_resuming_submissions": self.challenge4.allow_resuming_submissions,  # noqa: C0301
            "allow_host_cancel_submissions": self.challenge4.allow_host_cancel_submissions,  # noqa: C0301
            "allow_cancel_running_submissions": self.challenge4.allow_cancel_running_submissions,  # noqa: C0301
            "allow_participants_resubmissions": self.challenge4.allow_participants_resubmissions,  # noqa: C0301
            "workers": self.challenge4.workers,
            "created_at": f"{self.challenge4.created_at.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "queue": self.challenge4.queue,
            "worker_cpu_cores": 512,
            "worker_memory": 1024,
            "cpu_only_jobs": self.challenge4.cpu_only_jobs,
            "job_cpu_cores": self.challenge4.job_cpu_cores,
            "job_memory": self.challenge4.job_memory,
            "uses_ec2_worker": self.challenge4.uses_ec2_worker,
            "evaluation_module_error": self.challenge4.evaluation_module_error,
            "ec2_storage": self.challenge4.ec2_storage,
            "ephemeral_storage": self.challenge4.ephemeral_storage,
            "worker_image_url": self.challenge4.worker_image_url,
            "worker_instance_type": self.challenge4.worker_instance_type,
            "sqs_retention_period": self.challenge4.sqs_retention_period,
            "github_repository": self.challenge4.github_repository,
            "github_branch": self.challenge4.github_branch,
        }

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_by_pk_when_challenge_is_disabled(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_challenge_by_pk",
                kwargs={"pk": self.challenge5.pk},
            )
        )
        expected = {"error": "Sorry, the challenge was removed!"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class GetChallengeBasedOnTeams(BaseAPITestClass):
    def setUp(self):
        super().setUp()

        self.challenge_host_team2 = ChallengeHostTeam.objects.create(
            team_name="Some Test Challenge Host Team", created_by=self.user
        )

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team2,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description for test challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            leaderboard_description=None,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=True,
            github_repository="challenge/github_repo",
        )

        self.challenge2 = Challenge.objects.create(
            title="Some Test Challenge",
            short_description="Short description for some test challenge",
            description="Description for some test challenge",
            terms_and_conditions="Terms and conditions for some test challenge",  # noqa: C0301
            submission_guidelines="Submission guidelines for some test challenge",  # noqa: C0301
            creator=self.challenge_host_team2,
            domain="CV",
            list_tags=["Paper", "Dataset", "Environment", "Workshop"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=True,
            github_repository="challenge2/github_repo",
        )

        self.participant_team2 = ParticipantTeam.objects.create(
            team_name="Some Participant Team", created_by=self.user
        )

        self.participant2 = Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team2,
        )

        self.challenge2.participant_teams.add(self.participant_team2)

    def test_get_challenge_when_host_team_is_given(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy("challenges:get_challenges_based_on_teams")
        )

        expected = [
            {
                "id": self.challenge2.pk,
                "title": self.challenge2.title,
                "short_description": self.challenge2.short_description,
                "description": self.challenge2.description,
                "terms_and_conditions": self.challenge2.terms_and_conditions,
                "submission_guidelines": self.challenge2.submission_guidelines,
                "evaluation_details": self.challenge2.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge2.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge2.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge2.creator.pk,
                    "team_name": self.challenge2.creator.team_name,
                    "created_by": self.challenge2.creator.created_by.username,
                    "team_url": self.challenge2.creator.team_url,
                },
                "domain": self.challenge2.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge2.list_tags,
                "has_prize": self.challenge2.has_prize,
                "has_sponsors": self.challenge2.has_sponsors,
                "published": self.challenge2.published,
                "submission_time_limit": self.challenge2.submission_time_limit,
                "is_registration_open": self.challenge2.is_registration_open,
                "enable_forum": self.challenge2.enable_forum,
                "leaderboard_description": self.challenge2.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
                "manual_participant_approval": self.challenge2.manual_participant_approval,  # noqa: C0301
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge2.forum_url,
                "is_docker_based": self.challenge2.is_docker_based,
                "is_static_dataset_code_upload": self.challenge2.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge2.slug,
                "max_docker_image_size": self.challenge2.max_docker_image_size,
                "cli_version": self.challenge2.cli_version,
                "remote_evaluation": self.challenge2.remote_evaluation,
                "allow_resuming_submissions": self.challenge2.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge2.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge2.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge2.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge2.workers,
                "created_at": f"{self.challenge2.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge2.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge2.cpu_only_jobs,
                "job_cpu_cores": self.challenge2.job_cpu_cores,
                "job_memory": self.challenge2.job_memory,
                "uses_ec2_worker": self.challenge2.uses_ec2_worker,
                "evaluation_module_error": self.challenge2.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge2.ec2_storage,
                "ephemeral_storage": self.challenge2.ephemeral_storage,
                "worker_image_url": self.challenge2.worker_image_url,
                "worker_instance_type": self.challenge2.worker_instance_type,
                "sqs_retention_period": self.challenge2.sqs_retention_period,
                "github_repository": self.challenge2.github_repository,
                "github_branch": self.challenge2.github_branch,
            }
        ]

        response = self.client.get(
            self.url, {"host_team": self.challenge_host_team2.pk}
        )
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_participant_team_is_given(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy("challenges:get_challenges_based_on_teams")
        )

        expected = [
            {
                "id": self.challenge2.pk,
                "title": self.challenge2.title,
                "short_description": self.challenge2.short_description,
                "description": self.challenge2.description,
                "terms_and_conditions": self.challenge2.terms_and_conditions,
                "submission_guidelines": self.challenge2.submission_guidelines,
                "evaluation_details": self.challenge2.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge2.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge2.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge2.creator.pk,
                    "team_name": self.challenge2.creator.team_name,
                    "created_by": self.challenge2.creator.created_by.username,
                    "team_url": self.challenge2.creator.team_url,
                },
                "domain": self.challenge2.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge2.list_tags,
                "has_prize": self.challenge2.has_prize,
                "has_sponsors": self.challenge2.has_sponsors,
                "published": self.challenge2.published,
                "submission_time_limit": self.challenge2.submission_time_limit,
                "is_registration_open": self.challenge2.is_registration_open,
                "enable_forum": self.challenge2.enable_forum,
                "leaderboard_description": self.challenge2.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
                "manual_participant_approval": self.challenge2.manual_participant_approval,  # noqa: C0301
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge2.forum_url,
                "is_docker_based": self.challenge2.is_docker_based,
                "is_static_dataset_code_upload": self.challenge2.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge2.slug,
                "max_docker_image_size": self.challenge2.max_docker_image_size,
                "cli_version": self.challenge2.cli_version,
                "remote_evaluation": self.challenge2.remote_evaluation,
                "allow_resuming_submissions": self.challenge2.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge2.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge2.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge2.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge2.workers,
                "created_at": f"{self.challenge2.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge2.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge2.cpu_only_jobs,
                "job_cpu_cores": self.challenge2.job_cpu_cores,
                "job_memory": self.challenge2.job_memory,
                "uses_ec2_worker": self.challenge2.uses_ec2_worker,
                "evaluation_module_error": self.challenge2.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge2.ec2_storage,
                "ephemeral_storage": self.challenge2.ephemeral_storage,
                "worker_image_url": self.challenge2.worker_image_url,
                "worker_instance_type": self.challenge2.worker_instance_type,
                "sqs_retention_period": self.challenge2.sqs_retention_period,
                "github_repository": self.challenge2.github_repository,
                "github_branch": self.challenge2.github_branch,
            }
        ]

        response = self.client.get(
            self.url, {"participant_team": self.participant_team2.pk}
        )
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_mode_is_participant(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy("challenges:get_challenges_based_on_teams")
        )

        expected = [
            {
                "id": self.challenge2.pk,
                "title": self.challenge2.title,
                "short_description": self.challenge2.short_description,
                "description": self.challenge2.description,
                "terms_and_conditions": self.challenge2.terms_and_conditions,
                "submission_guidelines": self.challenge2.submission_guidelines,
                "evaluation_details": self.challenge2.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge2.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge2.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge2.creator.pk,
                    "team_name": self.challenge2.creator.team_name,
                    "created_by": self.challenge2.creator.created_by.username,
                    "team_url": self.challenge2.creator.team_url,
                },
                "domain": self.challenge2.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge2.list_tags,
                "has_prize": self.challenge2.has_prize,
                "has_sponsors": self.challenge2.has_sponsors,
                "published": self.challenge2.published,
                "submission_time_limit": self.challenge2.submission_time_limit,
                "is_registration_open": self.challenge2.is_registration_open,
                "enable_forum": self.challenge2.enable_forum,
                "leaderboard_description": self.challenge2.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
                "manual_participant_approval": self.challenge2.manual_participant_approval,  # noqa: C0301
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge2.forum_url,
                "is_docker_based": self.challenge2.is_docker_based,
                "is_static_dataset_code_upload": self.challenge2.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge2.slug,
                "max_docker_image_size": self.challenge2.max_docker_image_size,
                "cli_version": self.challenge2.cli_version,
                "remote_evaluation": self.challenge2.remote_evaluation,
                "allow_resuming_submissions": self.challenge2.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge2.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge2.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge2.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge2.workers,
                "created_at": f"{self.challenge2.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge2.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge2.cpu_only_jobs,
                "job_cpu_cores": self.challenge2.job_cpu_cores,
                "job_memory": self.challenge2.job_memory,
                "uses_ec2_worker": self.challenge2.uses_ec2_worker,
                "evaluation_module_error": self.challenge2.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge2.ec2_storage,
                "ephemeral_storage": self.challenge2.ephemeral_storage,
                "worker_image_url": self.challenge2.worker_image_url,
                "worker_instance_type": self.challenge2.worker_instance_type,
                "sqs_retention_period": self.challenge2.sqs_retention_period,
                "github_repository": self.challenge2.github_repository,
                "github_branch": self.challenge2.github_branch,
            }
        ]

        response = self.client.get(self.url, {"mode": "participant"})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_mode_is_host(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy("challenges:get_challenges_based_on_teams")
        )

        expected = [
            {
                "id": self.challenge.pk,
                "title": self.challenge.title,
                "short_description": self.challenge.short_description,
                "description": self.challenge.description,
                "terms_and_conditions": self.challenge.terms_and_conditions,
                "submission_guidelines": self.challenge.submission_guidelines,
                "evaluation_details": self.challenge.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge.creator.pk,
                    "team_name": self.challenge.creator.team_name,
                    "created_by": self.challenge.creator.created_by.username,
                    "team_url": self.challenge.creator.team_url,
                },
                "domain": self.challenge.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge.list_tags,
                "has_prize": self.challenge.has_prize,
                "has_sponsors": self.challenge.has_sponsors,
                "published": self.challenge.published,
                "submission_time_limit": self.challenge.submission_time_limit,
                "is_registration_open": self.challenge.is_registration_open,
                "enable_forum": self.challenge.enable_forum,
                "leaderboard_description": self.challenge.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
                "manual_participant_approval": self.challenge.manual_participant_approval,  # noqa: C0301
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge.forum_url,
                "is_docker_based": self.challenge.is_docker_based,
                "is_static_dataset_code_upload": self.challenge.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge.slug,
                "max_docker_image_size": self.challenge.max_docker_image_size,
                "cli_version": self.challenge.cli_version,
                "remote_evaluation": self.challenge.remote_evaluation,
                "allow_resuming_submissions": self.challenge.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge.workers,
                "created_at": f"{self.challenge.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge.cpu_only_jobs,
                "job_cpu_cores": self.challenge.job_cpu_cores,
                "job_memory": self.challenge.job_memory,
                "uses_ec2_worker": self.challenge.uses_ec2_worker,
                "evaluation_module_error": self.challenge.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge.ec2_storage,
                "ephemeral_storage": self.challenge.ephemeral_storage,
                "worker_image_url": self.challenge.worker_image_url,
                "worker_instance_type": self.challenge.worker_instance_type,
                "sqs_retention_period": self.challenge.sqs_retention_period,
                "github_repository": self.challenge.github_repository,
                "github_branch": self.challenge.github_branch,
            },
            {
                "id": self.challenge2.pk,
                "title": self.challenge2.title,
                "short_description": self.challenge2.short_description,
                "description": self.challenge2.description,
                "terms_and_conditions": self.challenge2.terms_and_conditions,
                "submission_guidelines": self.challenge2.submission_guidelines,
                "evaluation_details": self.challenge2.evaluation_details,
                "image": None,
                "start_date": f"{self.challenge2.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge2.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "creator": {
                    "id": self.challenge2.creator.pk,
                    "team_name": self.challenge2.creator.team_name,
                    "created_by": self.challenge2.creator.created_by.username,
                    "team_url": self.challenge2.creator.team_url,
                },
                "domain": self.challenge2.domain,
                "domain_name": "Computer Vision",
                "list_tags": self.challenge2.list_tags,
                "has_prize": self.challenge2.has_prize,
                "has_sponsors": self.challenge2.has_sponsors,
                "published": self.challenge2.published,
                "submission_time_limit": self.challenge2.submission_time_limit,
                "is_registration_open": self.challenge2.is_registration_open,
                "enable_forum": self.challenge2.enable_forum,
                "leaderboard_description": self.challenge2.leaderboard_description,  # noqa: C0301
                "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
                "manual_participant_approval": self.challenge2.manual_participant_approval,  # noqa: C0301
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "banned_email_ids": [],
                "approved_by_admin": True,
                "forum_url": self.challenge2.forum_url,
                "is_docker_based": self.challenge2.is_docker_based,
                "is_static_dataset_code_upload": self.challenge2.is_static_dataset_code_upload,  # noqa: C0301
                "slug": self.challenge2.slug,
                "max_docker_image_size": self.challenge2.max_docker_image_size,
                "cli_version": self.challenge2.cli_version,
                "remote_evaluation": self.challenge2.remote_evaluation,
                "allow_resuming_submissions": self.challenge2.allow_resuming_submissions,  # noqa: C0301
                "allow_host_cancel_submissions": self.challenge2.allow_host_cancel_submissions,  # noqa: C0301
                "allow_cancel_running_submissions": self.challenge2.allow_cancel_running_submissions,  # noqa: C0301
                "allow_participants_resubmissions": self.challenge2.allow_participants_resubmissions,  # noqa: C0301
                "workers": self.challenge2.workers,
                "created_at": f"{self.challenge2.created_at.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "queue": self.challenge2.queue,
                "worker_cpu_cores": 512,
                "worker_memory": 1024,
                "cpu_only_jobs": self.challenge2.cpu_only_jobs,
                "job_cpu_cores": self.challenge2.job_cpu_cores,
                "job_memory": self.challenge2.job_memory,
                "uses_ec2_worker": self.challenge2.uses_ec2_worker,
                "evaluation_module_error": self.challenge2.evaluation_module_error,  # noqa: C0301
                "ec2_storage": self.challenge2.ec2_storage,
                "ephemeral_storage": self.challenge2.ephemeral_storage,
                "worker_image_url": self.challenge2.worker_image_url,
                "worker_instance_type": self.challenge2.worker_instance_type,
                "sqs_retention_period": self.challenge2.sqs_retention_period,
                "github_repository": self.challenge2.github_repository,
                "github_branch": self.challenge2.github_branch,
            },
        ]

        response = self.client.get(self.url, {"mode": "host"})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_with_incorrect_url_pattern(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy("challenges:get_challenges_based_on_teams")
        )

        expected = {"error": "Invalid url pattern!"}
        response = self.client.get(
            self.url, {"invalid_q_param": "invalidvalue"}
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_challenge_with_incorrect_url_pattern_with_all_values(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy("challenges:get_challenges_based_on_teams")
        )

        expected = {"error": "Invalid url pattern!"}
        response = self.client.get(
            self.url,
            {
                "host_team": self.challenge_host_team2.pk,
                "participant_team": self.participant_team2.pk,
                "mode": "participant",
            },
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class ChallengePrizesTest(BaseAPITestClass):

    def setUp(self):
        super().setUp()
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description for test challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            published=True,
            is_registration_open=True,
            enable_forum=True,
            approved_by_admin=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

    def test_challenge_has_prize_false(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_challenge_by_pk",
                kwargs={"pk": self.challenge.pk},
            )
        )

        self.challenge.has_prize = False
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_prize"])

    def test_challenge_has_prize_true(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_prizes_by_challenge",
                kwargs={"challenge_pk": self.challenge.pk},
            )
        )

        self.challenge.has_prize = True
        self.challenge.save()
        prize = ChallengePrize.objects.create(
            challenge=self.challenge,
            amount="100USD",
            rank=1,
        )
        prize1 = ChallengePrize.objects.create(
            challenge=self.challenge,
            amount="500USD",
            rank=2,
        )
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["challenge"], prize.challenge.pk)
        self.assertEqual(response.data[0]["amount"], prize.amount)
        self.assertEqual(response.data[0]["rank"], prize.rank)
        self.assertEqual(response.data[1]["challenge"], prize1.challenge.pk)
        self.assertEqual(response.data[1]["amount"], prize1.amount)
        self.assertEqual(response.data[1]["rank"], prize1.rank)


class ChallengeSponsorTest(BaseAPITestClass):

    def setUp(self):
        super().setUp()
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description for test challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            published=True,
            is_registration_open=True,
            enable_forum=True,
            approved_by_admin=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

    def test_challenge_has_sponsor_false(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_challenge_by_pk",
                kwargs={"pk": self.challenge.pk},
            )
        )

        self.challenge.has_sponsors = False
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["has_sponsors"])

    def test_challenge_has_sponsor_true(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_sponsors_by_challenge",
                kwargs={"challenge_pk": self.challenge.pk},
            )
        )

        self.challenge.has_sponsors = True
        self.challenge.save()
        sponsor = ChallengeSponsor.objects.create(
            challenge=self.challenge,
            name="Sponsor 1",
            website="https://evalai.com",
        )
        response = self.client.get(self.url, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]["challenge"], sponsor.challenge.pk)
        self.assertEqual(response.data[0]["name"], sponsor.name)
        self.assertEqual(response.data[0]["website"], sponsor.website)


class BaseChallengePhaseClass(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                max_submissions_per_day=100000,
                max_submissions_per_month=100000,
                max_submissions=100000,
                codename="Phase Code Name",
                is_restricted_to_select_one_submission=True,
                is_partial_submission_evaluation_enabled=False,
            )
            self.challenge_phase.slug = (
                f"{self.challenge.title.split(' ')[0].lower()}-"
                f"{self.challenge_phase.codename.replace(' ', '-').lower()}-"
                f"{self.challenge.pk}"
            )[:198]
            self.challenge_phase.save()

            self.private_challenge_phase = ChallengePhase.objects.create(
                name="Private Challenge Phase",
                description="Description for Private Challenge Phase",
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
                max_submissions_per_month=100000,
                max_submissions=100000,
                codename="Private Phase Code Name",
                is_restricted_to_select_one_submission=True,
                is_partial_submission_evaluation_enabled=False,
            )
            self.private_challenge_phase.slug = (
                f"{self.challenge.title.split(' ')[0].lower()}-"
                f"{self.private_challenge_phase.codename.replace(' ', '-').lower()}-"
                f"{self.challenge.pk}"
            )[:198]
            self.private_challenge_phase.save()

    def tearDown(self):  # pylint: disable=no-self-use
        shutil.rmtree("/tmp/evalai")


class GetChallengePhaseTest(BaseChallengePhaseClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_list",
            kwargs={"challenge_pk": self.challenge.pk},
        )

    def test_get_challenge_phase(self):
        expected = [
            {
                "id": self.challenge_phase.id,
                "name": self.challenge_phase.name,
                "description": self.challenge_phase.description,
                "leaderboard_public": self.challenge_phase.leaderboard_public,
                "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "challenge": self.challenge_phase.challenge.pk,
                "is_public": self.challenge_phase.is_public,
                "is_active": True,
                "codename": "Phase Code Name",
                "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,  # noqa: C0301
                "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
                "max_submissions": self.challenge_phase.max_submissions,
                "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
                "slug": self.challenge_phase.slug,
                "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
                "submission_meta_attributes": None,
                "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
                "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,  # noqa: C0301
                "allowed_email_ids": self.challenge_phase.allowed_email_ids,
                "is_submission_public": self.challenge_phase.is_submission_public,  # noqa: C0301
                "disable_logs": self.challenge_phase.disable_logs,
            },
            {
                "id": self.private_challenge_phase.id,
                "name": self.private_challenge_phase.name,
                "description": self.private_challenge_phase.description,
                "leaderboard_public": self.private_challenge_phase.leaderboard_public,  # noqa: C0301
                "start_date": f"{self.private_challenge_phase.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.private_challenge_phase.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "challenge": self.private_challenge_phase.challenge.pk,
                "is_public": self.private_challenge_phase.is_public,
                "is_active": True,
                "codename": self.private_challenge_phase.codename,
                "max_submissions_per_day": self.private_challenge_phase.max_submissions_per_day,  # noqa: C0301
                "max_submissions_per_month": self.private_challenge_phase.max_submissions_per_month,  # noqa: C0301
                "max_submissions": self.private_challenge_phase.max_submissions,  # noqa: C0301
                "max_concurrent_submissions_allowed": self.private_challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
                "slug": self.private_challenge_phase.slug,
                "is_restricted_to_select_one_submission": self.private_challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
                "submission_meta_attributes": None,
                "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
                "default_submission_meta_attributes": self.private_challenge_phase.default_submission_meta_attributes,  # noqa: C0301
                "allowed_email_ids": self.challenge_phase.allowed_email_ids,
                "is_submission_public": self.challenge_phase.is_submission_public,  # noqa: C0301
                "disable_logs": self.challenge_phase.disable_logs,
            },
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_phase_when_user_is_not_authenticated(self):
        expected = [
            {
                "id": self.challenge_phase.id,
                "name": self.challenge_phase.name,
                "description": self.challenge_phase.description,
                "leaderboard_public": self.challenge_phase.leaderboard_public,
                "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "challenge": self.challenge_phase.challenge.pk,
                "is_public": self.challenge_phase.is_public,
                "is_active": True,
                "codename": "Phase Code Name",
                "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,  # noqa: C0301
                "max_submissions": self.challenge_phase.max_submissions,
                "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
                "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
                "slug": self.challenge_phase.slug,
                "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
                "submission_meta_attributes": None,
                "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
                "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,  # noqa: C0301
                "allowed_email_ids": self.challenge_phase.allowed_email_ids,
                "is_submission_public": self.challenge_phase.is_submission_public,  # noqa: C0301
                "disable_logs": self.challenge_phase.disable_logs,
            }
        ]
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_for_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_list",
            kwargs={"challenge_pk": self.challenge.pk + 1},
        )
        expected = {"error": "Challenge does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_challenge_phase_when_user_is_host(self):
        expected = [
            {
                "id": self.challenge_phase.id,
                "name": self.challenge_phase.name,
                "description": self.challenge_phase.description,
                "leaderboard_public": self.challenge_phase.leaderboard_public,
                "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "challenge": self.challenge_phase.challenge.pk,
                "is_public": self.challenge_phase.is_public,
                "is_active": True,
                "codename": "Phase Code Name",
                "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,  # noqa: C0301
                "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
                "max_submissions": self.challenge_phase.max_submissions,
                "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
                "slug": self.challenge_phase.slug,
                "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
                "submission_meta_attributes": None,
                "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
                "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,  # noqa: C0301
                "allowed_email_ids": self.challenge_phase.allowed_email_ids,
                "is_submission_public": self.challenge_phase.is_submission_public,  # noqa: C0301
                "disable_logs": self.challenge_phase.disable_logs,
            },
            {
                "id": self.private_challenge_phase.id,
                "name": self.private_challenge_phase.name,
                "description": self.private_challenge_phase.description,
                "leaderboard_public": self.private_challenge_phase.leaderboard_public,  # noqa: C0301
                "start_date": f"{self.private_challenge_phase.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.private_challenge_phase.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "challenge": self.private_challenge_phase.challenge.pk,
                "is_public": self.private_challenge_phase.is_public,
                "is_active": True,
                "codename": self.private_challenge_phase.codename,
                "max_submissions_per_day": self.private_challenge_phase.max_submissions_per_day,  # noqa: C0301
                "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
                "max_submissions": self.private_challenge_phase.max_submissions,  # noqa: C0301
                "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
                "slug": self.private_challenge_phase.slug,
                "is_restricted_to_select_one_submission": self.private_challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
                "submission_meta_attributes": None,
                "allowed_submission_file_types": self.private_challenge_phase.allowed_submission_file_types,  # noqa: C0301
                "is_partial_submission_evaluation_enabled": self.private_challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
                "default_submission_meta_attributes": self.private_challenge_phase.default_submission_meta_attributes,  # noqa: C0301
                "allowed_email_ids": self.private_challenge_phase.allowed_email_ids,  # noqa: C0301
                "is_submission_public": self.private_challenge_phase.is_submission_public,  # noqa: C0301
                "disable_logs": self.private_challenge_phase.disable_logs,
            },
        ]

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_phase_when_a_phase_is_not_public(self):
        self.challenge_phase.is_public = False
        self.challenge_phase.save()

        expected = []

        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateChallengePhaseTest(
    BaseChallengePhaseClass
):  # pylint: disable=too-many-instance-attributes
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_list",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.data = {
            "name": "New Challenge Phase",
            "description": "Description for new challenge phase",
            "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
        }

    @override_settings(MEDIA_ROOT="/tmp/evalai")
    def test_create_challenge_phase_with_all_data(self):
        self.data["test_annotation"] = SimpleUploadedFile(
            "another_test_file.txt",
            b"Another Dummy file content",
            content_type="text/plain",
        )
        self.data["codename"] = "Test Code Name"
        response = self.client.post(self.url, self.data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(MEDIA_ROOT="/tmp/evalai")
    def test_create_challenge_phase_with_same_codename(self):
        self.data["test_annotation"] = SimpleUploadedFile(
            "another_test_file.txt",
            b"Another Dummy file content",
            content_type="text/plain",
        )

        expected = {
            "non_field_errors": [
                "The fields codename, challenge must make a unique set."
            ]
        }
        response = self.client.post(self.url, self.data, format="multipart")
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_max_submissions_per_month_if_field_exist(self):
        zip_file_path = join(
            settings.BASE_DIR, "examples", "example1", "test_zip_file.zip"
        )
        with open(zip_file_path, "rb") as zip_file:
            zip_file_content = zip_file.read()
            zip_file_name = zip_file.name
            self.test_zip_file = SimpleUploadedFile(  # pylint: disable=attribute-defined-outside-init
                zip_file_name,
                zip_file_content,
                content_type="application/zip",
            )

        self.zip_configuration = ChallengeConfiguration.objects.create(  # pylint: disable=attribute-defined-outside-init
            user=self.user,
            challenge=self.challenge,
            zip_configuration=SimpleUploadedFile(
                zip_file_name,
                zip_file_content,
                content_type="application/zip",
            ),
            stdout_file=None,
            stderr_file=None,
        )
        self.client.force_authenticate(user=self.user)

        self.input_zip_file = SimpleUploadedFile(  # pylint: disable=attribute-defined-outside-init
            "test_sample.zip",
            b"Dummy File Content",
            content_type="application/zip",
        )

        self.url = (
            reverse_lazy(  # pylint: disable=attribute-defined-outside-init
                "challenges:create_challenge_using_zip_file",
                kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
            )
        )
        with mock.patch("challenges.views.requests.get") as m:
            resp = mock.Mock()
            resp.content = self.test_zip_file.read()
            resp.status_code = 200
            m.return_value = resp
            response = self.client.post(
                self.url,
                {"zip_configuration": self.input_zip_file},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for zipTestPhase in ChallengePhase.objects.all():
            max_per_month_field = zipTestPhase._meta.get_field(  # pylint: disable=protected-access
                "max_submissions_per_month"
            )
            max_per_month = max_per_month_field.value_from_object(zipTestPhase)
            id_field = zipTestPhase._meta.get_field(  # pylint: disable=protected-access
                "name"
            )
            id_val = id_field.value_from_object(zipTestPhase)
            if id_val == "Challenge Name of the challenge phase":
                self.assertTrue(max_per_month in (1000, 345))

    def test_max_submissions_per_month_if_field_doesnt_exist(self):
        zip_file_path = join(
            settings.BASE_DIR, "examples", "example1", "test_zip_file.zip"
        )
        with open(zip_file_path, "rb") as zip_file:
            zip_file_content = zip_file.read()
            zip_file_name = zip_file.name
            self.test_zip_file = SimpleUploadedFile(  # pylint: disable=attribute-defined-outside-init
                zip_file_name,
                zip_file_content,
                content_type="application/zip",
            )

        self.zip_configuration = ChallengeConfiguration.objects.create(  # pylint: disable=attribute-defined-outside-init
            user=self.user,
            challenge=self.challenge,
            zip_configuration=SimpleUploadedFile(
                zip_file_name,
                zip_file_content,
                content_type="application/zip",
            ),
            stdout_file=None,
            stderr_file=None,
        )
        self.client.force_authenticate(user=self.user)

        self.input_zip_file = SimpleUploadedFile(  # pylint: disable=attribute-defined-outside-init
            "test_sample.zip",
            b"Dummy File Content",
            content_type="application/zip",
        )

        self.url = (
            reverse_lazy(  # pylint: disable=attribute-defined-outside-init
                "challenges:create_challenge_using_zip_file",
                kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
            )
        )
        with mock.patch("challenges.views.requests.get") as m:
            resp = mock.Mock()
            resp.content = self.test_zip_file.read()
            resp.status_code = 200
            m.return_value = resp
            response = self.client.post(
                self.url,
                {"zip_configuration": self.input_zip_file},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        for zipTestPhase in ChallengePhase.objects.all():
            max_per_month_field = zipTestPhase._meta.get_field(  # pylint: disable=protected-access
                "max_submissions_per_month"
            )
            max_per_month = max_per_month_field.value_from_object(zipTestPhase)

            max_field = zipTestPhase._meta.get_field(  # pylint: disable=protected-access
                "max_submissions"
            )
            max_total = max_field.value_from_object(zipTestPhase)

            self.assertTrue(max_per_month == max_total)

    def test_create_challenge_phase_with_no_data(self):
        del self.data["name"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_challenge_phase_when_user_is_not_authenticated(self):
        self.client.force_authenticate(user=None)

        expected = {"error": "Authentication credentials were not provided."}

        response = self.client.post(self.url, {})
        self.assertEqual(list(response.data.values())[0], expected["error"])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_challenge_phase_when_user_is_a_part_of_host_team(self):
        self.user1 = User.objects.create(  # pylint: disable=attribute-defined-outside-init
            username="otheruser", password="other_secret_password"
        )

        self.challenge_host_team1 = ChallengeHostTeam.objects.create(  # pylint: disable=attribute-defined-outside-init
            team_name="Other Test Challenge Host Team", created_by=self.user1
        )

        # Now allot self.user as also a host of self.challenge_host_team1
        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team1,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.challenge2 = Challenge.objects.create(  # pylint: disable=attribute-defined-outside-init
            title="Other Test Challenge",
            short_description="Short description for other test challenge",
            description="Description for other test challenge",
            terms_and_conditions="Terms and conditions for other test challenge",  # noqa: C0301
            submission_guidelines="Submission guidelines for other test challenge",  # noqa: C0301
            creator=self.challenge_host_team1,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        data = {
            "name": "Challenge Phase 2",
            "description": "Description for Challenge Phase 2",
            "leaderboard_public": False,
            "is_public": True,
            "start_date": timezone.now() - timedelta(days=2),
            "end_date": timezone.now() + timedelta(days=1),
            "test_annotation": SimpleUploadedFile(
                "test_sample_file.txt",
                b"Dummy file content",
                content_type="text/plain",
            ),
            "max_submissions_per_day": 100000,
            "max_submissions_per_month": 100000,
            "max_submissions": 100000,
            "max_concurrent_submissions_allowed": 3,
            "codename": "Phase Code Name 2",
            "is_restricted_to_select_one_submission": True,
            "is_partial_submission_evaluation_enabled": False,
        }
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_list",
            kwargs={"challenge_pk": self.challenge2.pk},
        )
        response = self.client.post(self.url, data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_phase_when_user_is_not_part_of_host_team(self):
        self.user2 = User.objects.create(  # pylint: disable=attribute-defined-outside-init
            username="user_is_not_part_of_host_team",
            password="other_secret_password",
        )

        self.challenge_host_team2 = ChallengeHostTeam.objects.create(  # pylint: disable=attribute-defined-outside-init
            team_name="Other Test Challenge Host Team 2", created_by=self.user2
        )

        self.challenge2 = Challenge.objects.create(  # pylint: disable=attribute-defined-outside-init
            title="Other Test Challenge",
            short_description="Short description for other test challenge",
            description="Description for other test challenge",
            terms_and_conditions="Terms and conditions for other test challenge",  # noqa: C0301
            submission_guidelines="Submission guidelines for other test challenge",  # noqa: C0301
            creator=self.challenge_host_team2,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        data = {
            "name": "Challenge Phase 2",
            "description": "Description for Challenge Phase 2",
            "leaderboard_public": False,
            "is_public": True,
            "start_date": timezone.now() - timedelta(days=2),
            "end_date": timezone.now() + timedelta(days=1),
            "test_annotation": SimpleUploadedFile(
                "test_sample_file.txt",
                b"Dummy file content",
                content_type="text/plain",
            ),
            "max_submissions_per_day": 100000,
            "max_submissions_per_month": 100000,
            "max_submissions": 100000,
            "max_concurrent_submissions_allowed": 3,
            "codename": "Phase Code Name 2",
            "is_restricted_to_select_one_submission": True,
            "is_partial_submission_evaluation_enabled": False,
        }
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_list",
            kwargs={"challenge_pk": self.challenge2.pk},
        )

        expected = {
            "error": "Sorry, you are not allowed to perform this operation!"
        }
        response = self.client.post(self.url, data, format="multipart")
        self.assertEqual(response.data["detail"], expected["error"])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GetParticularChallengePhase(
    BaseChallengePhaseClass
):  # pylint: disable=too-many-instance-attributes
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_detail",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "pk": self.challenge_phase.pk,
            },
        )

    def test_get_particular_challenge_phase_if_user_is_participant(self):
        expected = {
            "id": self.challenge_phase.id,
            "name": self.challenge_phase.name,
            "description": self.challenge_phase.description,
            "leaderboard_public": self.challenge_phase.leaderboard_public,
            "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "challenge": self.challenge_phase.challenge.pk,
            "is_public": self.challenge_phase.is_public,
            "is_active": True,
            "codename": "Phase Code Name",
            "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,  # noqa: C0301
            "max_submissions": self.challenge_phase.max_submissions,
            "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
            "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
            "slug": self.challenge_phase.slug,
            "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
            "submission_meta_attributes": None,
            "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
            "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
            "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,  # noqa: C0301
            "allowed_email_ids": self.challenge_phase.allowed_email_ids,
            "is_submission_public": self.challenge_phase.is_submission_public,
            "disable_logs": self.challenge_phase.disable_logs,
        }
        self.client.force_authenticate(user=self.participant_user)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_particular_challenge_phase_if_user_is_challenge_host(self):
        expected = {
            "id": self.challenge_phase.id,
            "name": self.challenge_phase.name,
            "description": self.challenge_phase.description,
            "leaderboard_public": self.challenge_phase.leaderboard_public,
            "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "challenge": self.challenge_phase.challenge.pk,
            "is_public": self.challenge_phase.is_public,
            "is_submission_public": self.challenge_phase.is_submission_public,
            "annotations_uploaded_using_cli": self.challenge_phase.annotations_uploaded_using_cli,  # noqa: C0301
            "is_active": True,
            "codename": "Phase Code Name",
            "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,  # noqa: C0301
            "max_submissions": self.challenge_phase.max_submissions,
            "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
            "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
            "test_annotation": f"http://testserver{self.challenge_phase.test_annotation.url}",
            "slug": self.challenge_phase.slug,
            "environment_image": self.challenge_phase.environment_image,
            "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
            "submission_meta_attributes": None,
            "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
            "config_id": None,
            "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
            "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,  # noqa: C0301
            "allowed_email_ids": self.challenge_phase.allowed_email_ids,
            "disable_logs": self.challenge_phase.disable_logs,
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_challenge_phase_when_user_is_not_its_creator(self):
        self.user1 = User.objects.create(  # pylint: disable=attribute-defined-outside-init
            username="someuser1",
            email="user1@test.com",
            password="secret_psassword",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@test.com",
            primary=True,
            verified=True,
        )

        self.client.force_authenticate(user=self.user1)

        expected = {
            "detail": "Sorry, you are not allowed to perform this operation!"
        }

        response = self.client.put(
            self.url, {"name": "Rose Phase", "description": "New description."}
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_challenge_phase_when_user_is_its_creator(self):
        new_name = "Rose Phase"
        new_description = "New description."
        expected = {
            "id": self.challenge_phase.id,
            "name": new_name,
            "description": new_description,
            "leaderboard_public": self.challenge_phase.leaderboard_public,
            "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "challenge": self.challenge_phase.challenge.pk,
            "is_public": self.challenge_phase.is_public,
            "is_active": True,
            "codename": "Phase Code Name",
            "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,  # noqa: C0301
            "max_submissions": self.challenge_phase.max_submissions,
            "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
            "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
            "slug": self.challenge_phase.slug,
            "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
            "submission_meta_attributes": None,
            "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
            "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
            "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,  # noqa: C0301
            "allowed_email_ids": self.challenge_phase.allowed_email_ids,
            "is_submission_public": self.challenge_phase.is_submission_public,
            "disable_logs": self.challenge_phase.disable_logs,
        }
        response = self.client.put(
            self.url, {"name": new_name, "description": new_description}
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_detail",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "pk": self.challenge_phase.pk + 2,
            },
        )
        expected = {
            "error": f"Challenge phase {self.challenge_phase.pk + 2} does not exist for challenge {self.challenge.pk}"  # noqa: C0301
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_host_team_for_challenge_does_not_exist(self):
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_detail",
            kwargs={
                "challenge_pk": self.challenge.pk + 1,
                "pk": self.challenge_phase.pk,
            },
        )
        expected = {"error": "Challenge does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_particular_challenge_phase_when_user_is_not_authenticated(
        self,
    ):
        self.client.force_authenticate(user=None)

        expected = {"error": "Authentication credentials were not provided."}

        response = self.client.post(self.url, {})
        self.assertEqual(list(response.data.values())[0], expected["error"])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class UpdateParticularChallengePhase(
    BaseChallengePhaseClass
):  # pylint: disable=too-many-instance-attributes
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_detail",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "pk": self.challenge_phase.pk,
            },
        )

        self.partial_update_challenge_phase_name = (
            "Partial Update Challenge Phase Name"
        )
        self.update_challenge_phase_title = "Update Challenge Phase Name"
        self.update_description = "Update Challenge Phase Description"
        self.data = {
            "name": self.update_challenge_phase_title,
            "description": self.update_description,
        }

    def test_particular_challenge_phase_partial_update(self):
        self.partial_update_data = (
            {  # pylint: disable=attribute-defined-outside-init
                "name": self.partial_update_challenge_phase_name
            }
        )
        expected = {
            "id": self.challenge_phase.id,
            "name": self.partial_update_challenge_phase_name,
            "description": self.challenge_phase.description,
            "leaderboard_public": self.challenge_phase.leaderboard_public,
            "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(
                "+00:00", ""
            ),
            "challenge": self.challenge_phase.challenge.pk,
            "is_public": self.challenge_phase.is_public,
            "is_active": True,
            "codename": "Phase Code Name",
            "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,  # noqa: C0301
            "max_submissions": self.challenge_phase.max_submissions,
            "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
            "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
            "slug": self.challenge_phase.slug,
            "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
            "submission_meta_attributes": None,
            "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
            "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
            "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,  # noqa: C0301
            "allowed_email_ids": self.challenge_phase.allowed_email_ids,
            "is_submission_public": self.challenge_phase.is_submission_public,
            "disable_logs": self.challenge_phase.disable_logs,
        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(MEDIA_ROOT="/tmp/evalai")
    def test_particular_challenge_phase_update(self):

        self.update_test_annotation = SimpleUploadedFile(  # pylint: disable=attribute-defined-outside-init
            "update_test_sample_file.txt",
            b"Dummy update file content",
            content_type="text/plain",
        )
        self.data["test_annotation"] = self.update_test_annotation
        response = self.client.put(self.url, self.data, format="multipart")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_update_with_no_data(self):
        self.data = {"name": ""}
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_particular_challenge_update_when_user_is_not_authenticated(self):
        self.client.force_authenticate(user=None)

        expected = {"error": "Authentication credentials were not provided."}

        response = self.client.post(self.url, {})
        self.assertEqual(list(response.data.values())[0], expected["error"])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DeleteParticularChallengePhase(BaseChallengePhaseClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_detail",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "pk": self.challenge_phase.pk,
            },
        )

    def test_particular_challenge_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_particular_challenge_delete_when_user_is_not_authenticated(self):
        self.client.force_authenticate(user=None)

        expected = {"error": "Authentication credentials were not provided."}

        response = self.client.post(self.url, {})
        self.assertEqual(list(response.data.values())[0], expected["error"])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BaseChallengePhaseSplitClass(
    BaseAPITestClass
):  # pylint: disable=too-many-instance-attributes
    def setUp(self):
        super().setUp()
        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        self.user2 = User.objects.create(
            username="someuser2",
            email="user2@test.com",
            password="secret_password2",
            is_staff=True,
        )

        self.participant_user = User.objects.create(
            username="someuser1",
            email="participant@test.com",
            password="secret_password1",
        )

        EmailAddress.objects.create(
            user=self.participant_user,
            email="participant@test.com",
            primary=True,
            verified=True,
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@test.com",
            primary=True,
            verified=True,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for get challenge phase split tests",
            created_by=self.participant_user,
        )

        self.participant = Participant.objects.create(
            user=self.participant_user,
            status=Participant.SELF,
            team=self.participant_team,
        )

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

        self.dataset_split = DatasetSplit.objects.create(
            name="Test Dataset Split", codename="test-split"
        )
        self.dataset_split_host = DatasetSplit.objects.create(
            name="Test Dataset Split host", codename="test-split-host"
        )

        self.leaderboard = Leaderboard.objects.create(
            schema=json.dumps({"hello": "world"})
        )

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            dataset_split=self.dataset_split,
            challenge_phase=self.challenge_phase,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC,
            leaderboard_decimal_precision=2,
            is_leaderboard_order_descending=True,
            show_leaderboard_by_latest_submission=False,
        )

        self.challenge_phase_split_host = ChallengePhaseSplit.objects.create(
            dataset_split=self.dataset_split_host,
            challenge_phase=self.challenge_phase,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.HOST,
            show_leaderboard_by_latest_submission=False,
        )

    def tearDown(self):  # pylint: disable=no-self-use
        shutil.rmtree("/tmp/evalai")


class GetChallengePhaseSplitTest(BaseChallengePhaseSplitClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:challenge_phase_split_list",
            kwargs={"challenge_pk": self.challenge.pk},
        )

    def test_get_challenge_phase_split(self):
        expected = [
            {
                "id": self.challenge_phase_split.id,
                "challenge_phase": self.challenge_phase.id,
                "challenge_phase_name": self.challenge_phase.name,
                "dataset_split": self.dataset_split.id,
                "dataset_split_name": self.dataset_split.name,
                "visibility": self.challenge_phase_split.visibility,
                "show_leaderboard_by_latest_submission": self.challenge_phase_split.show_leaderboard_by_latest_submission,  # noqa: C0301
                "show_execution_time": False,
                "leaderboard_schema": self.challenge_phase_split.leaderboard.schema,  # noqa: C0301
                "is_multi_metric_leaderboard": self.challenge_phase_split.is_multi_metric_leaderboard,  # noqa: C0301
            }
        ]
        self.client.force_authenticate(user=self.participant_user)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_phase_split_when_challenge_phase_does_not_exist(
        self,
    ):
        self.url = reverse_lazy(
            "challenges:challenge_phase_split_list",
            kwargs={"challenge_pk": self.challenge.pk},
        )

        self.challenge.delete()

        expected = {"error": "Challenge does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_challenge_phase_split_when_user_is_challenge_host(self):
        self.url = reverse_lazy(
            "challenges:challenge_phase_split_list",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        expected = [
            {
                "id": self.challenge_phase_split.id,
                "challenge_phase": self.challenge_phase.id,
                "challenge_phase_name": self.challenge_phase.name,
                "dataset_split": self.dataset_split.id,
                "dataset_split_name": self.dataset_split.name,
                "visibility": self.challenge_phase_split.visibility,
                "show_leaderboard_by_latest_submission": self.challenge_phase_split.show_leaderboard_by_latest_submission,  # noqa: C0301
                "show_execution_time": False,
                "leaderboard_schema": self.challenge_phase_split.leaderboard.schema,  # noqa: C0301
                "is_multi_metric_leaderboard": self.challenge_phase_split.is_multi_metric_leaderboard,  # noqa: C0301
            },
            {
                "id": self.challenge_phase_split_host.id,
                "challenge_phase": self.challenge_phase.id,
                "challenge_phase_name": self.challenge_phase.name,
                "dataset_split": self.dataset_split_host.id,
                "dataset_split_name": self.dataset_split_host.name,
                "visibility": self.challenge_phase_split_host.visibility,
                "show_leaderboard_by_latest_submission": self.challenge_phase_split_host.show_leaderboard_by_latest_submission,  # noqa: C0301
                "show_execution_time": False,
                "leaderboard_schema": self.challenge_phase_split_host.leaderboard.schema,  # noqa: C0301
                "is_multi_metric_leaderboard": self.challenge_phase_split_host.is_multi_metric_leaderboard,  # noqa: C0301
            },
        ]
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_phase_split_when_user_is_staff(self):
        self.url = reverse_lazy(
            "challenges:challenge_phase_split_list",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        expected = [
            {
                "id": self.challenge_phase_split.id,
                "challenge_phase": self.challenge_phase.id,
                "challenge_phase_name": self.challenge_phase.name,
                "dataset_split": self.dataset_split.id,
                "dataset_split_name": self.dataset_split.name,
                "visibility": self.challenge_phase_split.visibility,
                "show_leaderboard_by_latest_submission": self.challenge_phase_split.show_leaderboard_by_latest_submission,  # noqa: C0301
                "show_execution_time": False,
                "leaderboard_schema": self.challenge_phase_split.leaderboard.schema,  # noqa: C0301
                "is_multi_metric_leaderboard": self.challenge_phase_split.is_multi_metric_leaderboard,  # noqa: C0301
            },
            {
                "id": self.challenge_phase_split_host.id,
                "challenge_phase": self.challenge_phase.id,
                "challenge_phase_name": self.challenge_phase.name,
                "dataset_split": self.dataset_split_host.id,
                "dataset_split_name": self.dataset_split_host.name,
                "visibility": self.challenge_phase_split_host.visibility,
                "show_leaderboard_by_latest_submission": self.challenge_phase_split_host.show_leaderboard_by_latest_submission,  # noqa: C0301
                "show_execution_time": False,
                "leaderboard_schema": self.challenge_phase_split_host.leaderboard.schema,  # noqa: C0301
                "is_multi_metric_leaderboard": self.challenge_phase_split_host.is_multi_metric_leaderboard,  # noqa: C0301
            },
        ]
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateChallengeUsingZipFile(
    APITestCase
):  # pylint: disable=too-many-instance-attributes
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="host", email="host@test.com", password="secret_password"
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        self.path = join(
            settings.BASE_DIR, "examples", "example1", "test_zip_file"
        )

        with open(
            join(self.path, "description.html"), "rb"
        ) as desc_file, open(
            join(self.path, "terms_and_conditions.html"), "rb"
        ) as terms_file, open(
            join(self.path, "submission_guidelines.html"), "rb"
        ) as guidelines_file, open(
            join(self.path, "evaluation_details.html"), "rb"
        ) as eval_file:
            self.challenge = Challenge.objects.create(
                title="Challenge Title",
                short_description="Short description of the challenge (preferably 140 characters)",  # noqa: C0301
                description=desc_file.read().decode("utf-8"),
                terms_and_conditions=terms_file.read().decode("utf-8"),
                submission_guidelines=guidelines_file.read().decode("utf-8"),
                evaluation_details=eval_file.read().decode("utf-8"),
                creator=self.challenge_host_team,
                published=False,
                enable_forum=True,
                anonymous_leaderboard=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
            )
        self.challenge.slug = (
            f"{self.challenge.title.replace(' ', '-').lower()}-{self.challenge.pk}"
        )[:199]
        self.challenge.save()

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            with open(
                join(self.path, "challenge_phase_description.html"), "rb"
            ) as desc_file:
                description = desc_file.read().decode("utf-8")
            with open(
                join(self.path, "test_annotation.txt"), "rb"
            ) as test_file:
                test_file_name = test_file.name
                test_file_content = test_file.read()
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description=description,
                leaderboard_public=False,
                is_public=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    test_file_name,
                    test_file_content,
                    content_type="text/plain",
                ),
            )
        self.dataset_split = DatasetSplit.objects.create(
            name="Name of the dataset split",
            codename="codename of dataset split",
        )

        self.leaderboard = Leaderboard.objects.create(
            schema=json.dumps(
                {
                    "labels": ["yes/no", "number", "others", "overall"],
                    "default_order_by": "overall",
                }
            )
        )

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            dataset_split=self.dataset_split,
            challenge_phase=self.challenge_phase,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC,
        )

        zip_file_path = join(
            settings.BASE_DIR, "examples", "example1", "test_zip_file.zip"
        )
        with open(zip_file_path, "rb") as zip_file:
            zip_file_content = zip_file.read()
            zip_file_name = zip_file.name

        self.test_zip_file = SimpleUploadedFile(
            zip_file_name,
            zip_file_content,
            content_type="application/zip",
        )

        self.zip_configuration = ChallengeConfiguration.objects.create(  # pylint: disable=attribute-defined-outside-init
            user=self.user,
            challenge=self.challenge,
            zip_configuration=SimpleUploadedFile(
                zip_file_name,
                zip_file_content,
                content_type="application/zip",
            ),
            stdout_file=None,
            stderr_file=None,
        )
        self.client.force_authenticate(user=self.user)

        self.input_zip_file = SimpleUploadedFile(
            "test_sample.zip",
            b"Dummy File Content",
            content_type="application/zip",
        )

    @responses.activate
    def test_create_challenge_using_zip_file_when_zip_file_is_not_uploaded(
        self,
    ):
        responses.add(responses.POST, settings.SLACK_WEB_HOOK_URL, status=200)
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:create_challenge_using_zip_file",
                kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
            )
        )
        expected = {"zip_configuration": ["No file was submitted."]}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @responses.activate
    def test_create_challenge_using_zip_file_when_zip_file_is_not_uploaded_successfully(  # noqa: C0301
        self,
    ):
        responses.add(responses.POST, settings.SLACK_WEB_HOOK_URL, status=200)
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:create_challenge_using_zip_file",
                kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
            )
        )

        expected = {
            "zip_configuration": [
                "The submitted data was not a file. Check the encoding type on the form."  # noqa: C0301
            ]
        }
        response = self.client.post(
            self.url, {"zip_configuration": self.input_zip_file}
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @responses.activate
    def test_create_challenge_using_zip_file_when_server_error_occurs(self):
        responses.add(responses.POST, settings.SLACK_WEB_HOOK_URL, status=200)
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:create_challenge_using_zip_file",
                kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
            )
        )
        expected = {
            "error": "A server error occured while processing zip file. Please try again!"  # noqa: C0301
        }
        response = self.client.post(
            self.url,
            {"zip_configuration": self.input_zip_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    @responses.activate
    def test_create_challenge_using_zip_file_when_challenge_host_team_does_not_exists(  # noqa: C0301
        self,
    ):
        responses.add(responses.POST, settings.SLACK_WEB_HOOK_URL, status=200)
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:create_challenge_using_zip_file",
                kwargs={
                    "challenge_host_team_pk": self.challenge_host_team.pk + 10
                },
            )
        )
        expected = {
            "detail": f"ChallengeHostTeam {self.challenge_host_team.pk + 10} does not exist"  # noqa: C0301
        }
        response = self.client.post(
            self.url,
            {"zip_configuration": self.input_zip_file},
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @responses.activate
    def test_create_challenge_using_zip_file_when_user_is_not_authenticated(
        self,
    ):
        responses.add(responses.POST, settings.SLACK_WEB_HOOK_URL, status=200)
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:create_challenge_using_zip_file",
                kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
            )
        )
        self.client.force_authenticate(user=None)

        expected = {"error": "Authentication credentials were not provided."}

        response = self.client.post(self.url, {})
        self.assertEqual(list(response.data.values())[0], expected["error"])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @responses.activate
    def test_create_challenge_using_zip_file_when_max_concurrent_submissions_allowed_exists(  # noqa: C0301
        self,
    ):
        challenge_phases = ChallengePhase.objects.all()
        for zipTestPhase in challenge_phases:
            max_concurrent_submissions_allowed_field = zipTestPhase._meta.get_field(  # pylint: disable=protected-access
                "max_concurrent_submissions_allowed"
            )
            max_con = (
                max_concurrent_submissions_allowed_field.value_from_object(
                    zipTestPhase
                )
            )
            self.assertTrue(max_con == 3)

    @responses.activate
    def test_create_challenge_using_zip_file_success(self):
        responses.add(responses.POST, settings.SLACK_WEB_HOOK_URL, status=200)
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:create_challenge_using_zip_file",
                kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
            )
        )

        self.assertEqual(Challenge.objects.count(), 1)
        self.assertEqual(DatasetSplit.objects.count(), 1)
        self.assertEqual(Leaderboard.objects.count(), 1)
        self.assertEqual(ChallengePhaseSplit.objects.count(), 1)

        with mock.patch("challenges.views.requests.get") as m:
            resp = mock.Mock()
            resp.content = self.test_zip_file.read()
            resp.status_code = 200
            m.return_value = resp
            response = self.client.post(
                self.url,
                {"zip_configuration": self.input_zip_file},
                format="multipart",
            )
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertEqual(Challenge.objects.count(), 2)
        self.assertEqual(DatasetSplit.objects.count(), 2)
        self.assertEqual(Leaderboard.objects.count(), 2)
        self.assertEqual(ChallengePhaseSplit.objects.count(), 2)


class GetAllSubmissionsTest(
    BaseAPITestClass
):  # pylint: disable=too-many-instance-attributes
    def setUp(self):
        super().setUp()

        self.user5 = User.objects.create(
            username="otheruser",
            password="other_secret_password",
            email="user5@test.com",
        )

        self.user6 = User.objects.create(
            username="participant",
            password="secret password",
            email="user6@test.com",
        )

        self.user7 = User.objects.create(
            username="not a challenge host of challenge5",
            password="secret password",
        )

        EmailAddress.objects.create(
            user=self.user5,
            email="user5@test.com",
            primary=True,
            verified=True,
        )

        EmailAddress.objects.create(
            user=self.user6,
            email="user6@test.com",
            primary=True,
            verified=True,
        )

        EmailAddress.objects.create(
            user=self.user7,
            email="user7@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host_team7 = ChallengeHostTeam.objects.create(
            team_name="Other Test Challenge Host Team7", created_by=self.user7
        )
        self.challenge_host_team5 = ChallengeHostTeam.objects.create(
            team_name="Other Test Challenge Host Team5", created_by=self.user5
        )

        # Now allot self.user as also a host of self.challenge_host_team1
        self.challenge_host5 = ChallengeHost.objects.create(
            user=self.user5,
            team_name=self.challenge_host_team5,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.participant_team6 = ParticipantTeam.objects.create(
            team_name="Participant Team 1 for Challenge5",
            created_by=self.user6,
        )

        self.participant_team7 = ParticipantTeam.objects.create(
            team_name="Participant Team 2 for Challenge5",
            created_by=self.user7,
        )

        self.participant6 = Participant.objects.create(
            user=self.user6,
            status=Participant.ACCEPTED,
            team=self.participant_team6,
        )

        self.challenge5 = Challenge.objects.create(
            title="Other Test Challenge",
            short_description="Short description for other test challenge",  # noqa: C0301
            description="Description for other test challenge",  # noqa: C0301
            terms_and_conditions="Terms and conditions for other test challenge",  # noqa: C0301
            submission_guidelines="Submission guidelines for other test challenge",  # noqa: C0301
            creator=self.challenge_host_team5,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge5_phase1 = ChallengePhase.objects.create(
                name="Challenge Phase 1",
                description="Description for Challenge Phase 1",
                leaderboard_public=False,
                codename="Phase Code Name 1",
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge5,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content 1",
                    content_type="text/plain",
                ),
            )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge5_phase2 = ChallengePhase.objects.create(
                name="Challenge Phase 2",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                codename="Phase Code Name 2",
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge5,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content 2",
                    content_type="text/plain",
                ),
            )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge5_phase3 = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge5,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
            )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.submission1 = Submission.objects.create(
                participant_team=self.participant_team6,
                challenge_phase=self.challenge5_phase3,
                created_by=self.challenge_host_team5.created_by,
                status="submitted",
                input_file=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                method_name="Test Method 1",
                method_description="Test Description 1",
                project_url="http://testserver1/",
                publication_url="http://testserver1/",
                is_public=True,
                is_flagged=True,
            )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.submission2 = Submission.objects.create(
                participant_team=self.participant_team6,
                challenge_phase=self.challenge5_phase1,
                created_by=self.challenge_host_team5.created_by,
                status="submitted",
                input_file=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                method_name="Test Method 2",
                method_description="Test Description 2",
                project_url="http://testserver2/",
                publication_url="http://testserver2/",
                is_public=True,
                is_flagged=True,
            )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.submission3 = Submission.objects.create(
                participant_team=self.participant_team6,
                challenge_phase=self.challenge5_phase1,
                created_by=self.challenge_host_team5.created_by,
                status="submitted",
                input_file=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                method_name="Test Method 3",
                method_description="Test Description 3",
                project_url="http://testserver3/",
                publication_url="http://testserver3/",
                is_public=True,
                is_flagged=True,
            )

        self.client.force_authenticate(user=self.user6)

    def test_get_all_submissions_when_challenge_does_not_exist(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_all_submissions_of_challenge",
                kwargs={
                    "challenge_pk": self.challenge5.pk + 10,
                    "challenge_phase_pk": self.challenge5_phase3.pk,
                },
            )
        )
        expected = {
            "detail": f"Challenge {self.challenge5.pk + 10} does not exist"
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_all_submissions_when_challenge_phase_does_not_exist(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_all_submissions_of_challenge",
                kwargs={
                    "challenge_pk": self.challenge5.pk,
                    "challenge_phase_pk": self.challenge5_phase3.pk + 10,
                },
            )
        )
        expected = {
            "error": f"Challenge Phase {self.challenge5_phase3.pk + 10} does not exist"  # noqa: C0301
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_all_submissions_when_user_is_host_of_challenge(self):
        self.url_phase1 = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_all_submissions_of_challenge",
                kwargs={
                    "challenge_pk": self.challenge5.pk,
                    "challenge_phase_pk": self.challenge5_phase1.pk,
                },
            )
        )
        self.url_phase2 = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_all_submissions_of_challenge",
                kwargs={
                    "challenge_pk": self.challenge5.pk,
                    "challenge_phase_pk": self.challenge5_phase2.pk,
                },
            )
        )
        self.client.force_authenticate(user=self.user5)
        submissions = [self.submission3, self.submission2]
        expected = []
        for submission in submissions:
            expected.append(
                {
                    "id": submission.id,
                    "participant_team": submission.participant_team.team_name,
                    "challenge_phase": submission.challenge_phase.name,
                    "created_by": submission.created_by.username,
                    "status": submission.status,
                    "is_public": submission.is_public,
                    "is_flagged": submission.is_flagged,  # noqa: C0301
                    "submission_number": submission.submission_number,
                    "submitted_at": f"{submission.submitted_at.isoformat()}Z".replace(  # noqa: C0301
                        "+00:00", ""
                    ),
                    "rerun_resumed_at": submission.rerun_resumed_at,  # noqa: C0301
                    "execution_time": submission.execution_time,
                    "input_file": f"http://testserver{submission.input_file.url}",
                    "submission_input_file": None,
                    "stdout_file": None,
                    "stderr_file": None,
                    "environment_log_file": None,
                    "submission_result_file": None,
                    "submission_metadata_file": None,
                    "participant_team_members_email_ids": ["user6@test.com"],
                    "participant_team_members_affiliations": [""],
                    "participant_team_members": [
                        {"username": "participant", "email": "user6@test.com"}
                    ],
                    "created_at": submission.created_at,
                    "method_name": submission.method_name,
                    "submission_metadata": None,
                    "method_description": submission.method_description,
                    "publication_url": submission.publication_url,
                    "project_url": submission.project_url,
                    "is_verified_by_host": False,
                }
            )
        response_phase1 = self.client.get(self.url_phase1, {})
        response_phase2 = self.client.get(self.url_phase2, {})
        self.assertEqual(response_phase1.data["results"], expected)
        self.assertEqual(response_phase1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_phase2.data["results"], [])
        self.assertEqual(response_phase2.status_code, status.HTTP_200_OK)

    def test_get_all_submissions_when_user_is_participant_of_challenge(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_all_submissions_of_challenge",
                kwargs={
                    "challenge_pk": self.challenge5.pk,
                    "challenge_phase_pk": self.challenge5_phase3.pk,
                },
            )
        )
        self.client.force_authenticate(user=self.user6)
        expected = [
            {
                "id": self.submission1.id,
                "participant_team": self.submission1.participant_team.pk,
                "participant_team_name": self.submission1.participant_team.team_name,  # noqa: C0301
                "execution_time": self.submission1.execution_time,
                "challenge_phase": self.submission1.challenge_phase.pk,
                "created_by": self.submission1.created_by.pk,  # noqa: C0301
                "status": self.submission1.status,
                "input_file": f"http://testserver{self.submission1.input_file.url}",  # noqa: C0301
                "submission_input_file": None,
                "method_name": self.submission1.method_name,
                "method_description": self.submission1.method_description,
                "project_url": self.submission1.project_url,
                "publication_url": self.submission1.publication_url,
                "stdout_file": None,
                "stderr_file": None,
                "submission_result_file": None,
                "started_at": self.submission1.started_at,
                "completed_at": self.submission1.completed_at,
                "submitted_at": f"{self.submission1.submitted_at.isoformat()}Z".replace(  # noqa: C0301
                    "+00:00", ""
                ),
                "rerun_resumed_at": self.submission1.rerun_resumed_at,
                "is_public": self.submission1.is_public,
                "is_flagged": self.submission1.is_flagged,
                "ignore_submission": False,
                "when_made_public": self.submission1.when_made_public,
                "is_baseline": self.submission1.is_baseline,
                "job_name": self.submission1.job_name,
                "submission_metadata": None,
                "is_verified_by_host": False,
            }
        ]
        self.challenge5.participant_teams.add(self.participant_team6)
        self.challenge5.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_all_submissions_when_user_is_neither_host_nor_participant_of_challenge(  # noqa: C0301
        self,
    ):
        self.client.force_authenticate(user=self.user7)
        # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:get_all_submissions_of_challenge",
            kwargs={
                "challenge_pk": self.challenge5.pk,
                "challenge_phase_pk": self.challenge5_phase3.pk,
            },
        )
        expected = {
            "error": "You are neither host nor participant of the challenge!"
        }
        self.challenge5.participant_teams.add(self.participant_team6)
        self.challenge5.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_all_challenges_submission_metrics(self):

        self.user8 = User.objects.create(  # pylint: disable=attribute-defined-outside-init
            username="admin_test",
            password="admin@123",
            is_staff=True,
        )

        EmailAddress.objects.create(
            user=self.user8,
            email="user8@test.com",
            primary=True,
            verified=True,
        )

        self.maxDiff = None  # pylint: disable=attribute-defined-outside-init

        url = reverse_lazy("challenges:get_all_challenges_submission_metrics")

        expected_response = {
            self.challenge.pk: {
                "archived": 0,
                "cancelled": 0,
                "failed": 0,
                "finished": 0,
                "partially_evaluated": 0,
                "resuming": 0,
                "running": 0,
                "queued": 0,
                "submitted": 0,
                "submitting": 0,
            },
            self.challenge5.pk: {
                "archived": 0,
                "cancelled": 0,
                "failed": 0,
                "finished": 0,
                "partially_evaluated": 0,
                "resuming": 0,
                "running": 0,
                "queued": 0,
                "submitted": 3,
                "submitting": 0,
            },
        }

        self.client.force_authenticate(user=self.user8)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_response)


class DownloadAllSubmissionsFileTest(
    BaseAPITestClass
):  # pylint: disable=too-many-instance-attributes
    def setUp(self):
        super().setUp()

        self.user1 = User.objects.create(
            username="otheruser1",
            password="other_secret_password",
            email="user1@test.com",
        )

        self.user2 = User.objects.create(
            username="otheruser2",
            password="other_secret_password",
            email="user2@test.com",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@test.com",
            primary=True,
            verified=True,
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@test.com",
            primary=True,
            verified=True,
        )

        self.participant_team1 = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge8", created_by=self.user1
        )

        self.participant1 = Participant.objects.create(
            user=self.user1,
            status=Participant.ACCEPTED,
            team=self.participant_team1,
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
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
            )
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.submission = Submission.objects.create(
                participant_team=self.participant_team1,
                challenge_phase=self.challenge_phase,
                created_by=self.participant_team1.created_by,
                status="submitted",
                input_file=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                method_name="Test Method",
                method_description="Test Description",
                project_url="http://testserver/",
                publication_url="http://testserver/",
                is_public=True,
            )

        self.file_type_csv = "csv"

        self.file_type_pdf = "pdf"

    def test_download_all_submissions_when_challenge_does_not_exist(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:download_all_submissions",
                kwargs={
                    "challenge_pk": self.challenge.pk + 10,
                    "challenge_phase_pk": self.challenge_phase.pk,
                    "file_type": self.file_type_csv,
                },
            )
        )
        expected = {
            "detail": f"Challenge {self.challenge.pk + 10} does not exist"
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_all_submissions_when_challenge_phase_does_not_exist(
        self,
    ):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:download_all_submissions",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "challenge_phase_pk": self.challenge_phase.pk + 10,
                    "file_type": self.file_type_csv,
                },
            )
        )
        expected = {
            "error": f"Challenge Phase {self.challenge_phase.pk + 10} does not exist"  # noqa: C0301
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_all_submissions_when_file_type_is_not_csv(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:download_all_submissions",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "challenge_phase_pk": self.challenge_phase.pk,
                    "file_type": self.file_type_pdf,
                },
            )
        )
        expected = {"error": "The file type requested is not valid!"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_download_all_submissions_when_user_is_challenge_host(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:download_all_submissions",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "challenge_phase_pk": self.challenge_phase.pk,
                    "file_type": self.file_type_csv,
                },
            )
        )
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_all_submissions_for_host_with_custom_fields(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:download_all_submissions",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "challenge_phase_pk": self.challenge_phase.pk,
                    "file_type": self.file_type_csv,
                },
            )
        )
        submissions = Submission.objects.filter(
            challenge_phase__challenge=self.challenge
        ).order_by("-submitted_at")
        submissions = ChallengeSubmissionManagementSerializer(
            submissions, many=True
        )
        expected = io.StringIO()
        expected_submissions = csv.writer(expected, quoting=csv.QUOTE_ALL)
        expected_submissions.writerow(
            ["id", "Team Members", "Team Members Email Id", "Challenge Phase"]
        )
        self.data = [  # pylint: disable=attribute-defined-outside-init
            "participant_team_members",
            "participant_team_members_email",
            "challenge_phase",
        ]
        for submission in submissions.data:
            row = [submission["id"]]
            for field in self.data:
                if field == "participant_team_members":
                    row.append(
                        ",".join(
                            username["username"]
                            for username in submission[
                                "participant_team_members"
                            ]
                        )
                    )
                elif field == "participant_team_members_email":
                    row.append(
                        ",".join(
                            email["email"]
                            for email in submission["participant_team_members"]
                        )
                    )
                elif field == "created_at":
                    row.append(
                        submission["created_at"].strftime("%m/%d/%Y %H:%M:%S")
                    )
                else:
                    row.append(submission[field])
            expected_submissions.writerow(row)
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.content.decode("utf-8"), expected.getvalue())
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_all_submissions_when_user_is_challenge_participant(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:download_all_submissions",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "challenge_phase_pk": self.challenge_phase.pk,
                    "file_type": self.file_type_csv,
                },
            )
        )

        self.challenge.participant_teams.add(self.participant_team1)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_all_submissions_when_user_is_neither_a_challenge_host_nor_a_participant(  # noqa: C0301
        self,
    ):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:download_all_submissions",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "challenge_phase_pk": self.challenge_phase.pk,
                    "file_type": self.file_type_csv,
                },
            )
        )

        self.client.force_authenticate(user=self.user2)

        expected = {
            "error": "You are neither host nor participant of the challenge!"
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CreateLeaderboardTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy("challenges:create_leaderboard")
        self.data = [
            {"schema": {"key": "value"}},
            {"schema": {"key2": "value2"}},
        ]

    def test_create_leaderboard_with_all_data(self):
        self.url = reverse_lazy("challenges:create_leaderboard")
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_leaderboard_with_no_data(self):
        self.url = reverse_lazy("challenges:create_leaderboard")
        self.data = []
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetOrUpdateLeaderboardTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.leaderboard = Leaderboard.objects.create(
            schema=json.dumps(
                {
                    "labels": ["yes/no", "number", "others", "overall"],
                    "default_order_by": "overall",
                }
            )
        )

        self.url = reverse_lazy(
            "challenges:get_or_update_leaderboard",
            kwargs={"leaderboard_pk": self.leaderboard.pk},
        )
        self.data = {"schema": {"key": "updated schema"}}

    def test_get_or_update_leaderboard_when_leaderboard_doesnt_exist(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_leaderboard",
            kwargs={"leaderboard_pk": self.leaderboard.pk + 10},
        )
        expected = {
            "detail": f"Leaderboard {self.leaderboard.pk + 10} does not exist"
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_leaderboard(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_leaderboard",
            kwargs={"leaderboard_pk": self.leaderboard.pk},
        )
        expected = {
            "id": self.leaderboard.pk,
            "schema": self.leaderboard.schema,
            "config_id": None,
        }
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_leaderboard_with_all_data(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_leaderboard",
            kwargs={"leaderboard_pk": self.leaderboard.pk},
        )
        self.data["schema"] = json.dumps(self.data["schema"])
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_leaderboard_with_no_data(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_leaderboard",
            kwargs={"leaderboard_pk": self.leaderboard.pk},
        )
        del self.data["schema"]
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateDatasetSplitTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy("challenges:create_dataset_split")

        self.data = [
            {"name": "Dataset Split1", "codename": "Dataset split codename1"},
            {"name": "Dataset split2", "codename": "Dataset split codename2"},
        ]

    def test_create_dataset_split_with_all_data(self):
        self.url = reverse_lazy("challenges:create_dataset_split")
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_dataset_split_with_no_data(self):
        self.url = reverse_lazy("challenges:create_dataset_split")
        self.data = []
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetOrUpdateDatasetSplitTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.dataset_split = DatasetSplit.objects.create(
            name="Name of the dataset split",
            codename="codename of dataset split",
        )

        self.url = reverse_lazy(
            "challenges:get_or_update_dataset_split",
            kwargs={"dataset_split_pk": self.dataset_split.pk},
        )
        self.data = {
            "name": "Updated Name of dataset split",
            "codename": "Updated codename of dataset split",
        }

    def test_get_or_update_dataset_split_when_dataset_split_doesnt_exist(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_dataset_split",
            kwargs={"dataset_split_pk": self.dataset_split.pk + 10},
        )
        expected = {
            "detail": f"DatasetSplit {self.dataset_split.pk + 10} does not exist"  # noqa: C0301
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_dataset_split(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_dataset_split",
            kwargs={"dataset_split_pk": self.dataset_split.pk},
        )
        expected = {
            "id": self.dataset_split.pk,
            "name": self.dataset_split.name,
            "codename": self.dataset_split.codename,
            "config_id": None,
        }
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_dataset_split_with_all_data(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_dataset_split",
            kwargs={"dataset_split_pk": self.dataset_split.pk},
        )
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_dataset_split_with_no_data(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_dataset_split",
            kwargs={"dataset_split_pk": self.dataset_split.pk},
        )
        del self.data["codename"]
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateChallengePhaseSplitTest(BaseChallengePhaseSplitClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy("challenges:create_challenge_phase_split")

        self.data = [
            {
                "dataset_split": self.dataset_split.pk,
                "challenge_phase": self.challenge_phase.pk,
                "leaderboard": self.leaderboard.pk,
                "visibility": 1,
            },
            {
                "dataset_split": self.dataset_split.pk,
                "challenge_phase": self.challenge_phase.pk,
                "leaderboard": self.leaderboard.pk,
                "visibility": 3,
            },
        ]

    def test_create_challenge_phase_split_with_all_data(self):
        self.url = reverse_lazy("challenges:create_challenge_phase_split")
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_dataset_split_with_no_data(self):
        self.url = reverse_lazy("challenges:create_challenge_phase_split")
        self.data = []
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetOrUpdateChallengePhaseSplitTest(BaseChallengePhaseSplitClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_or_update_dataset_split",
            kwargs={"challenge_phase_split_pk": self.challenge_phase_split.pk},
        )
        self.leaderboard1 = Leaderboard.objects.create(
            schema=json.dumps(
                {
                    "labels": ["yes/no", "number", "others", "overall"],
                    "default_order_by": "overall",
                }
            )
        )
        self.data = {"leaderboard": self.leaderboard1.pk}

    def test_get_or_update_dataset_split_when_dataset_split_doesnt_exist(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_challenge_phase_split",
            kwargs={
                "challenge_phase_split_pk": self.challenge_phase_split.pk + 10
            },
        )
        expected = {
            "detail": f"ChallengePhaseSplit {self.challenge_phase_split.pk + 10} does not exist"  # noqa: C0301
        }
        expected = {
            "detail": f"ChallengePhaseSplit {self.challenge_phase_split.pk + 10} does not exist"  # noqa: C0301
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_dataset_split(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_challenge_phase_split",
            kwargs={"challenge_phase_split_pk": self.challenge_phase_split.pk},
        )
        expected = {
            "id": self.challenge_phase_split.pk,
            "dataset_split": self.dataset_split.pk,
            "leaderboard": self.leaderboard.pk,
            "challenge_phase": self.challenge_phase.pk,
            "visibility": self.challenge_phase_split.visibility,
            "leaderboard_decimal_precision": self.challenge_phase_split.leaderboard_decimal_precision,  # noqa: C0301
            "is_leaderboard_order_descending": self.challenge_phase_split.is_leaderboard_order_descending,  # noqa: C0301
            "show_leaderboard_by_latest_submission": self.challenge_phase_split.show_leaderboard_by_latest_submission,  # noqa: C0301
            "show_execution_time": False,
        }
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_challenge_phase_split_with_all_data(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_challenge_phase_split",
            kwargs={"challenge_phase_split_pk": self.challenge_phase_split.pk},
        )
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_dataset_split_with_no_data(self):
        self.url = reverse_lazy(
            "challenges:get_or_update_challenge_phase_split",
            kwargs={"challenge_phase_split_pk": self.challenge_phase_split.pk},
        )
        del self.data["leaderboard"]
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StarChallengesTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:star_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.user2 = User.objects.create(
            username="someuser2",
            email="user2@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@test.com",
            primary=True,
            verified=True,
        )

        self.challenge1 = Challenge.objects.create(
            title="Test Challenge1",
            short_description="Short description for test challenge1",
            description="Description for test challenge1",
            terms_and_conditions="Terms and conditions for test challenge1",
            submission_guidelines="Submission guidelines for test challenge1",
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
        )

        self.star_challenge = StarChallenge.objects.create(
            user=self.user, challenge=self.challenge, is_starred=True
        )
        self.client.force_authenticate(user=self.user)

    def test_star_challenge_when_challenge_does_not_exist(self):
        self.url = reverse_lazy(
            "challenges:star_challenge",
            kwargs={"challenge_pk": self.challenge.pk + 10},
        )

        expected = {
            "detail": f"Challenge {self.challenge.pk + 10} does not exist"
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_challenge_when_user_has_starred(self):
        self.url = reverse_lazy(
            "challenges:star_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        expected = {
            "user": self.user.pk,
            "challenge": self.challenge.pk,
            "count": 1,
            "is_starred": True,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_user_hasnt_starred(self):
        self.url = reverse_lazy(
            "challenges:star_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.client.force_authenticate(user=self.user2)
        expected = {"is_starred": False, "count": 1}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_no_user_has_starred_or_unstarred_it(self):
        self.url = reverse_lazy(
            "challenges:star_challenge",
            kwargs={"challenge_pk": self.challenge1.pk},
        )
        expected = {"is_starred": False, "count": 0}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unstar_challenge(self):
        self.url = reverse_lazy(
            "challenges:star_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.star_challenge.is_starred = False
        expected = {
            "user": self.user.pk,
            "challenge": self.challenge.pk,
            "count": 0,
            "is_starred": self.star_challenge.is_starred,
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_star_challenge(self):
        self.url = reverse_lazy(
            "challenges:star_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        self.star_challenge.delete()
        expected = {
            "user": self.user.pk,
            "challenge": self.challenge.pk,
            "count": 1,
            "is_starred": True,
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class GetChallengePhaseByPkTest(BaseChallengePhaseClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_by_pk",
            kwargs={"pk": self.challenge_phase.pk},
        )

    def test_get_challenge_phase_by_pk(self):
        expected = {
            "id": self.challenge_phase.id,
            "name": self.challenge_phase.name,
            "description": self.challenge_phase.description,  # noqa: C0301
            "leaderboard_public": self.challenge_phase.leaderboard_public,  # noqa: C0301
            "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(  # noqa: C0301
                "+00:00", ""
            ),
            "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(  # noqa: C0301
                "+00:00", ""
            ),
            "challenge": self.challenge_phase.challenge.pk,
            "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,  # noqa: C0301
            "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
            "max_submissions": self.challenge_phase.max_submissions,
            "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
            "is_public": self.challenge_phase.is_public,
            "is_active": True,
            "codename": self.challenge_phase.codename,
            "slug": self.challenge_phase.slug,
            "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
            "submission_meta_attributes": None,
            "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
            "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
            "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,  # noqa: C0301
            "allowed_email_ids": self.challenge_phase.allowed_email_ids,
            "is_submission_public": self.challenge_phase.is_submission_public,
            "disable_logs": self.challenge_phase.disable_logs,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_phase_by_pk_if_pk_does_not_exist(self):
        self.url = reverse_lazy(
            "challenges:get_challenge_phase_by_pk",
            kwargs={"pk": self.challenge_phase.pk + 2},
        )
        expected = {
            "detail": f"ChallengePhase {self.challenge_phase.pk + 2} does not exist"  # noqa: C0301
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetChallengePhasesByChallengePkTest(BaseChallengePhaseClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:get_challenge_phases_by_challenge_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )

        self.user1 = User.objects.create(
            username="someuser1",
            email="user1@test.com",
            password="secret_psassword",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@test.com",
            primary=True,
            verified=True,
        )

    def test_get_challenge_phases_by_challenge_pk(self):
        expected = [
            {
                "id": self.private_challenge_phase.id,
                "name": self.private_challenge_phase.name,
                "description": self.private_challenge_phase.description,
                "leaderboard_public": self.private_challenge_phase.leaderboard_public,  # noqa: C0301
                "start_date": f"{self.private_challenge_phase.start_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "end_date": f"{self.private_challenge_phase.end_date.isoformat()}Z".replace(
                    "+00:00", ""
                ),
                "challenge": self.private_challenge_phase.challenge.pk,
                "max_submissions_per_day": self.private_challenge_phase.max_submissions_per_day,  # noqa: C0301
                "max_submissions_per_month": self.private_challenge_phase.max_submissions_per_month,  # noqa: C0301
                "max_submissions": self.private_challenge_phase.max_submissions,  # noqa: C0301
                "max_concurrent_submissions_allowed": self.private_challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
                "is_public": self.private_challenge_phase.is_public,
                "is_active": True,
                "is_submission_public": self.private_challenge_phase.is_submission_public,  # noqa: C0301
                "annotations_uploaded_using_cli": self.private_challenge_phase.annotations_uploaded_using_cli,  # noqa: C0301
                "codename": self.private_challenge_phase.codename,
                "test_annotation": f"http://testserver{self.private_challenge_phase.test_annotation.url}",  # noqa: C0301
                "slug": self.private_challenge_phase.slug,
                "environment_image": self.private_challenge_phase.environment_image,  # noqa: C0301
                "is_restricted_to_select_one_submission": self.private_challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
                "submission_meta_attributes": None,
                "is_partial_submission_evaluation_enabled": self.private_challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
                "config_id": None,
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
                "default_submission_meta_attributes": self.private_challenge_phase.default_submission_meta_attributes,  # noqa: C0301
                "allowed_email_ids": self.challenge_phase.allowed_email_ids,
                "disable_logs": self.private_challenge_phase.disable_logs,
            },
            {
                "id": self.challenge_phase.id,
                "name": self.challenge_phase.name,
                "description": self.challenge_phase.description,
                "leaderboard_public": self.challenge_phase.leaderboard_public,
                "start_date": f"{self.challenge_phase.start_date.isoformat()}Z".replace(  # noqa: C0301
                    "+00:00", ""
                ),
                "end_date": f"{self.challenge_phase.end_date.isoformat()}Z".replace(  # noqa: C0301
                    "+00:00", ""
                ),
                "challenge": self.challenge_phase.challenge.pk,
                "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,  # noqa: C0301
                "max_submissions_per_month": self.challenge_phase.max_submissions_per_month,  # noqa: C0301
                "max_submissions": self.challenge_phase.max_submissions,
                "max_concurrent_submissions_allowed": self.challenge_phase.max_concurrent_submissions_allowed,  # noqa: C0301
                "is_public": self.challenge_phase.is_public,
                "is_active": True,
                "is_submission_public": self.challenge_phase.is_submission_public,  # noqa: C0301
                "annotations_uploaded_using_cli": self.challenge_phase.annotations_uploaded_using_cli,  # noqa: C0301
                "codename": self.challenge_phase.codename,
                "test_annotation": f"http://testserver{self.challenge_phase.test_annotation.url}",  # noqa: C0301
                "slug": self.challenge_phase.slug,
                "environment_image": self.challenge_phase.environment_image,
                "is_restricted_to_select_one_submission": self.challenge_phase.is_restricted_to_select_one_submission,  # noqa: C0301
                "submission_meta_attributes": None,
                "is_partial_submission_evaluation_enabled": self.challenge_phase.is_partial_submission_evaluation_enabled,  # noqa: C0301
                "config_id": None,
                "allowed_submission_file_types": self.challenge_phase.allowed_submission_file_types,  # noqa: C0301
                "default_submission_meta_attributes": self.challenge_phase.default_submission_meta_attributes,  # noqa: C0301
                "allowed_email_ids": self.challenge_phase.allowed_email_ids,
                "disable_logs": self.challenge_phase.disable_logs,
            },
        ]
        response = self.client.get(self.url, {})
        actual_sorted = sorted(response.data, key=lambda x: x["id"])
        expected_sorted = sorted(expected, key=lambda x: x["id"])
        self.assertEqual(actual_sorted, expected_sorted)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_phases_by_challenge_pk_when_challenge_does_not_exist(  # noqa: C0301
        self,
    ):
        self.url = reverse_lazy(
            "challenges:get_challenge_phases_by_challenge_pk",
            kwargs={"challenge_pk": self.challenge.pk + 10},
        )

        expected = {
            "detail": f"Challenge {self.challenge.pk + 10} does not exist"  # noqa: C0301
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_challenge_phases_by_challenge_pk_when_user_is_not_challenge_host(  # noqa: C0301
        self,
    ):
        """
        This is the case in which a user is not a challenge host
        """
        self.client.force_authenticate(user=self.user1)
        expected = {
            "error": "Sorry, you are not authorized to access these challenge phases."  # noqa: C0301
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetAWSCredentialsForParticipantTeamTest(BaseChallengePhaseClass):
    def setUp(self):
        super().setUp()
        self.url = reverse_lazy(
            "challenges:star_challenge",
            kwargs={"challenge_pk": self.challenge.pk},
        )

        self.user1 = User.objects.create(
            username="otheruser1",
            password="other_secret_password",
            email="user1@test.com",
        )

        self.user2 = User.objects.create(
            username="otheruser2",
            password="other_secret_password",
            email="user2@test.com",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@test.com",
            primary=True,
            verified=True,
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@test.com",
            primary=True,
            verified=True,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge8", created_by=self.user1
        )

        self.participant1 = Participant.objects.create(
            user=self.user1,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )
        self.challenge.participant_teams.add(self.participant_team)
        self.client.force_authenticate(user=self.user1)
        self.challenge.is_docker_based = True
        self.challenge.save()

    def test_get_aws_credentials_when_challenge_is_not_docker_based(self):
        self.challenge.is_docker_based = False
        self.challenge.save()

        self.url = reverse_lazy(
            "challenges:get_aws_credentials_for_participant_team",
            kwargs={"phase_pk": self.challenge_phase.pk},
        )
        expected = {"error": "Sorry, this is not a docker based challenge."}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_aws_credentials_when_not_participated(self):
        self.url = reverse_lazy(
            "challenges:get_aws_credentials_for_participant_team",
            kwargs={"phase_pk": self.challenge_phase.pk},
        )
        expected = {"error": "You have not participated in this challenge."}
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_get_aws_credentials(self):
        self.url = reverse_lazy(
            "challenges:get_aws_credentials_for_participant_team",
            kwargs={"phase_pk": self.challenge_phase.pk},
        )
        response = self.client.get(self.url, {})
        data = response.data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Check if all fields for cli exists
        self.assertTrue("federated_user" in data["success"])
        self.assertTrue("docker_repository_uri" in data["success"])
        federated_user = data["success"]["federated_user"]
        self.assertTrue("AccessKeyId" in federated_user["Credentials"])
        self.assertTrue("SecretAccessKey" in federated_user["Credentials"])
        self.assertTrue("SessionToken" in federated_user["Credentials"])


@mock_s3
class PresignedURLAnnotationTest(BaseChallengePhaseClass):
    @mock.patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_get_annotation_presigned_url(self, mock_get_aws_creds):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_annotation_file_presigned_url",
                kwargs={"challenge_phase_pk": self.challenge_phase.pk},
            )
        )

        expected = {
            "presigned_urls": [
                {
                    "partNumber": 1,
                    "url": "https://test-bucket.s3.amazonaws.com/media/annotation_files/",  # noqa: C0301
                }
            ]
        }

        self.client.force_authenticate(user=self.challenge_host.user)
        mock_get_aws_creds.return_value = {
            "AWS_ACCESS_KEY_ID": "dummy-key",
            "AWS_SECRET_ACCESS_KEY": "dummy-access-key",
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_REGION": "us-east-1",
        }
        client = boto3.client("s3")
        client.create_bucket(Bucket="test-bucket")

        num_file_chunks = 1
        response = self.client.post(
            self.url,
            data={
                "num_file_chunks": num_file_chunks,
                "file_name": "media/submissions/dummy.txt",
            },
        )
        self.assertEqual(
            len(response.data["presigned_urls"]),
            len(expected["presigned_urls"]),
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(MEDIA_ROOT="/tmp/evalai")
    @mock.patch("challenges.utils.get_aws_credentials_for_challenge")
    def test_finish_annotation_file_upload(self, mock_get_aws_creds):
        # Create a annotation using multipart upload
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_annotation_file_presigned_url",
                kwargs={"challenge_phase_pk": self.challenge_phase.pk},
            )
        )

        self.client.force_authenticate(user=self.challenge_host.user)
        mock_get_aws_creds.return_value = {
            "AWS_ACCESS_KEY_ID": "dummy-key",
            "AWS_SECRET_ACCESS_KEY": "dummy-access-key",
            "AWS_STORAGE_BUCKET_NAME": "test-bucket",
            "AWS_REGION": "us-east-1",
        }
        client = boto3.client("s3")
        client.create_bucket(Bucket="test-bucket")

        num_file_chunks = 1
        response = self.client.post(
            self.url,
            data={
                "num_file_chunks": num_file_chunks,
                "file_name": "media/submissions/dummy.txt",
            },
        )

        expected = {
            "upload_id": response.data["upload_id"],
            "challenge_phase_pk": self.challenge_phase.pk,
        }

        # Upload submission in parts to mocked S3 bucket
        parts = []

        presigned_url_object = response.data["presigned_urls"][0]
        part = presigned_url_object["partNumber"]
        url = presigned_url_object["url"]
        file_data = self.challenge_phase.test_annotation.read()

        response = requests.put(url, data=file_data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

        etag = response.headers["ETag"]
        parts.append({"ETag": etag, "PartNumber": part})

        # Finish multipart upload
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:finish_annotation_file_upload",
                kwargs={"challenge_phase_pk": self.challenge_phase.pk},
            )
        )

        response = self.client.post(
            self.url,
            data={
                "parts": json.dumps(parts),
                "upload_id": expected["upload_id"],
            },
        )

        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class TestAllowedEmailIds(BaseChallengePhaseClass):
    def test_get_or_update_allowed_email_ids_success(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_or_update_allowed_email_ids",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "phase_pk": self.challenge_phase.pk,
                },
            )
        )
        expected = {
            "allowed_email_ids": self.challenge_phase.allowed_email_ids,
        }
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_or_update_allowed_email_ids_patch_success(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_or_update_allowed_email_ids",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "phase_pk": self.challenge_phase.pk,
                },
            )
        )
        expected = ["user1@example.com", "user2@example.com"]
        expected.extend(self.challenge_phase.allowed_email_ids)
        allowed_email_ids = ["user1@example.com", "user2@example.com"]
        data = {
            "allowed_email_ids": allowed_email_ids,
        }
        response = self.client.patch(self.url, data)
        self.assertCountEqual(response.data["allowed_email_ids"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_or_update_allowed_email_ids_delete_success(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_or_update_allowed_email_ids",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "phase_pk": self.challenge_phase.pk,
                },
            )
        )
        allowed_email_ids = ["user1@example.com", "user2@example.com"]
        data = {
            "allowed_email_ids": allowed_email_ids,
        }
        self.client.patch(self.url, data)
        expected = {
            "allowed_email_ids": self.challenge_phase.allowed_email_ids,
        }
        response = self.client.delete(self.url, data)
        self.assertCountEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_allowed_email_ids_with_invalid_input(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_or_update_allowed_email_ids",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "phase_pk": self.challenge_phase.pk,
                },
            )
        )
        allowed_email_ids = "user1@example.com"
        data = {
            "allowed_email_ids": allowed_email_ids,
        }
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Field allowed_email_ids should be a list."
        )

    def test_update_allowed_email_ids_when_input_is_none(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_or_update_allowed_email_ids",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "phase_pk": self.challenge_phase.pk,
                },
            )
        )
        data = {
            "allowed_email_ids": None,
        }
        response = self.client.patch(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "Field allowed_email_ids is missing."
        )

    def test_get_allowed_email_ids_when_challenge_phase_does_not_exist(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_or_update_allowed_email_ids",
                kwargs={
                    "challenge_pk": self.challenge.pk,
                    "phase_pk": self.challenge_phase.pk + 1000,
                },
            )
        )
        expected = {
            "error": f"Challenge phase {self.challenge_phase.pk + 1000} does not exist for challenge {self.challenge.pk}"  # noqa: C0301
        }
        response = self.client.get(self.url, {}, json)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_allowed_email_ids_when_challange_does_not_exist(self):
        self.url = (  # pylint: disable=attribute-defined-outside-init
            reverse_lazy(
                "challenges:get_or_update_allowed_email_ids",
                kwargs={
                    "challenge_pk": self.challenge.pk + 1000,
                    "phase_pk": self.challenge_phase.pk,
                },
            )
        )
        response = self.client.get(self.url, {}, json)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ChallengeSendApprovalRequestTest(BaseAPITestClass):

    @responses.activate
    def test_request_challenge_approval_when_challenge_has_finished_submissions(  # noqa: C0301
        self,
    ):
        responses.add(
            responses.POST,
            settings.APPROVAL_WEBHOOK_URL,
            body=b"ok",
            status=200,
            content_type="text/plain",
        )

        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "message": "Approval request sent! You should also receive an email with subscription plan details."  # noqa: C0301
            },
        )
        self.assertEqual(
            response.data,
            {
                "message": "Approval request sent! You should also receive an email with subscription plan details."  # noqa: C0301
            },
        )

    def test_request_challenge_approval_when_challenge_has_unfinished_submissions(  # noqa: C0301
        self,
    ):
        # pylint: disable=attribute-defined-outside-init
        self.user1 = User.objects.create(
            username="otheruser1",
            password="other_secret_password",
            email="user1@test.com",
        )

        EmailAddress.objects.create(
            user=self.user1,
            email="user1@test.com",
            primary=True,
            verified=True,
        )

        self.participant_team1 = ParticipantTeam.objects.create(  # pylint: disable=attribute-defined-outside-init
            team_name="Participant Team for Challenge8", created_by=self.user1
        )

        self.participant1 = Participant.objects.create(  # pylint: disable=attribute-defined-outside-init
            user=self.user1,
            status=Participant.ACCEPTED,
            team=self.participant_team1,
        )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(  # pylint: disable=attribute-defined-outside-init
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
            )

        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(
            response.data,
            {
                "error": "The following challenge phases do not have finished submissions: Challenge Phase"  # noqa: C0301
            },
        )

    @responses.activate
    @mock.patch("challenges.views.send_subscription_plans_email")
    @mock.patch("challenges.views.logger")
    def test_request_challenge_approval_with_successful_subscription_email(
        self, mock_logger, mock_send_email
    ):
        """Test that subscription plans email is sent successfully during approval request"""  # noqa: C0301
        responses.add(
            responses.POST,
            settings.APPROVAL_WEBHOOK_URL,
            body=b"ok",
            status=200,
            content_type="text/plain",
        )

        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(url)

        # Verify email function was called with correct challenge
        mock_send_email.assert_called_once_with(self.challenge)

        # Verify success logging
        mock_logger.info.assert_any_call(
            f"Subscription plans email sent successfully for challenge {self.challenge.pk}"  # noqa: C0301
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "message": "Approval request sent! You should also receive an email with subscription plan details."  # noqa: C0301
            },
        )

    @responses.activate
    @mock.patch("challenges.views.send_subscription_plans_email")
    @mock.patch("challenges.views.logger")
    def test_request_challenge_approval_with_email_failure_continues_approval(
        self, mock_logger, mock_send_email
    ):
        """Test that approval process continues even if email sending fails"""
        responses.add(
            responses.POST,
            settings.APPROVAL_WEBHOOK_URL,
            body=b"ok",
            status=200,
            content_type="text/plain",
        )

        # Make email sending fail
        mock_send_email.side_effect = Exception("Email service unavailable")

        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(url)

        # Verify email function was called
        mock_send_email.assert_called_once_with(self.challenge)

        # Verify error logging
        mock_logger.error.assert_any_call(
            f"Failed to send subscription plans email for challenge {self.challenge.pk}: Email service unavailable"  # noqa: C0301
        )

        # Verify approval process continues despite email failure
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(
            response.data,
            {
                "message": "Approval request sent! You should also receive an email with subscription plan details."  # noqa: C0301
            },
        )

    @responses.activate
    @mock.patch("challenges.views.send_subscription_plans_email")
    def test_request_challenge_approval_challenge_not_found(
        self, mock_send_email
    ):
        """Test that email is not sent when challenge doesn't exist"""
        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": 99999},  # Non-existent challenge
        )
        response = self.client.get(url)

        # Verify email function was not called for non-existent challenge
        mock_send_email.assert_not_called()

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @responses.activate
    @mock.patch("challenges.views.send_subscription_plans_email")
    def test_request_challenge_approval_user_not_host(self, mock_send_email):
        """Test that email is not sent when user is not challenge host"""
        # Create a different user who is not a challenge host
        other_user = User.objects.create(
            username="otheruser",
            password="other_password",
            email="other@test.com",
        )
        EmailAddress.objects.create(
            user=other_user,
            email="other@test.com",
            primary=True,
            verified=True,
        )

        # Authenticate as the other user
        self.client.force_authenticate(user=other_user)

        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(url)

        # Verify email function was not called for unauthorized user
        mock_send_email.assert_not_called()

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @responses.activate
    @mock.patch("challenges.views.send_subscription_plans_email")
    def test_request_challenge_approval_webhook_failure_after_email_success(
        self, mock_send_email
    ):
        """Test that email is sent even if webhook fails later"""
        responses.add(
            responses.POST,
            settings.APPROVAL_WEBHOOK_URL,
            body=b"error",  # Simulate webhook failure
            status=200,
            content_type="text/plain",
        )

        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(url)

        # Verify email function was called despite webhook failure
        mock_send_email.assert_called_once_with(self.challenge)

        # Webhook failure should result in error response
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertIn("error", response.data)

    @responses.activate
    @mock.patch("challenges.views.send_subscription_plans_email")
    def test_request_challenge_approval_with_smtp_error(self, mock_send_email):
        """Test handling of SMTP-specific errors during email sending"""
        responses.add(
            responses.POST,
            settings.APPROVAL_WEBHOOK_URL,
            body=b"ok",
            status=200,
            content_type="text/plain",
        )

        # Simulate SMTP error
        mock_send_email.side_effect = SMTPException(
            "SMTP server not available"
        )

        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(url)

        # Verify email function was called
        mock_send_email.assert_called_once_with(self.challenge)

        # Approval should continue despite SMTP error
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @responses.activate
    @mock.patch("challenges.views.send_subscription_plans_email")
    def test_request_challenge_approval_email_integration_with_challenge_phases(  # noqa: C0301
        self, mock_send_email
    ):
        """Test email integration with challenge that has multiple phases"""
        # Create additional challenge phase
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            additional_phase = ChallengePhase.objects.create(
                name="Additional Phase",
                description="Description for Additional Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file2.txt",
                    b"Dummy file content 2",
                    content_type="text/plain",
                ),
            )

        # Create a finished submission for the additional phase to satisfy the submission check  # noqa: C0301
        # Ensure participant team is associated with the challenge and user is a participant  # noqa: C0301
        self.challenge.participant_teams.add(self.participant_team)
        Participant.objects.get_or_create(
            user=self.user,
            team=self.participant_team,
            defaults={"status": Participant.ACCEPTED},
        )

        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=additional_phase,
            created_by=self.user,
            status="submitted",  # Start with submitted status
            input_file=SimpleUploadedFile(
                "test_input.txt", b"test input", content_type="text/plain"
            ),
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        # Manually update the status to finished after creation to bypass any automatic processing  # noqa: C0301
        submission.status = "finished"
        submission.save()

        responses.add(
            responses.POST,
            settings.APPROVAL_WEBHOOK_URL,
            body=b"ok",
            status=200,
            content_type="text/plain",
        )

        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(url)

        # Verify email function was called with the challenge
        mock_send_email.assert_called_once_with(self.challenge)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @responses.activate
    @mock.patch("challenges.views.send_subscription_plans_email")
    def test_request_challenge_approval_email_not_sent_when_submissions_incomplete(  # noqa: C0301
        self, mock_send_email
    ):
        """Test that email is not sent when submission check fails"""
        # Create a challenge phase without finished submissions
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            ChallengePhase.objects.create(
                name="Unfinished Phase",
                description="Description for Unfinished Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_unfinished_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
            )

        url = reverse_lazy(
            "challenges:request_challenge_approval_by_pk",
            kwargs={"challenge_pk": self.challenge.pk},
        )
        response = self.client.get(url)

        # Email should NOT be sent when submission check fails
        mock_send_email.assert_not_called()

        # The request should fail due to unfinished submissions
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertIn(
            "do not have finished submissions", response.data["error"]
        )


class CreateOrUpdateGithubChallengeTest(
    APITestCase
):  # pylint: disable=attribute-defined-outside-init,too-many-instance-attributes
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="host", email="host@test.com", password="secret_password"
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        with open(
            join(
                settings.BASE_DIR, "examples", "example1", "test_zip_file.zip"
            ),
            "rb",
        ) as zip_file:
            self.test_zip_file = SimpleUploadedFile(
                zip_file.name,
                zip_file.read(),
                content_type="application/zip",
            )

        self.input_zip_file = SimpleUploadedFile(
            "test_sample.zip",
            b"Dummy File Content",
            content_type="application/zip",
        )

        self.client.force_authenticate(user=self.user)

    def test_create_challenge_using_github_when_challenge_host_team_does_not_exist(  # noqa: C0301
        self,
    ):
        self.url = reverse_lazy(
            "challenges:create_or_update_github_challenge",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk + 10
            },
        )
        expected = {
            "detail": f"ChallengeHostTeam {self.challenge_host_team.pk + 10} does not exist"  # noqa: C0301
        }
        response = self.client.post(
            self.url,
            {
                "GITHUB_REPOSITORY": "https://github.com/yourusername/repository",  # noqa: C0301
                "zip_configuration": self.input_zip_file,
            },
            format="multipart",
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_challenge_using_github_when_user_is_not_authenticated(
        self,
    ):
        self.url = reverse_lazy(
            "challenges:create_or_update_github_challenge",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )
        self.client.force_authenticate(user=None)
        expected = {"error": "Authentication credentials were not provided."}
        response = self.client.post(self.url, {})
        self.assertEqual(list(response.data.values())[0], expected["error"])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_challenge_using_github_success(self):
        self.url = reverse_lazy(
            "challenges:create_or_update_github_challenge",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )

        with mock.patch("challenges.views.requests.get") as m:
            resp = mock.Mock()
            resp.content = self.test_zip_file.read()
            resp.status_code = 200
            m.return_value = resp
            response = self.client.post(
                self.url,
                {
                    "GITHUB_REPOSITORY": "https://github.com/yourusername/repository",  # noqa: C0301
                    "zip_configuration": self.input_zip_file,
                },
                format="multipart",
            )
            expected = {
                "Success": "Challenge Challenge Title has been created successfully and sent for review to EvalAI Admin."  # noqa: C0301
            }

            self.assertEqual(response.status_code, 201)
            self.assertEqual(response.json(), expected)
        self.assertEqual(Challenge.objects.count(), 1)
        self.assertEqual(DatasetSplit.objects.count(), 1)
        self.assertEqual(Leaderboard.objects.count(), 1)
        self.assertEqual(ChallengePhaseSplit.objects.count(), 1)

        # Verify github_repository is properly stored
        challenge = Challenge.objects.first()
        self.assertEqual(
            challenge.github_repository,
            "https://github.com/yourusername/repository",
        )

    def test_update_challenge_using_github_reuses_existing_challenge_config(
        self,
    ):
        """Test that updating an existing challenge via GitHub push
        updates the existing ChallengeConfiguration instead of
        creating a new one.
        """
        self.url = reverse_lazy(
            "challenges:create_or_update_github_challenge",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )
        github_repository = "https://github.com/yourusername/repository"

        # First push - create challenge
        with mock.patch("challenges.views.requests.get") as m:
            resp = mock.Mock()
            resp.content = self.test_zip_file.read()
            resp.status_code = 200
            m.return_value = resp
            response = self.client.post(
                self.url,
                {
                    "GITHUB_REPOSITORY": github_repository,
                    "zip_configuration": self.input_zip_file,
                },
                format="multipart",
            )
            self.assertEqual(response.status_code, 201)

        # Verify challenge and ChallengeConfiguration were created
        challenge = Challenge.objects.get(github_repository=github_repository)
        initial_challenge_configs = ChallengeConfiguration.objects.filter(
            challenge=challenge.pk
        )
        self.assertEqual(initial_challenge_configs.count(), 1)
        initial_challenge_config = initial_challenge_configs.first()
        initial_challenge_config_pk = initial_challenge_config.pk

        # Create ChallengeHost so user is recognized as a host of the challenge
        # This is needed for the update request to pass the permission check
        ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        # Second push - update challenge
        # Reset zip file for second read
        self.zip_file.seek(0)
        test_zip_file_2 = SimpleUploadedFile(
            self.zip_file.name,
            self.zip_file.read(),
            content_type="application/zip",
        )
        with mock.patch("challenges.views.requests.get") as m:
            resp = mock.Mock()
            resp.content = test_zip_file_2.read()
            resp.status_code = 200
            m.return_value = resp
            response = self.client.post(
                self.url,
                {
                    "GITHUB_REPOSITORY": github_repository,
                    "zip_configuration": self.input_zip_file,
                },
                format="multipart",
            )
            self.assertEqual(response.status_code, 200)
            expected = {
                "Success": (
                    "The challenge Challenge Title has been updated successfully"
                )
            }
            self.assertEqual(response.json(), expected)

        # Verify that there's still only one ChallengeConfiguration
        # and it's the same one (updated, not a new one)
        updated_challenge_configs = ChallengeConfiguration.objects.filter(
            challenge=challenge.pk
        )
        self.assertEqual(updated_challenge_configs.count(), 1)
        updated_challenge_config = updated_challenge_configs.first()
        # Verify it's the same ChallengeConfiguration object (same pk)
        self.assertEqual(
            initial_challenge_config_pk, updated_challenge_config.pk
        )


class ValidateChallengeTest(
    APITestCase
):  # pylint: disable=attribute-defined-outside-init,too-many-instance-attributes
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="host", email="host@test.com", password="secret_password"
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        with open(
            join(
                settings.BASE_DIR, "examples", "example1", "test_zip_file.zip"
            ),
            "rb",
        ) as zip_file:
            self.test_zip_file = SimpleUploadedFile(
                zip_file.name,
                zip_file.read(),
                content_type="application/zip",
            )
        with open(
            join(
                settings.BASE_DIR,
                "examples",
                "example3",
                "incorrect_zip_file.zip",
            ),
            "rb",
        ) as zip_incorect_file:
            self.test_zip_incorrect_file = SimpleUploadedFile(
                zip_incorect_file.name,
                zip_incorect_file.read(),
                content_type="application/zip",
            )

        self.input_zip_file = SimpleUploadedFile(
            "test_sample.zip",
            b"Dummy File Content",
            content_type="application/zip",
        )

        self.client.force_authenticate(user=self.user)

    def test_validate_challenge_using_success(self):
        self.url = reverse_lazy(
            "challenges:validate_challenge_config",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )

        with mock.patch("challenges.views.requests.get") as m:
            resp = mock.Mock()
            resp.content = self.test_zip_file.read()
            resp.status_code = 200
            m.return_value = resp
            response = self.client.post(
                self.url,
                {
                    "GITHUB_REPOSITORY": "https://github.com/yourusername/repository",  # noqa: C0301
                    "GITHUB_BRANCH_NAME": "refs/heads/challenge",
                    "zip_configuration": self.input_zip_file,
                },
                format="multipart",
            )
            expected = {
                "Success": "The challenge config has been validated successfully"  # noqa: C0301
            }

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), expected)

    def test_validate_challenge_using_failure(self):
        self.maxDiff = None  # pylint: disable=attribute-defined-outside-init
        self.url = reverse_lazy(
            "challenges:validate_challenge_config",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )

        with mock.patch("challenges.views.requests.get") as m:
            resp = mock.Mock()
            resp.content = self.test_zip_incorrect_file.read()
            resp.status_code = 200

            m.return_value = resp
            response = self.client.post(
                self.url,
                {
                    "GITHUB_REPOSITORY": "https://github.com/yourusername/repository",  # noqa: C0301
                    "zip_configuration": self.input_zip_file,
                },
                format="multipart",
            )
            expected = {
                "error": "Please add the challenge title\n"
                "Please add the challenge description\n"
                "Please add the evaluation details\n"
                "Please add the terms and conditions.\n"
                "Please add the submission guidelines.\n"
                "ERROR: There is no key for the evaluation script in the YAML file. Please add it and then try again!\n"  # noqa: C0301
                "ERROR: Please add the start_date and end_date.\n"  # noqa: C0301
                "ERROR: The 'default_order_by' value 'aa' in the schema for the leaderboard with ID: 1 is not a valid label.\n"  # noqa: C0301
                "ERROR: No codename found for the challenge phase. Please add a codename and try again!\n"  # noqa: C0301
                " ERROR: There is no key for description in phase Dev Phase.\n"  # noqa: C0301
                "ERROR: Please add the start_date and end_date in challenge phase 1.\n"  # noqa: C0301
                "ERROR: Please enter the following fields for the submission meta attribute in challenge phase 1: description, type\n"  # noqa: C0301
                "ERROR: Challenge phase 1 has the following schema errors:\n"  # noqa: C0301
                " {'description': [ErrorDetail(string='This field is required.', code='required')], 'max_submissions_per_month': [ErrorDetail(string='This field may not be null.', code='null')]}\n"  # noqa: C0301
                "ERROR: Invalid leaderboard id 1 found in challenge phase split 1.\n"  # noqa: C0301
                "ERROR: Invalid phased id 1 found in challenge phase split 1.\n"  # noqa: C0301
                "ERROR: Invalid leaderboard id 1 found in challenge phase split 2.\n"  # noqa: C0301
                "ERROR: Invalid leaderboard id 1 found in challenge phase split 3."  # noqa: C0301
            }

            self.assertEqual(response.status_code, 400)
            self.assertEqual(response.json(), expected)


class TestLeaderboardData(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.url = None
        self.challenge_phase = ChallengePhase.objects.create(
            name="Challenge Phase",
            description="Description for Challenge Phase",
            leaderboard_public=False,
            is_public=True,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            challenge=self.challenge,
            test_annotation=SimpleUploadedFile(
                "test_sample_file.txt",
                b"Dummy file content",
                content_type="text/plain",
            ),
        )

        self.leaderboard = Leaderboard.objects.create(
            schema=json.dumps(
                {
                    "labels": ["yes/no", "number", "others", "overall"],
                    "default_order_by": "overall",
                }
            )
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=SimpleUploadedFile(
                "test_sample_file.txt",
                b"Dummy file content",
                content_type="text/plain",
            ),
            method_name="Test Method 1",
            method_description="Test Description 1",
            project_url="http://testserver1/",
            publication_url="http://testserver1/",
            is_public=True,
            is_flagged=True,
        )

        self.dataset_split = DatasetSplit.objects.create(
            name="Test Dataset Split", codename="test-split"
        )

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            dataset_split=self.dataset_split,
            challenge_phase=self.challenge_phase,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC,
            leaderboard_decimal_precision=2,
            is_leaderboard_order_descending=True,
            show_leaderboard_by_latest_submission=False,
        )

        self.leaderboard_data = LeaderboardData.objects.create(
            challenge_phase_split=self.challenge_phase_split,
            submission=self.submission,
            leaderboard=self.leaderboard,
            result=[0.5, 0.6, 0.7, 0.8],
            error="",
        )
        self.user.is_staff = True
        self.user.save()

    def test_get_leaderboard_data_success(self):
        self.url = reverse_lazy(
            "challenges:get_leaderboard_data",
            kwargs={"challenge_phase_split_pk": self.challenge_phase_split.pk},
        )
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_leaderboard_data_when_not_staff(self):
        self.url = reverse_lazy(
            "challenges:get_leaderboard_data",
            kwargs={"challenge_phase_split_pk": self.challenge_phase_split.pk},
        )
        self.user.is_staff = False
        self.user.save()
        expected = {
            "error": "Sorry, you are not authorized to access this resource!"
        }
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_modify_leaderboard_data_when_not_staff(self):
        self.url = reverse_lazy("challenges:modify_leaderboard_data")
        self.user.is_staff = False
        self.user.save()
        expected = {
            "error": "Sorry, you are not authorized to access this resource!"
        }
        response = self.client.put(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_modify_leaderboard_data_success(self):
        self.url = reverse_lazy("challenges:modify_leaderboard_data")
        data = {"leaderboard_data": self.leaderboard_data.pk, "is_disabled": 0}
        expected = {"message": "Leaderboard data updated successfully!"}
        response = self.client.put(self.url, data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_modify_leaderboard_data_with_other_parameters(self):
        self.url = reverse_lazy("challenges:modify_leaderboard_data")
        data = {
            "leaderboard": self.leaderboard.pk,
            "challenge_phase_split": self.challenge_phase_split.pk,
            "submission": self.submission.pk,
            "is_disabled": 0,
        }
        expected = {"message": "Leaderboard data updated successfully!"}
        response = self.client.put(self.url, data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestUpdateChallengeApproval(BaseAPITestClass):
    def setUp(self):
        settings.AWS_SES_REGION_NAME = "us-east-1"
        settings.AWS_SES_REGION_ENDPOINT = "email.us-east-1.amazonaws.com"
        super().setUp()
        self.url = None

    def test_update_challenge_approval_when_challenge_exists(self):
        self.user.is_staff = True
        self.user.save()
        self.url = reverse_lazy("challenges:update_challenge_approval")
        expected = {"message": "Challenge updated successfully!"}
        response = self.client.post(
            self.url,
            {"challenge_pk": self.challenge.pk, "approved_by_admin": True},
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_challenge_approval_when_not_a_staff(self):
        self.url = reverse_lazy("challenges:update_challenge_approval")
        self.user.is_staff = False
        self.user.save()
        expected = {
            "error": "Sorry, you are not authorized to access this resource!"
        }
        response = self.client.post(
            self.url,
            {"challenge_pk": self.challenge.pk, "approved_by_admin": True},
        )
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class TestUpdateChallengeAttributes(BaseAPITestClass):
    def setUp(self):
        settings.AWS_SES_REGION_NAME = "us-east-1"
        settings.AWS_SES_REGION_ENDPOINT = "email.us-east-1.amazonaws.com"
        super().setUp()
        self.url = None

    def test_update_challenge_attributes_when_challenge_exists(self):
        self.url = reverse_lazy("challenges:update_challenge_attributes")
        self.user.is_staff = True
        self.user.save()

        expected = {
            "message": f"Challenge attributes updated successfully for challenge with primary key {self.challenge.pk}!"  # noqa: C0301
        }

        response = self.client.post(
            self.url,
            {
                "challenge_pk": self.challenge.pk,
                "title": "Updated Title",
                "description": "Updated Description",
                "approved_by_admin": True,
                "ephemeral_storage": 25,
            },
        )

        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_challenge_attributes_when_not_a_staff(self):
        self.url = reverse_lazy("challenges:update_challenge_attributes")
        self.user.is_staff = False
        self.user.save()
        expected = {
            "error": "Sorry, you are not authorized to access this resource!"
        }

        response = self.client.post(
            self.url,
            {
                "challenge_pk": self.challenge.pk,
                "title": "Updated Title",
                "description": "Updated Description",
                "approved_by_admin": True,
                "ephemeral_storage": 25,
            },
        )

        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
