from datetime import timedelta
from unittest.mock import patch

from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission
from jobs.stale_submission_alerts import (
    cache_key_for_challenge,
    find_challenges_with_stale_remote_submissions,
    notify_remote_challenge_hosts_of_stale_submissions,
)
from participants.models import ParticipantTeam

LOCMEM_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
    "throttling": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}


class StaleRemoteSubmissionAlertsTestCase(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create(
            username="host", email="host@test.com", password="password"
        )
        self.host_team = ChallengeHostTeam.objects.create(
            team_name="Host Team", created_by=self.user
        )
        ChallengeHost.objects.create(
            user=self.user,
            team_name=self.host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user
        )
        now = timezone.now()
        self.challenge = Challenge.objects.create(
            title="Remote Challenge",
            description="desc",
            terms_and_conditions="terms",
            submission_guidelines="guide",
            creator=self.host_team,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
            published=True,
            remote_evaluation=True,
            inform_hosts=True,
        )
        self.challenge_phase = ChallengePhase.objects.create(
            name="Phase 1",
            description="phase",
            leaderboard_public=False,
            is_public=True,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
            challenge=self.challenge,
        )

    def _create_stale_submission(self, hours_old=3):
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )
        Submission.objects.filter(pk=submission.pk).update(
            submitted_at=timezone.now() - timedelta(hours=hours_old)
        )
        return Submission.objects.get(pk=submission.pk)

    def test_finds_stale_submissions_for_remote_challenges_only(self):
        self._create_stale_submission()
        non_remote = Challenge.objects.create(
            title="Hosted",
            description="desc",
            terms_and_conditions="terms",
            submission_guidelines="guide",
            creator=self.host_team,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            published=True,
            remote_evaluation=False,
            inform_hosts=True,
        )
        non_remote_phase = ChallengePhase.objects.create(
            name="Phase",
            description="phase",
            leaderboard_public=False,
            is_public=True,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30),
            challenge=non_remote,
        )
        stale_non_remote = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=non_remote_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )
        Submission.objects.filter(pk=stale_non_remote.pk).update(
            submitted_at=timezone.now() - timedelta(hours=5)
        )

        rows = find_challenges_with_stale_remote_submissions()
        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["challenge_phase__challenge_id"], self.challenge.pk
        )

    @override_settings(DEBUG=False, CACHES=LOCMEM_CACHES)
    @patch("jobs.stale_submission_alerts.send_email")
    def test_sends_email_to_challenge_hosts(self, mock_send_email):
        mock_send_email.return_value = True
        self._create_stale_submission()
        with self.settings(
            SENDGRID_SETTINGS={
                "TEMPLATES": {
                    "STUCK_REMOTE_SUBMISSIONS_EMAIL": "template-stuck"
                }
            }
        ):
            result = notify_remote_challenge_hosts_of_stale_submissions()

        self.assertEqual(result["challenges_notified"], 1)
        self.assertEqual(result["emails_sent"], 1)
        mock_send_email.assert_called_once()
        self.assertEqual(mock_send_email.call_args[1]["recipient"], "host@test.com")
        self.assertEqual(
            mock_send_email.call_args[1]["template_id"], "template-stuck"
        )
        self.assertTrue(cache.get(cache_key_for_challenge(self.challenge.pk)))

    @override_settings(DEBUG=False)
    @patch("jobs.stale_submission_alerts.send_email")
    def test_skips_recent_submissions(self, mock_send_email):
        mock_send_email.return_value = True
        submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
        )
        Submission.objects.filter(pk=submission.pk).update(
            submitted_at=timezone.now() - timedelta(minutes=30)
        )
        with self.settings(
            SENDGRID_SETTINGS={
                "TEMPLATES": {
                    "STUCK_REMOTE_SUBMISSIONS_EMAIL": "template-stuck"
                }
            },
            REMOTE_STUCK_SUBMISSION_THRESHOLD_MINUTES=120,
        ):
            result = notify_remote_challenge_hosts_of_stale_submissions()

        self.assertEqual(result["challenges_notified"], 0)
        mock_send_email.assert_not_called()

    @override_settings(DEBUG=False, CACHES=LOCMEM_CACHES)
    @patch("jobs.stale_submission_alerts.send_email")
    def test_respects_per_challenge_cooldown(self, mock_send_email):
        mock_send_email.return_value = True
        self._create_stale_submission()
        with self.settings(
            SENDGRID_SETTINGS={
                "TEMPLATES": {
                    "STUCK_REMOTE_SUBMISSIONS_EMAIL": "template-stuck"
                }
            }
        ):
            first = notify_remote_challenge_hosts_of_stale_submissions()
            second = notify_remote_challenge_hosts_of_stale_submissions()

        self.assertEqual(first["challenges_notified"], 1)
        self.assertEqual(second["skipped_cooldown"], 1)
        self.assertEqual(mock_send_email.call_count, 1)
