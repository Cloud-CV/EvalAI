from datetime import timedelta
from io import StringIO

from accounts.models import Profile
from allauth.account.models import EmailAddress
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam


class MergeDuplicateEmailsCommandTest(TestCase):
    def setUp(self):
        self.user_old = User.objects.create_user(
            username="original_user",
            email="dupe@example.com",
            password="password",
        )
        self.user_new = User.objects.create_user(
            username="dupe@example.com",
            email="dupe@example.com",
            password="password",
        )
        EmailAddress.objects.create(
            user=self.user_old,
            email="dupe@example.com",
            primary=True,
            verified=True,
        )
        EmailAddress.objects.create(
            user=self.user_new,
            email="dupe_alt@example.com",
            primary=True,
            verified=True,
        )

        self.host_team = ChallengeHostTeam.objects.create(
            team_name="HostTeam", created_by=self.user_old
        )
        self.challenge_host = ChallengeHost.objects.create(
            user=self.user_new,
            team_name=self.host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="ParticipantTeam", created_by=self.user_new
        )
        self.participant = Participant.objects.create(
            user=self.user_new,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

    def test_dry_run_does_not_modify(self):
        out = StringIO()
        call_command("merge_duplicate_emails", stdout=out)
        output = out.getvalue()

        self.assertIn("DRY-RUN", output)
        self.assertIn("dupe@example.com", output)

        self.user_new.refresh_from_db()
        self.assertTrue(self.user_new.is_active)
        self.assertEqual(
            ChallengeHost.objects.get(pk=self.challenge_host.pk).user,
            self.user_new,
        )

    def test_commit_merges_and_deactivates(self):
        """With no submissions on either side, the newer account is kept."""
        out = StringIO()
        call_command("merge_duplicate_emails", "--commit", stdout=out)
        output = out.getvalue()

        self.assertIn("COMMIT", output)

        # FKs owned by old user get reassigned to the new (canonical) user
        self.host_team.refresh_from_db()
        self.assertEqual(self.host_team.created_by, self.user_new)

        # FKs already on user_new stay on user_new
        self.challenge_host.refresh_from_db()
        self.assertEqual(self.challenge_host.user, self.user_new)
        self.participant.refresh_from_db()
        self.assertEqual(self.participant.user, self.user_new)
        self.participant_team.refresh_from_db()
        self.assertEqual(self.participant_team.created_by, self.user_new)

        # Old user is deactivated with renamed email
        self.user_old.refresh_from_db()
        self.assertFalse(self.user_old.is_active)
        self.assertEqual(self.user_old.email, "dupe+duplicate@example.com")

        self.assertTrue(Profile.objects.filter(user=self.user_old).exists())
        ea = EmailAddress.objects.filter(user=self.user_old)
        self.assertTrue(ea.exists())
        self.assertEqual(ea.first().email, "dupe+duplicate@example.com")

        # New user stays active
        self.user_new.refresh_from_db()
        self.assertTrue(self.user_new.is_active)

    def test_no_duplicates_is_noop(self):
        User.objects.filter(pk=self.user_new.pk).delete()
        out = StringIO()
        call_command("merge_duplicate_emails", "--commit", stdout=out)
        self.assertIn("No duplicate emails found", out.getvalue())

    def test_keeps_account_with_submissions(self):
        """When only the newer account has submissions, it should be kept."""
        now = timezone.now()
        challenge = Challenge.objects.create(
            title="SubChallenge",
            short_description="s",
            description="d",
            terms_and_conditions="t",
            submission_guidelines="g",
            creator=self.host_team,
            domain="CV",
            list_tags=["Test"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
        )
        phase = ChallengePhase.objects.create(
            name="Phase1",
            challenge=challenge,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
        )
        Submission.objects.create(
            created_by=self.user_new,
            participant_team=self.participant_team,
            challenge_phase=phase,
            status="submitted",
        )

        out = StringIO()
        call_command("merge_duplicate_emails", "--commit", stdout=out)

        self.user_new.refresh_from_db()
        self.assertTrue(self.user_new.is_active)

        self.user_old.refresh_from_db()
        self.assertFalse(self.user_old.is_active)

    def test_keeps_account_with_most_submissions(self):
        """When both accounts have submissions, the one with more wins."""
        now = timezone.now()
        challenge = Challenge.objects.create(
            title="SubChallenge",
            short_description="s",
            description="d",
            terms_and_conditions="t",
            submission_guidelines="g",
            creator=self.host_team,
            domain="CV",
            list_tags=["Test"],
            published=True,
            is_registration_open=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
        )
        phase = ChallengePhase.objects.create(
            name="Phase1",
            challenge=challenge,
            start_date=now - timedelta(days=1),
            end_date=now + timedelta(days=30),
        )
        # Old user has more submissions
        for _ in range(5):
            Submission.objects.create(
                created_by=self.user_old,
                participant_team=self.participant_team,
                challenge_phase=phase,
                status="submitted",
            )
        Submission.objects.create(
            created_by=self.user_new,
            participant_team=self.participant_team,
            challenge_phase=phase,
            status="submitted",
        )

        out = StringIO()
        call_command("merge_duplicate_emails", "--commit", stdout=out)

        self.user_old.refresh_from_db()
        self.assertTrue(self.user_old.is_active)

        self.user_new.refresh_from_db()
        self.assertFalse(self.user_new.is_active)
        self.assertEqual(self.user_new.email, "dupe+duplicate@example.com")
