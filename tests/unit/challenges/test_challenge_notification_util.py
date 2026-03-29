from unittest.mock import MagicMock
from unittest.mock import patch as mockpatch

from challenges.challenge_notification_util import (
    construct_and_send_eks_cluster_creation_mail,
    construct_and_send_worker_start_mail,
)
from rest_framework.test import APITestCase


class TestChallengeNotificationUtil(APITestCase):
    @mockpatch("challenges.challenge_notification_util.settings")
    def test_construct_and_send_worker_start_mail_debug_returns_early(
        self, mock_settings
    ):
        mock_settings.DEBUG = True
        mock_challenge = MagicMock()
        construct_and_send_worker_start_mail(mock_challenge)

    @mockpatch("challenges.challenge_notification_util.settings")
    def test_construct_and_send_worker_start_mail_no_email_sent(
        self, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_challenge = MagicMock()
        mock_challenge.pk = 1
        construct_and_send_worker_start_mail(mock_challenge)

    @mockpatch("challenges.challenge_notification_util.settings")
    def test_construct_and_send_eks_cluster_creation_mail_debug_returns_early(
        self, mock_settings
    ):
        mock_settings.DEBUG = True
        mock_challenge = MagicMock()
        construct_and_send_eks_cluster_creation_mail(mock_challenge)

    @mockpatch("challenges.challenge_notification_util.settings")
    def test_construct_and_send_eks_cluster_creation_mail_no_email_sent(
        self, mock_settings
    ):
        mock_settings.DEBUG = False
        mock_challenge = MagicMock()
        mock_challenge.pk = 1
        construct_and_send_eks_cluster_creation_mail(mock_challenge)
