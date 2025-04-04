import mock
import boto3
import os

from unittest import TestCase

from moto import mock_ecs
from datetime import timedelta
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from http import HTTPStatus

from rest_framework.test import APITestCase, APIClient

from hosts.models import ChallengeHost, ChallengeHostTeam

import challenges.aws_utils as aws_utils
from challenges.models import Challenge, ChallengePhase


class BaseTestClass(APITestCase):
    def setUp(self):
        aws_utils.COMMON_SETTINGS_DICT["EXECUTION_ROLE_ARN"] = "arn:aws:iam::us-east-1:012345678910:role/ecsTaskExecutionRole"

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
            published=False,
            is_registration_open=True,
            enable_forum=True,
            queue="test_queue",
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
        )
        self.challenge.slug = "{}-{}".format(
            self.challenge.title.replace(" ", "-").lower(), self.challenge.pk
        )[:199]
        self.challenge.save()

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )
        self.challenge2 = Challenge.objects.create(
            title="Test Challenge 2",
            creator=self.challenge_host_team,
            queue="test_queue_2",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
            )
            self.challenge_phase2 = ChallengePhase.objects.create(
                name="Challenge Phase 2",
                description="Description for Challenge Phase",
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge2,
            )

        self.client.force_authenticate(user=self.user)
        self.ecs_client = boto3.client("ecs", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"), aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"), aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),)


class TestClientTokenGen(TestCase):
    def test_client_token_gen(self):
        response = aws_utils.client_token_generator()
        self.assertTrue(all(ord(c) < 128 for c in response))


@mock_ecs
class TestRegisterTaskDefinition(BaseTestClass):
    def setUp(self):
        super(TestRegisterTaskDefinition, self).setUp()

    def test_register_task_def_by_challenge_pk_for_new_challenge(self):
        queue_name = self.challenge.queue
        expected_arn = "arn:aws:ecs:us-east-1:012345678910:task-definition/test_queue:1"
        expected_status_code = HTTPStatus.OK
        response = aws_utils.register_task_def_by_challenge_pk(self.ecs_client, queue_name, self.challenge)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        arn = response["taskDefinition"]["taskDefinitionArn"]
        self.assertEqual(arn, expected_arn)
        self.assertEqual(status_code, expected_status_code)

    def test_register_task_def_by_challenge_pk_for_existing_service(self):
        queue_name = self.challenge2.queue
        aws_utils.register_task_def_by_challenge_pk(self.ecs_client, queue_name, self.challenge2)
        expected_status_code = HTTPStatus.BAD_REQUEST
        expected_error_message = "Error. Task definition already registered for challenge {}.".format(self.challenge2.pk)
        response = aws_utils.register_task_def_by_challenge_pk(self.ecs_client, queue_name, self.challenge2)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        error_message = response["Error"]
        self.assertEqual(expected_error_message, error_message)
        self.assertEqual(status_code, expected_status_code)

    def test_register_task_def_by_challenge_pk_for_empty_execution_role_arn(self):
        aws_utils.COMMON_SETTINGS_DICT["EXECUTION_ROLE_ARN"] = ""
        queue_name = self.challenge2.queue
        expected_status_code = HTTPStatus.BAD_REQUEST
        expected_error_message = "Please ensure that the TASK_EXECUTION_ROLE_ARN is appropriately passed as an environment varible."
        response = aws_utils.register_task_def_by_challenge_pk(self.ecs_client, queue_name, self.challenge2)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        error_message = response["Error"]
        self.assertEqual(expected_error_message, error_message)
        self.assertEqual(status_code, expected_status_code)


@mock_ecs
class TestCreateService(BaseTestClass):
    def setUp(self):
        super(TestCreateService, self).setUp()

    def test_create_service_by_challenge_pk_for_new_challenge(self):
        client_token = "abc123"
        self.ecs_client.create_cluster(clusterName="cluster")
        expected_status_code = HTTPStatus.OK
        expected_num = 1
        response = aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, client_token)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        self.assertEqual(status_code, expected_status_code)
        self.assertEqual(self.challenge.workers, expected_num)
        self.assertTrue(self.challenge.task_def_arn)

    def test_create_service_by_challenge_pk_for_existing_service(self):
        client_token = "abc123"
        self.ecs_client.create_cluster(clusterName="cluster")
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, client_token)
        client_token = "abcd1234"
        expected_status_code = HTTPStatus.BAD_REQUEST
        expected_error_message = "Worker service for challenge {} already exists. Please scale, stop or delete.".format(self.challenge.pk)
        response = aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, client_token)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        error_message = response["Error"]
        self.assertEqual(expected_error_message, error_message)
        self.assertEqual(status_code, expected_status_code)


