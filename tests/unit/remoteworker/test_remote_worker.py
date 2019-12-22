import mock
import os
import shutil

from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework.test import APITestCase

from participants.models import Participant

from scripts.workers.remote_submission_worker import (
    make_request,
    get_message_from_sqs_queue,
    delete_message_from_sqs_queue,
    get_submission_by_pk,
    get_challenge_phases_by_challenge_pk,
    get_challenge_by_queue_name,
    get_challenge_phase_by_pk,
    process_submission_message,
    update_submission_data,
    update_submission_status,
    return_url_per_environment,
)


class BaseTestClass(APITestCase):
    def setUp(self):
        self.submission_pk = 1
        self.challenge_pk = 1
        self.challenge_phase_pk = 1
        self.data = {"test": "data"}
        self.headers = {"Authorization": "Token test_token"}

    def make_request_url(self):
        return "/test/url"

    def get_message_from_sqs_queue_url(self, queue_name):
        return "/api/jobs/challenge/queues/{}/".format(queue_name)

    def delete_message_from_sqs_queue_url(self, queue_name, receipt_handle):
        return "/api/jobs/queues/{}/receipt/{}/".format(queue_name, receipt_handle)

    def get_submission_by_pk_url(self, submission_pk):
        return "/api/jobs/submission/{}".format(submission_pk)

    def get_challenge_phases_by_challenge_pk_url(self, challenge_pk):
        return "/api/challenges/{}/phases/".format(challenge_pk)

    def get_challenge_by_queue_name_url(self, queue_name):
        return "/api/challenges/challenge/queues/{}/".format(queue_name)

    def get_challenge_phase_by_pk_url(self, challenge_pk, challenge_phase_pk):
        return "/api/challenges/challenge/{}/challenge_phase/{}".format(challenge_pk, challenge_phase_pk)

    def update_submission_data_url(self, challenge_pk):
        return "/api/jobs/challenge/{}/update_submission/".format(challenge_pk)


@mock.patch("scripts.workers.remote_submission_worker.AUTH_TOKEN", "test_token")
@mock.patch("scripts.workers.remote_submission_worker.requests")
class MakeRequestTestClass(BaseTestClass):
    def setUp(self):
        super(MakeRequestTestClass, self).setUp()
        self.url = super(MakeRequestTestClass, self).make_request_url()

    def test_make_request_get(self, mock_make_request):
        make_request(self.url, "GET")
        mock_make_request.get.assert_called_with(url=self.url, headers=self.headers)

    def test_make_request_put(self, mock_make_request):
        make_request(self.url, "PUT", data=self.data)
        mock_make_request.put.assert_called_with(url=self.url, headers=self.headers, data=self.data)

    def test_make_request_patch(self, mock_make_request):
        make_request(self.url, "PATCH", data=self.data)
        mock_make_request.patch.assert_called_with(url=self.url, headers=self.headers, data=self.data)


