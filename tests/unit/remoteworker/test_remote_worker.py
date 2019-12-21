import mock

from unittest import TestCase

from django.contrib.auth.models import User

from scripts.workers.remote_submission_worker import (
    make_request,
    get_message_from_sqs_queue,
    delete_message_from_sqs_queue,
    get_submission_by_pk,
    get_challenge_phases_by_challenge_pk,
    get_challenge_by_queue_name,
    get_challenge_phase_by_pk,
    update_submission_data,
    update_submission_status,
    return_url_per_environment,
    load_challenge,
)
from challenges.models import Challenge, ChallengePhase


class BaseTestClass(TestCase):
    def setUp(self):
        self.submission_pk = 1
        self.challenge_pk = 1
        self.challenge_phase_pk = 1
        self.data = {"test": "data"}
        self.headers = {"Authorization": "Token test_token"}
        self.queue_name = "evalai_submission_queue"

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


@mock.patch("scripts.workers.remote_submission_worker.get_challenge_by_queue_name")
@mock.patch("scripts.workers.remote_submission_worker.create_dir_as_python_package")
@mock.patch("scripts.workers.remote_submission_worker.extract_challenge_data")
class LoadChallengeTestClass(BaseTestClass):
    def setUp(self):
        super(LoadChallengeTestClass, self).setUp()
        self.user = User(
            username='someuser',
            email="user@test.com",
            password='secret_password')

        self.challenge_host_team = ChallengeHostTeam(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.challenge = Challenge(
            id=self.challenge_pk,
            title='Test Challenge',
            description='Description for test challenge',
            terms_and_conditions='Terms and conditions for test challenge',
            submission_guidelines='Submission guidelines for test challenge',
            creator=self.challenge_host_team,
            published=True,
            approved_by_admin=True,
            enable_forum=True,
            anonymous_leaderboard=False)

        self.challenge_phase = ChallengePhase(
            id=self.challenge_phase_pk,
            name='Challenge Phase',
            description='Description for Challenge Phase',
            leaderboard_public=False,
            is_public=True,
            challenge=self.challenge)

        self.phases = [self.challenge_phase]

        self.queue_name_patcher = mock.patch(
            "scripts.workers.remote_submission_worker.QUEUE_NAME", "evalai_submission_queue"
        )
        self.queue_name_patcher.start()

    def tearDown(self):
        self.queue_name_patcher.stop()
        # super(LoadChallengeTestClass, self).tearDown()  # FUTURE

    @mock.patch("scripts.workers.remote_submission_worker.get_challenge_phases_by_challenge_pk")
    def test_load_challenge_success(self, mock_get_phases_by_challenge_pk, mock_extract_challenge_data,
                                    mock_create_dir_as_python_package, mock_get_challenge_by_queue_name):
        mock_get_challenge_by_queue_name.return_value = self.challenge
        mock_get_phases_by_challenge_pk.return_value = self.phases
        load_challenge()
        mock_get_phases_by_challenge_pk.assert_called_with(self.challenge_pk)
        mock_extract_challenge_data.assert_called_with(self.challenge, self.phases)

    @mock.patch("scripts.workers.remote_submission_worker.logger")
    def test_load_challenge_when_challenge_doesnt_exist(self, mock_logger, mock_extract_challenge_data,
                                                        mock_create_dir_as_python_package,
                                                        mock_get_challenge_by_queue_name):
        mock_get_challenge_by_queue_name.side_effect = Exception
        with self.assertRaises(Exception):
            load_challenge()
        mock_logger.assert_called_with("Challenge with queue name %s does not exists" % (self.queue_name))
        mock_extract_challenge_data.assert_not_called()
