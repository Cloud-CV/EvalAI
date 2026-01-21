import datetime as dt
import logging
from unittest.mock import Mock, patch

from challenges import github_utils as gu
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

    @patch("challenges.github_interface.GithubInterface.get_content_from_path")
    @patch("challenges.github_interface.requests.request")
    def test_update_content_from_path_creates_when_missing(
        self, mock_request, mock_get
    ):
        """When file is missing, create flow is used and no sha is sent"""
        mock_get.return_value = None
        mock_response = Mock()
        mock_response.json.return_value = {"sha": "new_sha"}
        mock_response.raise_for_status.return_value = None
        mock_request.return_value = mock_response

        result = self.github.update_content_from_path(
            "new.yaml", "Y29udGVudA=="
        )

        self.assertEqual(result, {"sha": "new_sha"})
        # Ensure PUT happened once
        mock_request.assert_called_once()

    def test_process_field_value_formats_and_serializes(self):
        # date formatting
        date = dt.datetime(2023, 1, 2, 3, 4, 5)
        self.assertEqual(
            self.github._process_field_value("start_date", date),
            "2023-01-02 03:04:05",
        )

        # list of objects -> list of ids
        class Obj:
            def __init__(self, pk):
                self.pk = pk

        self.assertEqual(
            self.github._process_field_value("list", [Obj(1), Obj(2)]), [1, 2]
        )

        # file-like/path-like
        class Dummy:
            name = "path/to/file.txt"

        self.assertEqual(
            self.github._process_field_value("evaluation_script", Dummy()),
            "path/to/file.txt",
        )

    def test_read_text_from_file_field_variants(self):
        # value with open/read returning bytes
        class FieldFileLike:
            def __init__(self, data=b"hello"):
                self._data = data

            def open(self, *_args, **_kwargs):
                return None

            def read(self):
                return self._data

            def close(self):
                return None

        self.assertEqual(
            self.github._read_text_from_file_field(FieldFileLike(b"hi")), "hi"
        )

        # value with only read
        class ReadOnly:
            def __init__(self, data=b"bye"):
                self._data = data

            def read(self):
                return self._data

        self.assertEqual(
            self.github._read_text_from_file_field(ReadOnly(b"bye")), "bye"
        )

        # value without read/open
        class Other:
            def __str__(self):
                return "stringified"

        self.assertEqual(
            self.github._read_text_from_file_field(Other()), "stringified"
        )

    def test_get_data_from_path_none_when_no_content(self):
        with patch.object(
            self.github, "get_content_from_path", return_value={}
        ):
            assert self.github.get_data_from_path("x") is None

    def test_is_repository_true_false(self):
        with patch.object(self.github, "make_request", return_value={"id": 1}):
            assert self.github.is_repository() is True
        with patch.object(self.github, "make_request", return_value=None):
            assert self.github.is_repository() is False

    def test_update_challenge_config_non_file_changes(self):
        # Existing YAML without key, then update data
        with patch.object(
            self.github, "get_data_from_path", return_value="title: Old\n"
        ), patch.object(
            self.github, "update_data_from_path", return_value={"ok": True}
        ) as mock_update:

            class ChallengeObj:
                title = "New"
                start_date = None
                end_date = None

            ok = self.github.update_challenge_config(ChallengeObj(), "title")
            self.assertTrue(ok)
            mock_update.assert_called_once()

    def test_update_challenge_config_skips_if_unchanged(self):
        with patch.object(
            self.github, "get_data_from_path", return_value="title: Same\n"
        ):

            class ChallengeObj:
                title = "Same"

            ok = self.github.update_challenge_config(ChallengeObj(), "title")
            self.assertTrue(ok)  # returns True but no update

    def test_update_challenge_config_file_field_missing_path(self):
        # evaluation_script path missing in YAML
        with patch.object(
            self.github, "get_data_from_path", return_value="{}\n"
        ):

            class ChallengeObj:
                evaluation_script = object()

            ok = self.github.update_challenge_config(
                ChallengeObj(), "evaluation_script"
            )
            self.assertFalse(ok)

    def test_update_challenge_config_file_field_updates_when_changed(self):
        # YAML with path, and new content different
        with patch.object(
            self.github,
            "get_data_from_path",
            side_effect=[
                "evaluation_script: path/file.txt\n",
                "old-text",
            ],
        ), patch.object(
            self.github, "update_data_from_path", return_value={"ok": True}
        ) as mock_update:

            class FileLike:
                def __init__(self, data):
                    self._data = data

                def read(self):
                    return self._data

            class ChallengeObj:
                evaluation_script = FileLike(b"new-text")

            ok = self.github.update_challenge_config(
                ChallengeObj(), "evaluation_script"
            )
            self.assertTrue(ok)
            mock_update.assert_called_once()

    def test_update_challenge_config_returns_false_on_process_failure(self):
        with patch.object(
            self.github, "get_data_from_path", return_value="{}\n"
        ):

            class ChallengeObj:
                # make _process_field_value return None by passing None
                title = None

            ok = self.github.update_challenge_config(ChallengeObj(), "title")
            self.assertFalse(ok)

    def test_update_challenge_phase_config_not_found_by_codename(self):
        with patch.object(
            self.github,
            "get_data_from_path",
            return_value="challenge_phases: []\n",
        ):

            class PhaseObj:
                codename = "missing"
                challenge = object()

            ok = self.github.update_challenge_phase_config(PhaseObj(), "name")
            self.assertFalse(ok)

    def test_update_challenge_phase_config_file_field_missing_path(self):
        yaml_text = """
challenge_phases:
  - codename: C1
    name: N
"""
        with patch.object(
            self.github, "get_data_from_path", return_value=yaml_text
        ):

            class PhaseObj:
                codename = "C1"
                test_annotation = object()
                challenge = object()

            ok = self.github.update_challenge_phase_config(
                PhaseObj(), "test_annotation"
            )
            self.assertFalse(ok)

    def test_update_challenge_phase_config_non_file_updates(self):
        yaml_text = """
challenge_phases:
  - codename: C1
    name: Old
"""
        with patch.object(
            self.github, "get_data_from_path", return_value=yaml_text
        ), patch.object(
            self.github, "update_data_from_path", return_value={"ok": True}
        ) as mock_update:

            class PhaseObj:
                codename = "C1"
                name = "New"
                challenge = object()

            ok = self.github.update_challenge_phase_config(PhaseObj(), "name")
            self.assertTrue(ok)
            mock_update.assert_called_once()

    def test_update_challenge_phase_config_skips_if_unchanged(self):
        yaml_text = """
challenge_phases:
  - codename: C1
    name: Same
"""
        with patch.object(
            self.github, "get_data_from_path", return_value=yaml_text
        ):

            class PhaseObj:
                codename = "C1"
                name = "Same"
                challenge = object()

            ok = self.github.update_challenge_phase_config(PhaseObj(), "name")
            self.assertTrue(ok)

    def test_update_challenge_phase_config_file_field_updates_when_changed(
        self,
    ):
        yaml_text = """
challenge_phases:
  - codename: C1
    name: N
    test_annotation_file: path/ann.txt
"""
        with patch.object(
            self.github,
            "get_data_from_path",
            side_effect=[
                yaml_text,
                "old",
            ],
        ), patch.object(
            self.github, "update_data_from_path", return_value={"ok": True}
        ) as mock_update:

            class FileLike:
                def __init__(self, data):
                    self._data = data

                def read(self):
                    return self._data

            class PhaseObj:
                codename = "C1"
                test_annotation = FileLike(b"new")
                challenge = object()

            ok = self.github.update_challenge_phase_config(
                PhaseObj(), "test_annotation"
            )
            self.assertTrue(ok)
            mock_update.assert_called_once()


