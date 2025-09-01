import logging
from unittest.mock import Mock, patch

from challenges.github_interface import GithubInterface
from challenges.github_utils import (
    github_challenge_phase_sync,
    github_challenge_sync,
)
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHostTeam


class TestGithubInterface(TestCase):
    """Test cases for GithubInterface class"""

    def setUp(self):
        self.token = "test_token"
        self.repo = "test/repo"
        self.branch = "master"
        self.github = GithubInterface(self.repo, self.branch, self.token)

    def test_init(self):
        """Test GithubInterface initialization"""
        self.assertEqual(self.github.GITHUB_AUTH_TOKEN, self.token)
        self.assertEqual(self.github.GITHUB_REPOSITORY, self.repo)
        self.assertEqual(self.github.BRANCH, self.branch)
        headers = self.github.get_request_headers()
        self.assertIn("Authorization", headers)

    def test_get_github_url(self):
        """Test get_github_url method"""
        url = "/test/path"
        expected = "https://api.github.com/test/path"
        result = self.github.get_github_url(url)
        self.assertEqual(result, expected)

    @patch("challenges.github_interface.requests.request")
    def test_get_content_from_path_success(self, mock_request):
        """Test get_content_from_path with successful response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": "test content"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = self.github.get_content_from_path("test.json")

        self.assertEqual(result, {"content": "test content"})
        mock_request.assert_called_once()

    @patch("challenges.github_interface.requests.request")
    def test_get_content_from_path_not_found(self, mock_request):
        """Test get_content_from_path with error response returns None"""
        from requests.exceptions import RequestException

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RequestException()
        mock_request.return_value = mock_response

        result = self.github.get_content_from_path("test.json")

        self.assertIsNone(result)

    @patch("challenges.github_interface.GithubInterface.get_content_from_path")
    @patch("challenges.github_interface.requests.request")
    def test_update_content_from_path_success(self, mock_request, mock_get):
        """Test update_content_from_path with successful response"""
        # Simulate existing file with sha so update path is used
        mock_get.return_value = {"sha": "old_sha"}
        mock_response = Mock()
        mock_response.json.return_value = {"sha": "new_sha"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = self.github.update_content_from_path(
            "test.json", "Y29udGVudA==", changed_field="title"
        )

        self.assertEqual(result, {"sha": "new_sha"})
        mock_request.assert_called_once()

    @patch("challenges.github_interface.requests.request")
    def test_update_content_from_path_failure(self, mock_request):
        """Test update_content_from_path with failed response returns None"""
        from requests.exceptions import RequestException

        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RequestException()
        mock_request.return_value = mock_response

        result = self.github.update_content_from_path(
            "test.json", "Y29udGVudA==", changed_field="title"
        )

        self.assertIsNone(result)

    @patch(
        "challenges.github_interface.GithubInterface.update_content_from_path"
    )
    def test_update_data_from_path_encodes_and_calls_update(self, mock_update):
        """update_data_from_path should base64-encode and call update_content_from_path"""
        mock_update.return_value = {"sha": "new_sha"}
        text = "hello"
        result = self.github.update_data_from_path(
            "test.json", text, changed_field="title"
        )

        self.assertEqual(result, {"sha": "new_sha"})
        mock_update.assert_called_once()


class TestGithubSync(TestCase):
    """Test cases for GitHub sync functionality"""

    def setUp(self):
        # Create a test challenge with GitHub configuration
        self.user = User.objects.create(
            username="owner", email="o@example.com"
        )
        self.host_team = ChallengeHostTeam.objects.create(
            team_name="team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Test Description",
            github_token="test_token",
            github_repository="test/repo",
            github_branch="master",
            creator=self.host_team,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
        )

        # Create a test challenge phase
        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            description="Test Phase Description",
            challenge=self.challenge,
            codename="test_phase",
        )

    @patch("challenges.github_utils.GithubInterface")
    def test_sync_challenge_to_github_success(self, mock_github_class):
        """Test successful challenge sync to GitHub"""
        mock_github = Mock()
        mock_github_class.return_value = mock_github
        mock_github.update_challenge_config.return_value = True

        github_challenge_sync(self.challenge.id, changed_field="title")

        mock_github_class.assert_called_once_with(
            "test/repo", "master", "test_token"
        )
        mock_github.update_challenge_config.assert_called_once()

    def test_sync_challenge_to_github_no_token(self):
        """Test challenge sync when no GitHub token is configured"""
        self.challenge.github_token = ""
        with self.assertLogs(level=logging.WARNING):
            github_challenge_sync(self.challenge.id, changed_field="title")

    def test_sync_challenge_to_github_no_repo(self):
        """Test challenge sync when no GitHub repository is configured"""
        self.challenge.github_repository = ""
        with self.assertLogs(level=logging.WARNING):
            github_challenge_sync(self.challenge.id, changed_field="title")

    @patch("challenges.github_utils.GithubInterface")
    def test_sync_challenge_phase_to_github_success(self, mock_github_class):
        """Test successful challenge phase sync to GitHub"""
        mock_github = Mock()
        mock_github_class.return_value = mock_github
        mock_github.update_challenge_phase_config.return_value = True

        github_challenge_phase_sync(
            self.challenge_phase.id, changed_field="name"
        )

        mock_github_class.assert_called_once_with(
            "test/repo", "master", "test_token"
        )
        mock_github.update_challenge_phase_config.assert_called_once()

    def test_sync_challenge_phase_to_github_no_token(self):
        """Test challenge phase sync when no GitHub token is configured"""
        self.challenge.github_token = ""
        with self.assertLogs(level=logging.WARNING):
            github_challenge_phase_sync(
                self.challenge_phase.id, changed_field="name"
            )

    def test_sync_challenge_phase_to_github_no_repo(self):
        """Test challenge phase sync when no GitHub repository is configured"""
        self.challenge.github_repository = ""
        with self.assertLogs(level=logging.WARNING):
            github_challenge_phase_sync(
                self.challenge_phase.id, changed_field="name"
            )

    @patch("challenges.github_utils.GithubInterface")
    def test_sync_challenge_calls_update(self, mock_github_class):
        """Basic check that challenge sync invokes update method"""
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        github_challenge_sync(self.challenge.id, changed_field="title")
        mock_github.update_challenge_config.assert_called_once()

    @patch("challenges.github_utils.GithubInterface")
    def test_sync_challenge_phase_calls_update(self, mock_github_class):
        """Basic check that challenge phase sync invokes update method"""
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        github_challenge_phase_sync(
            self.challenge_phase.id, changed_field="name"
        )
        mock_github.update_challenge_phase_config.assert_called_once()
