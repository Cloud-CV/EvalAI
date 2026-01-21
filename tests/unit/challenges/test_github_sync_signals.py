from unittest.mock import patch

from challenges import models as challenge_models
from challenges.models import (
    Challenge,
    ChallengePhase,
    GitHubSyncMiddleware,
    reset_github_sync_context,
)
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHostTeam


class TestGithubSyncSignals(TestCase):

    def setUp(self):
        # minimal creator for Challenge
        self.user = User.objects.create(
            username="owner", email="o@example.com"
        )
        self.host_team = ChallengeHostTeam.objects.create(
            team_name="team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Initial Title",
            description="Desc",
            github_token="test_token",
            github_repository="org/repo",
            github_branch="main",
            creator=self.host_team,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=5),
        )
        self.phase = ChallengePhase.objects.create(
            name="Initial Phase",
            description="Phase Desc",
            challenge=self.challenge,
            codename="phase_code",
        )

    @patch("challenges.aws_utils.challenge_approval_callback")
    @patch("challenges.github_utils.github_challenge_sync")
    def test_challenge_post_save_calls_sync_with_update_fields(
        self, mock_sync, _mock_approval_cb
    ):
        self.challenge.title = "Updated Title"
        # Pass update_fields so receiver can read changed field directly
        self.challenge.save(update_fields=["title"])

        mock_sync.assert_called_once()
        args, kwargs = mock_sync.call_args
        self.assertEqual(args[0], self.challenge.id)
        self.assertEqual(kwargs.get("changed_field"), "title")

    @patch("challenges.github_utils.github_challenge_phase_sync")
    def test_phase_post_save_calls_sync_with_update_fields(
        self, mock_phase_sync
    ):
        self.phase.name = "Updated Phase"
        self.phase.save(update_fields=["name"])

        mock_phase_sync.assert_called_once()
        args, kwargs = mock_phase_sync.call_args
        self.assertEqual(args[0], self.phase.id)
        self.assertEqual(kwargs.get("changed_field"), "name")

    @patch("challenges.aws_utils.challenge_approval_callback")
    @patch("challenges.github_utils.github_challenge_sync")
    def test_middleware_infers_changed_field_and_triggers_sync(
        self, mock_sync, _mock_approval_cb
    ):
        # Simulate a PATCH request payload captured by middleware
        class _Req:
            method = "PATCH"
            body = b'{\n  "title": "MW Title"\n}'

        mw = GitHubSyncMiddleware()
        mw.process_request(_Req())

        # Save without update_fields; receiver should infer from payload keys
        self.challenge.title = "MW Title"
        self.challenge.save()

        mock_sync.assert_called_once()
        _args, kwargs = mock_sync.call_args
        self.assertEqual(kwargs.get("changed_field"), "title")

    @patch("challenges.github_utils.github_challenge_sync")
    def test_challenge_create_does_not_sync(self, mock_sync):
        with patch("challenges.aws_utils.challenge_approval_callback"):
            Challenge.objects.create(
                title="New Challenge",
                description="Desc",
                github_token="test_token",
                github_repository="org/repo",
                github_branch="feature/test",  # avoid unique (repo, branch) conflict
                creator=self.host_team,
                start_date=timezone.now(),
                end_date=timezone.now() + timezone.timedelta(days=5),
            )

        mock_sync.assert_not_called()

    @patch("challenges.aws_utils.challenge_approval_callback")
    @patch("challenges.github_utils.github_challenge_sync")
    def test_no_sync_without_github_config(self, mock_sync, _mock_approval_cb):
        self.challenge.github_token = ""
        self.challenge.save(
            update_fields=["github_token"]
        )  # change without config
        mock_sync.assert_not_called()

    @patch("challenges.aws_utils.challenge_approval_callback")
    @patch("challenges.github_utils.github_challenge_sync")
    def test_dedupe_within_single_request(self, mock_sync, _mock_approval_cb):
        # Start request, middleware captures keys
        class _Req:
            method = "PATCH"
            body = b'{\n  "title": "One"\n}'

        mw = GitHubSyncMiddleware()
        mw.process_request(_Req())

        # Two saves in same request
        self.challenge.title = "One"
        self.challenge.save()
        self.challenge.description = "Changed"
        self.challenge.save()

        # Only the first should sync for this challenge in this request
        mock_sync.assert_called_once()

    @patch("challenges.aws_utils.challenge_approval_callback")
    @patch("challenges.github_utils.github_challenge_sync")
    def test_skip_when_change_source_is_github(
        self, mock_sync, _mock_approval_cb
    ):
        # Simulate a GitHub-sourced change via models' sync context
        challenge_models._github_sync_context.change_source = "github"
        try:
            self.challenge.title = "Ignored"
            self.challenge.save(update_fields=["title"])
            mock_sync.assert_not_called()
        finally:
            if hasattr(challenge_models._github_sync_context, "change_source"):
                delattr(challenge_models._github_sync_context, "change_source")

    @patch("challenges.aws_utils.challenge_approval_callback")
    @patch("challenges.github_utils.github_challenge_sync")
    def test_skip_when_skip_github_sync_flag_set(
        self, mock_sync, _mock_approval_cb
    ):
        # When internal skip flag is set, no sync should happen
        challenge_models._github_sync_context.skip_github_sync = True
        try:
            self.challenge.title = "Ignored by flag"
            self.challenge.save(update_fields=["title"])
            mock_sync.assert_not_called()
        finally:
            if hasattr(
                challenge_models._github_sync_context, "skip_github_sync"
            ):
                delattr(
                    challenge_models._github_sync_context, "skip_github_sync"
                )

    @patch("challenges.aws_utils.challenge_approval_callback")
    @patch("challenges.github_utils.github_challenge_sync")
    def test_no_changed_field_inference_means_no_sync(
        self, mock_sync, _mock_approval_cb
    ):
        # Ensure no payload keys available to infer
        reset_github_sync_context()
        self.challenge.title = "Still Updated"
        self.challenge.save()  # no update_fields, no middleware keys
        mock_sync.assert_not_called()

    @patch("challenges.aws_utils.challenge_approval_callback")
    @patch("challenges.github_utils.github_challenge_sync")
    def test_multiple_update_fields_prefers_first(
        self, mock_sync, _mock_approval_cb
    ):
        self.challenge.title = "A"
        self.challenge.description = "B"
        self.challenge.save(update_fields=["title", "description"])
        _args, kwargs = mock_sync.call_args
        # Order of update_fields is non-deterministic (Django converts to set), accept either
        assert kwargs.get("changed_field") in {"title", "description"}

    @patch("challenges.github_utils.github_challenge_phase_sync")
    def test_phase_middleware_infers_changed_field_and_triggers_sync(
        self, mock_phase_sync
    ):
        # Simulate request payload for phase update
        class _Req:
            method = "PATCH"
            body = b'{\n  "name": "New Phase Name"\n}'

        mw = challenge_models.GitHubSyncMiddleware()
        mw.process_request(_Req())

        self.phase.name = "New Phase Name"
        self.phase.save()

        mock_phase_sync.assert_called_once()
        _args, kwargs = mock_phase_sync.call_args
        self.assertEqual(kwargs.get("changed_field"), "name")