# Lightweight checks for sync config constants to ensure availability and shape
def test_github_sync_config_expected_keys():
    from challenges import github_sync_config as cfg

    assert isinstance(cfg.challenge_non_file_fields, list)
    for key in [
        "title",
        "published",
        "image",
        "evaluation_script",
        "start_date",
        "end_date",
    ]:
        assert key in cfg.challenge_non_file_fields

    assert isinstance(cfg.challenge_file_fields, list)
    for key in [
        "description",
        "evaluation_details",
        "terms_and_conditions",
        "submission_guidelines",
    ]:
        assert key in cfg.challenge_file_fields

    assert isinstance(cfg.challenge_phase_non_file_fields, list)
    assert "name" in cfg.challenge_phase_non_file_fields
    assert "codename" in cfg.challenge_phase_non_file_fields

    assert isinstance(cfg.challenge_phase_file_fields, list)
    assert "description" in cfg.challenge_phase_file_fields

    assert isinstance(cfg.challenge_additional_sections, list)
    for key in ["leaderboard", "dataset_splits", "challenge_phase_splits"]:
        assert key in cfg.challenge_additional_sections


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

    @patch("challenges.github_utils.GithubInterface")
    def test_sync_challenge_returns_false_on_update_failure(
        self, mock_github_class
    ):
        mock_github = Mock()
        mock_github_class.return_value = mock_github
        mock_github.update_challenge_config.return_value = False

        ok = gu.github_challenge_sync(self.challenge.id, changed_field="title")
        self.assertFalse(ok)

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

    def test_github_sync_invalid_changed_field_type_and_not_found(self):
        # invalid changed_field should return False and cleanup flags
        ok = gu.github_challenge_sync(self.challenge.id, changed_field=123)
        self.assertFalse(ok)
        # flags are cleaned
        self.assertFalse(hasattr(gu._github_sync_context, "skip_github_sync"))
        self.assertFalse(hasattr(gu._github_sync_context, "change_source"))

        # not found
        ok2 = gu.github_challenge_sync(999999, changed_field="title")
        self.assertFalse(ok2)

    @patch("challenges.github_utils.GithubInterface")
    def test_sync_challenge_phase_returns_false_on_update_failure(
        self, mock_github_class
    ):
        mock_github = Mock()
        mock_github_class.return_value = mock_github
        mock_github.update_challenge_phase_config.return_value = False

        ok = gu.github_challenge_phase_sync(
            self.challenge_phase.id, changed_field="name"
        )
        self.assertFalse(ok)

    def test_github_phase_sync_invalid_changed_field_type_and_not_found(self):
        # invalid changed_field type
        ok = gu.github_challenge_phase_sync(
            self.challenge_phase.id, changed_field=[]
        )
        self.assertFalse(ok)
        self.assertFalse(hasattr(gu._github_sync_context, "skip_github_sync"))
        self.assertFalse(hasattr(gu._github_sync_context, "change_source"))

        # not found
        ok2 = gu.github_challenge_phase_sync(999999, changed_field="name")
        self.assertFalse(ok2)

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