@mock_ecs
class TestUpdateService(BaseTestClass):
    def setUp(self):
        super(TestUpdateService, self).setUp()

    def test_update_service_by_challenge_pk_successfully(self):
        client_token = "abc123"
        num_of_tasks = 2
        self.ecs_client.create_cluster(clusterName="cluster")
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, client_token)
        self.ecs_client = boto3.client("ecs")
        expected_status_code = HTTPStatus.OK
        response = aws_utils.update_service_by_challenge_pk(self.ecs_client, self.challenge, num_of_tasks)
        status_code = response["ResponseMetadata"]["HTTPStatusCode"]
        self.assertEqual(status_code, expected_status_code)
        self.assertEqual(self.challenge.workers, num_of_tasks)

    def test_update_service_by_challenge_pk_for_non_existent_service(self):
        num_of_tasks = 2
        response = aws_utils.update_service_by_challenge_pk(self.ecs_client, self.challenge2, num_of_tasks)
        self.assertEqual(response["Error"]["Code"], "ServiceNotFoundException")


class TestServiceManager(BaseTestClass):
    def setUp(self):
        super(TestServiceManager, self).setUp()

    @mock.patch("challenges.aws_utils.client_token_generator")
    @mock.patch("challenges.aws_utils.create_service_by_challenge_pk")
    def test_service_manager_for_new_challenge(self, mock_create, mock_token_gen):
        mock_token_gen.return_value = "abc123"
        client_token = "abc123"
        aws_utils.service_manager(self.ecs_client, self.challenge)
        mock_create.assert_called_with(self.ecs_client, self.challenge, client_token)

    @mock_ecs
    @mock.patch("challenges.aws_utils.update_service_by_challenge_pk")
    def test_service_manager_for_active_challenge(self, mock_update):
        num_of_tasks = 3
        client_token = "abc123"
        self.ecs_client.create_cluster(clusterName="cluster")
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, client_token)
        aws_utils.service_manager(self.ecs_client, self.challenge2, num_of_tasks=num_of_tasks)
        mock_update.assert_called_with(self.ecs_client, self.challenge2, num_of_tasks, False)


@mock_ecs
class BaseAdminCallsClass(BaseTestClass):
    def setUp(self):
        super(BaseAdminCallsClass, self).setUp()

        self.challenge3 = Challenge.objects.create(
            title="Test Challenge 3",
            creator=self.challenge_host_team,
            queue="test_queue_3",
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )
        self.ecs_client.create_cluster(clusterName="cluster")
        self.client_token = "abc123"

    @classmethod
    def queryset(cls, pklist):
        queryset = Challenge.objects.filter(pk__in=pklist)
        queryset = sorted(queryset, key=lambda i: pklist.index(i.pk))
        return queryset


class TestStartWorkers(BaseAdminCallsClass):
    def setUp(self):
        super(TestStartWorkers, self).setUp()

    def test_start_workers_when_first_and_third_challenges_have_zero_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)
        self.challenge.workers = 0
        self.challenge.save()
        self.challenge3.workers = 0
        self.challenge3.save()
        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestStartWorkers, self).queryset(pklist)
        expected_count = 2
        expected_num_of_workers = [1, 1, 1]
        expected_message = "Please select challenge with inactive workers only."
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge2.pk}]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.start_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

        Challenge.objects.filter(pk=self.challenge2.pk).update(workers=0)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestStartWorkers, self).queryset(pklist)
        expected_count = 1
        expected_message = "Please select challenge with inactive workers only."
        expected_failures = [
            {"message": expected_message, "challenge_pk": self.challenge.pk},
            {"message": expected_message, "challenge_pk": self.challenge3.pk},
        ]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.start_workers(queryset)
        self.assertEqual(response, expected_response)

    def test_start_workers_for_all_new_challenges_with_no_worker_service(self):
        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestStartWorkers, self).queryset(pklist)
        expected_count = 3
        expected_failures = []
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.start_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertTrue(all(c.workers == 1 for c in queryset))


class TestStopWorkers(BaseAdminCallsClass):
    def setUp(self):
        super(TestStopWorkers, self).setUp()

    def test_stop_workers_when_first_challenge_has_zero_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)
        Challenge.objects.filter(pk=self.challenge.pk).update(workers=0)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestStopWorkers, self).queryset(pklist)
        expected_count = 2
        expected_num_of_workers = [0, 0, 0]
        expected_message = "Please select challenges with active workers only."
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge.pk}]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.stop_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    def test_stop_workers_for_all_challenge_workers_active(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestStopWorkers, self).queryset(pklist)
        expected_count = 3
        expected_failures = []
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.stop_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertTrue(all(c.workers == 0 for c in queryset))

    def test_stop_workers_where_second_and_third_challenges_are_new_with_no_worker_service(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestStopWorkers, self).queryset(pklist)
        expected_count = 1
        expected_num_of_workers = [0, None, None]
        expected_message = "Please select challenges with active workers only."
        expected_failures = [
            {"message": expected_message, "challenge_pk": self.challenge2.pk},
            {"message": expected_message, "challenge_pk": self.challenge3.pk},
        ]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.stop_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)