@mock.patch("scripts.workers.remote_submission_worker.QUEUE_NAME", "evalai_submission_queue")
@mock.patch("scripts.workers.remote_submission_worker.return_url_per_environment")
@mock.patch("scripts.workers.remote_submission_worker.make_request")
class APICallsTestClass(BaseTestClass):

    def test_get_message_from_sqs_queue(self, mock_make_request, mock_url):
        url = self.get_message_from_sqs_queue_url("evalai_submission_queue")
        get_message_from_sqs_queue()
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_delete_message_from_sqs_queue(self, mock_make_request, mock_url):
        test_receipt_handle = "MbZj6wDWli+JvwwJaBV+3dcjk2YW2vA3+STFFljTM8tJJg6HRG6PYSasuWXPJB+Cw"
        url = self.delete_message_from_sqs_queue_url("evalai_submission_queue", test_receipt_handle)
        delete_message_from_sqs_queue(test_receipt_handle)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_by_queue_name(self, mock_make_request, mock_url):
        url = self.get_challenge_by_queue_name_url("evalai_submission_queue")
        get_challenge_by_queue_name()
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_submission_by_pk(self, mock_make_request, mock_url):
        get_submission_by_pk(self.submission_pk)
        url = self.get_submission_by_pk_url(self.submission_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phases_by_challenge_pk(self, mock_make_request, mock_url):
        get_challenge_phases_by_challenge_pk(self.challenge_pk)
        url = self.get_challenge_phases_by_challenge_pk_url(self.challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_get_challenge_phase_by_pk(self, mock_make_request, mock_url):
        get_challenge_phase_by_pk(self.challenge_pk, self.challenge_phase_pk)
        url = self.get_challenge_phase_by_pk_url(self.challenge_pk, self.challenge_phase_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "GET")

    def test_update_submission_data(self, mock_make_request, mock_url):
        update_submission_data(self.data, self.challenge_pk, self.submission_pk)
        url = self.update_submission_data_url(self.challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PUT", data=self.data)

    def test_update_submission_status(self, mock_make_request, mock_url):
        update_submission_status(self.data, self.challenge_pk)
        url = self.update_submission_data_url(self.challenge_pk)
        mock_url.assert_called_with(url)
        url = mock_url(url)
        mock_make_request.assert_called_with(url, "PATCH", data=self.data)


@mock.patch("scripts.workers.remote_submission_worker.DJANGO_SERVER_PORT", "80")
@mock.patch("scripts.workers.remote_submission_worker.DJANGO_SERVER", "testserver")
class URLFormatTestCase(BaseTestClass):

    def test_return_url_per_environment(self):
        url = "/test/url"
        expected_url = "http://testserver:80{}".format(url)
        returned_url = return_url_per_environment(url)
        self.assertEqual(returned_url, expected_url)


class ProcessSubmissionMessage(BaseTestClass):
    def setUp(self):
        super(ProcessSubmissionMessage, self).setUp()

        self.user = {
            "username": "username",
            "email": "user@test.com",
            "password": "secret_password"
        }

        self.challenge_host_team = {
            "team_name": "Test Challenge Host Team",
            "created_by": self.user
        }

        self.participant_team = {
            "team_name": "Participant Team for Challenge",
            "created_by": self.user
        }

        self.participant = {
            "user": self.user,
            "status": Participant.SELF,
            "team": self.participant_team
        }

        self.challenge = {
            "id": self.challenge_pk,
            "title": "Test Challenge",
            "creator": self.challenge_host_team,
        }

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = {
                "id": self.challenge_phase_pk,
                "name": "Challenge Phase",
                "description": "Description for Challenge Phase",
                "leaderboard_public": False,
                "is_public": True,
                "challenge": self.challenge,
                "test_annotation": SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain"
                )
            }

        self.submission = {
            "id": self.submission_pk,
            "participant_team": self.participant_team,
            "challenge_phase": self.challenge_phase,
            "created_by": self.challenge_host_team["created_by"],
            "status": "submitted",
            "input_file": SimpleUploadedFile(
                "user_annotation_file.txt",
                b"Dummy file content",
                content_type="text/plain"
            ),
            "method_name": "Test Method",
            "method_description": "Test Description",
            "project_url": "http://testserver",
            "publication_url": "http://testserver",
            "is_public": True
        }

    def tearDown(self):
        try:
            shutil.rmtree("/tmp/evalai")
        except OSError:
            pass

    @mock.patch("scripts.workers.remote_submission_worker.extract_submission_data")
    def test_process_submission_message_when_submission_does_not_exist(self, mock_esd):
        self.submission_pk += 1
        message = {
            "challenge_pk": self.challenge_pk,
            "phase_pk": self.challenge_phase_pk,
            "submission_pk": self.submission_pk
        }
        mock_esd.return_value = None

        process_submission_message(message)
        self.assertEqual(process_submission_message(message), None)

    @mock.patch("scripts.workers.remote_submission_worker.extract_submission_data")
    @mock.patch("scripts.workers.remote_submission_worker.get_challenge_by_queue_name")
    @mock.patch("scripts.workers.remote_submission_worker.get_challenge_phase_by_pk")
    @mock.patch("scripts.workers.remote_submission_worker.logger.exception")
    def test_process_submission_message_when_challenge_phase_does_not_exist(self, mock_esd,
                                                                            mock_get_challenge_by_queue_name,
                                                                            mock_get_challenge_phase_by_pk,
                                                                            mock_logger):
        self.challenge_phase_pk += 1
        message = {
            "challenge_pk": self.challenge_pk,
            "phase_pk": self.challenge_phase_pk,
            "submission_pk": self.submission_pk
        }
        mock_esd.return_value = self.submission
        mock_get_challenge_by_queue_name.return_value = self.challenge
        mock_get_challenge_phase_by_pk.return_value = None

        with self.assertRaises(Exception):
            process_submission_message(message)
            mock_logger.assert_called_with("Challenge Phase {} does not exist".format(self.challenge_phase_pk))
