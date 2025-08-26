import json
import logging
from unittest.mock import Mock, patch

from challenges.github_utils import (
    GithubInterface,
    sync_challenge_phase_to_github,
    sync_challenge_to_github,
)
from challenges.models import Challenge, ChallengePhase
from django.test import TestCase
from django.utils import timezone


class TestGithubInterface(TestCase):
    """Test cases for GithubInterface class"""

    def setUp(self):
        self.token = "test_token"
        self.repo = "test/repo"
        self.branch = "master"
        self.github = GithubInterface(self.token, self.repo, self.branch)

    def test_init(self):
        """Test GithubInterface initialization"""
        self.assertEqual(self.github.token, self.token)
        self.assertEqual(self.github.repo, self.repo)
        self.assertEqual(self.github.branch, self.branch)
        self.assertEqual(self.github.base_url, "https://api.github.com")
        self.assertIn("Authorization", self.github.headers)
        self.assertIn("Accept", self.github.headers)

    def test_get_github_url(self):
        """Test get_github_url method"""
        url = "/test/path"
        expected = "https://api.github.com/test/path"
        result = self.github.get_github_url(url)
        self.assertEqual(result, expected)

    @patch("challenges.github_utils.requests.get")
    def test_get_file_contents_success(self, mock_get):
        """Test get_file_contents with successful response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"content": "test content"}
        mock_get.return_value = mock_response

        result = self.github.get_file_contents("test.json")

        self.assertEqual(result, {"content": "test content"})
        mock_get.assert_called_once()

    @patch("challenges.github_utils.requests.get")
    def test_get_file_contents_not_found(self, mock_get):
        """Test get_file_contents with 404 response"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = self.github.get_file_contents("test.json")

        self.assertIsNone(result)

    @patch("challenges.github_utils.requests.put")
    def test_update_text_file_success(self, mock_put):
        """Test update_text_file with successful response"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"sha": "test_sha"}
        mock_put.return_value = mock_response

        result = self.github.update_text_file(
            "test.json", "content", "message", "sha"
        )

        self.assertEqual(result, {"sha": "test_sha"})
        mock_put.assert_called_once()

    @patch("challenges.github_utils.requests.put")
    def test_update_text_file_failure(self, mock_put):
        """Test update_text_file with failure response"""
        mock_response = Mock()
        mock_response.status_code = 400
        mock_put.return_value = mock_response

        result = self.github.update_text_file(
            "test.json", "content", "message", "sha"
        )

        self.assertIsNone(result)

    @patch("challenges.github_utils.GithubInterface.get_file_contents")
    @patch("challenges.github_utils.GithubInterface.update_text_file")
    def test_update_json_if_changed_existing_changed(
        self, mock_update_text, mock_get
    ):
        """When existing JSON differs, it should commit with updated content"""
        old_data = {"a": 1}
        old_text = json.dumps(old_data, sort_keys=True)
        mock_get.return_value = {
            "sha": "test_sha",
            "content": old_text.encode("utf-8").decode("utf-8"),
        }  # content will be base64-decoded internally; provide as raw for simplicity
        mock_update_text.return_value = {"sha": "new_sha"}

        new_data = {"a": 2}
        result = self.github.update_json_if_changed("test.json", new_data)

        self.assertEqual(result, {"sha": "new_sha"})
        mock_get.assert_called_once_with("test.json")
        mock_update_text.assert_called_once()

    @patch("challenges.github_utils.GithubInterface.get_file_contents")
    @patch("challenges.github_utils.GithubInterface.update_text_file")
    def test_update_json_if_changed_new_file(self, mock_update_text, mock_get):
        """When file doesn't exist, it should create it"""
        mock_get.return_value = None
        mock_update_text.return_value = {"sha": "new_sha"}

        data = {"test": "data"}
        result = self.github.update_json_if_changed("test.json", data)

        self.assertEqual(result, {"sha": "new_sha"})
        mock_get.assert_called_once_with("test.json")
        mock_update_text.assert_called_once()


class TestGithubSync(TestCase):
    """Test cases for GitHub sync functionality"""

    def setUp(self):
        # Create a test challenge with GitHub configuration
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Test Description",
            github_token="test_token",
            github_repository="test/repo",
            github_branch="master",
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
        mock_github.update_json_if_changed.return_value = {"sha": "test_sha"}

        sync_challenge_to_github(self.challenge)

        mock_github_class.assert_called_once_with(
            "test_token", "test/repo", "master"
        )
        mock_github.update_json_if_changed.assert_called_once()

    def test_sync_challenge_to_github_no_token(self):
        """Test challenge sync when no GitHub token is configured"""
        self.challenge.github_token = ""

        with self.assertLogs(level=logging.WARNING):
            sync_challenge_to_github(self.challenge)

    def test_sync_challenge_to_github_no_repo(self):
        """Test challenge sync when no GitHub repository is configured"""
        self.challenge.github_repository = ""

        with self.assertLogs(level=logging.WARNING):
            sync_challenge_to_github(self.challenge)

    @patch("challenges.github_utils.GithubInterface")
    def test_sync_challenge_phase_to_github_success(self, mock_github_class):
        """Test successful challenge phase sync to GitHub"""
        mock_github = Mock()
        mock_github_class.return_value = mock_github
        mock_github.update_json_if_changed.return_value = {"sha": "test_sha"}

        sync_challenge_phase_to_github(self.challenge_phase)

        mock_github_class.assert_called_once_with(
            "test_token", "test/repo", "master"
        )
        mock_github.update_json_if_changed.assert_called_once()

    def test_sync_challenge_phase_to_github_no_token(self):
        """Test challenge phase sync when no GitHub token is configured"""
        self.challenge.github_token = ""

        with self.assertLogs(level=logging.WARNING):
            sync_challenge_phase_to_github(self.challenge_phase)

    def test_sync_challenge_phase_to_github_no_repo(self):
        """Test challenge phase sync when no GitHub repository is configured"""
        self.challenge.github_repository = ""

        with self.assertLogs(level=logging.WARNING):
            sync_challenge_phase_to_github(self.challenge_phase)

    @patch("challenges.github_utils.GithubInterface")
    def test_sync_challenge_data_structure(self, mock_github_class):
        """Test that challenge data is properly structured for GitHub sync"""
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        sync_challenge_to_github(self.challenge)

        # Verify that update_data_from_path was called with challenge data
        call_args = mock_github.update_json_if_changed.call_args
        self.assertEqual(call_args[0][0], "challenge.json")  # path
        challenge_data = call_args[0][1]  # data

        # Check that key fields are present
        self.assertEqual(challenge_data["title"], "Test Challenge")
        self.assertEqual(challenge_data["description"], "Test Description")
        self.assertIn("start_date", challenge_data)
        self.assertIn("end_date", challenge_data)

    @patch("challenges.github_utils.GithubInterface")
    def test_sync_challenge_phase_data_structure(self, mock_github_class):
        """Test that challenge phase data is properly structured for GitHub sync"""
        mock_github = Mock()
        mock_github_class.return_value = mock_github

        sync_challenge_phase_to_github(self.challenge_phase)

        # Verify that update_data_from_path was called with phase data
        call_args = mock_github.update_json_if_changed.call_args
        self.assertEqual(call_args[0][0], "phases/test_phase.json")  # path
        phase_data = call_args[0][1]  # data

        # Check that key fields are present
        self.assertEqual(phase_data["name"], "Test Phase")
        self.assertEqual(phase_data["description"], "Test Phase Description")
        self.assertEqual(phase_data["codename"], "test_phase")