class TestScaleWorkers(BaseAdminCallsClass):
    def setUp(self):
        super(TestScaleWorkers, self).setUp()

    def test_scale_workers_when_third_challenge_is_new_with_no_worker_service(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestScaleWorkers, self).queryset(pklist)
        num_of_tasks = self.challenge2.workers + 3
        expected_count = 2
        expected_num_of_workers = [num_of_tasks, num_of_tasks, None]
        expected_message = "Please start worker(s) before scaling."
        expected_failures = [
            {"message": expected_message, "challenge_pk": self.challenge3.pk},
        ]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.scale_workers(queryset, num_of_tasks)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    def test_scale_workers_when_second_challenge_is_scaled_to_same_number_of_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)
        pklist = [self.challenge2.pk]
        queryset = super(TestScaleWorkers, self).queryset(pklist)
        num_of_tasks = 3
        self.challenge2.workers = 3
        self.challenge2.save()

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestScaleWorkers, self).queryset(pklist)
        num_of_tasks = self.challenge2.workers
        expected_count = 2
        expected_message = "Please scale to a different number. Challenge has {} worker(s).".format(num_of_tasks)
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge2.pk}]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.scale_workers(queryset, num_of_tasks)
        self.assertEqual(response, expected_response)


class TestDeleteWorkers(BaseAdminCallsClass):

    def test_delete_workers_when_all_challenges_have_active_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestDeleteWorkers, self).queryset(pklist)

        expected_count = 3
        expected_num_of_workers = [None, None, None]
        expected_failures = []
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.delete_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    def test_delete_workers_when_second_challenge_has_no_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestDeleteWorkers, self).queryset(pklist)

        expected_count = 2
        expected_num_of_workers = [None, None, None]
        expected_message = "Please select challenges with active workers only."
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge2.pk}]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.delete_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    @mock.patch("challenges.aws_utils.delete_service_by_challenge_pk")
    def test_delete_worker_exception_message(self, mock_delete_by_pk):
        message = "Test error message."
        test_exception_dict = {"Error": message, "ResponseMetadata": {"HTTPStatusCode": HTTPStatus.NOT_FOUND}}
        mock_delete_by_pk.return_value = test_exception_dict

        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestDeleteWorkers, self).queryset(pklist)

        expected_count = 0
        expected_message = "Test error message."
        expected_failures = [
            {"message": expected_message, "challenge_pk": self.challenge.pk},
            {"message": expected_message, "challenge_pk": self.challenge2.pk},
            {"message": expected_message, "challenge_pk": self.challenge3.pk},
        ]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.delete_workers(queryset)
        self.assertEqual(response, expected_response)
        expected_num_of_workers = [1, 1, 1]
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)


class TestRestartWorkers(BaseAdminCallsClass):

    def test_restart_workers_when_all_challenges_have_active_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestRestartWorkers, self).queryset(pklist)

        expected_count = 3
        expected_num_of_workers = [1, 1, 1]
        expected_failures = []
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.restart_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    def test_restart_workers_when_first_challenge_has_zero_workers(self):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)
        aws_utils.scale_workers([self.challenge], 0)

        pklist = [self.challenge.pk, self.challenge2.pk, self.challenge3.pk]
        queryset = super(TestRestartWorkers, self).queryset(pklist)

        expected_count = 2
        expected_num_of_workers = [0, 1, 1]
        expected_message = "Please select challenges with active workers only."
        expected_failures = [{"message": expected_message, "challenge_pk": self.challenge.pk}]
        expected_response = {"count": expected_count, "failures": expected_failures}
        response = aws_utils.restart_workers(queryset)
        self.assertEqual(response, expected_response)
        self.assertEqual(list(c.workers for c in queryset), expected_num_of_workers)

    @mock.patch("challenges.aws_utils.restart_workers")
    def test_restart_workers_signal_callback_evaluation_script(self, mock_restart_workers):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge3, self.client_token)

        self.challenge.evaluation_script = SimpleUploadedFile(
            "test_sample_file_changer.zip",
            b"Dummy content.",
            content_type="zip",
        )
        self.challenge.save()

        mock_restart_workers.assert_called_with([self.challenge])

    @mock.patch("challenges.aws_utils.restart_workers")
    def test_restart_workers_signal_callback_test_annotation(self, mock_restart_workers):
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge, self.client_token)
        aws_utils.create_service_by_challenge_pk(self.ecs_client, self.challenge2, self.client_token)

        self.challenge_phase.test_annotation = SimpleUploadedFile(
            "test_sample_annotation1.txt",
            b"Dummy content 1.",
            content_type="text/plain",
        )
        self.challenge_phase.save()
        self.challenge_phase2.test_annotation = SimpleUploadedFile(
            "test_sample_annotation2.txt",
            b"Dummy content 2.",
            content_type="text/plain",
        )
        self.challenge_phase2.save()

        mock_call_args = mock_restart_workers.call_args_list
        mock_call_1 = mock.call([self.challenge])
        mock_call_2 = mock.call([self.challenge2])
        self.assertEqual(mock_call_args, [mock_call_1, mock_call_2])
