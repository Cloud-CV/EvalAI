import os
import shutil
from datetime import timedelta

from challenges.models import Challenge, ChallengePhase
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHostTeam
from jobs.admin import SubmissionAdmin
from jobs.admin_filters import OngoingChallengesFilter
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam


class OngoingChallengesFilterTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="12345"
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user
        )
        Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team,
        )
        now = timezone.now()

        # Past challenge (ended)
        self.past_challenge = Challenge.objects.create(
            title="Past Challenge",
            start_date=now - timedelta(days=10),
            end_date=now - timedelta(days=5),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

        # Ongoing challenge
        self.ongoing_challenge = Challenge.objects.create(
            title="Ongoing Challenge",
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=5),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

        # Future challenge (not started)
        self.future_challenge = Challenge.objects.create(
            title="Future Challenge",
            start_date=now + timedelta(days=5),
            end_date=now + timedelta(days=10),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

        # Ongoing but unpublished - should not appear in lookups
        self.ongoing_unpublished = Challenge.objects.create(
            title="Ongoing Unpublished",
            start_date=now - timedelta(days=2),
            end_date=now + timedelta(days=2),
            published=False,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

        # Ongoing but disabled - should not appear in lookups
        self.ongoing_disabled = Challenge.objects.create(
            title="Ongoing Disabled",
            start_date=now - timedelta(days=2),
            end_date=now + timedelta(days=2),
            published=True,
            approved_by_admin=True,
            is_disabled=True,
            creator=self.challenge_host_team,
        )

        try:
            os.makedirs("/tmp/evalai_test_filters")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai_test_filters"):
            test_annotation = SimpleUploadedFile(
                "test_sample_file.txt",
                b"Dummy file content",
                content_type="text/plain",
            )
            self.ongoing_phase = ChallengePhase.objects.create(
                name="Ongoing Phase",
                description="Phase desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=5),
                end_date=now + timedelta(days=5),
                challenge=self.ongoing_challenge,
                test_annotation=test_annotation,
            )
            self.past_phase = ChallengePhase.objects.create(
                name="Past Phase",
                description="Phase desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=10),
                end_date=now - timedelta(days=5),
                challenge=self.past_challenge,
                test_annotation=SimpleUploadedFile(
                    "past.txt", b"content", content_type="text/plain"
                ),
            )

        self.submission_ongoing = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.ongoing_phase,
            created_by=self.user,
            status="submitted",
            input_file=self.ongoing_phase.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
        )
        self.submission_past = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.past_phase,
            created_by=self.user,
            status="submitted",
            input_file=self.past_phase.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
        )

        self.model_admin = SubmissionAdmin(Submission, AdminSite())
        self.request = None

    def tearDown(self):
        if os.path.exists("/tmp/evalai_test_filters"):
            shutil.rmtree("/tmp/evalai_test_filters")

    def _get_filter(self):
        return OngoingChallengesFilter(
            self.request, {}, Submission, self.model_admin
        )

    def test_lookups_returns_only_ongoing_challenges(self):
        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)
        lookup_titles = [title for (_pk, title) in lookups]

        self.assertIn("Ongoing Challenge", lookup_titles)
        self.assertNotIn("Past Challenge", lookup_titles)
        self.assertNotIn("Future Challenge", lookup_titles)

    def test_lookups_excludes_unpublished_and_disabled(self):
        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)
        lookup_titles = [title for (_pk, title) in lookups]

        self.assertNotIn("Ongoing Unpublished", lookup_titles)
        self.assertNotIn("Ongoing Disabled", lookup_titles)

    def test_lookups_ordered_by_title(self):
        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)
        titles = [title for (_pk, title) in lookups]
        self.assertEqual(titles, sorted(titles))

    def test_queryset_filters_by_challenge_when_value_set(self):
        filter_instance = self._get_filter()
        filter_instance.value = lambda: str(self.ongoing_challenge.id)

        base_queryset = Submission.objects.all()
        filtered = filter_instance.queryset(self.request, base_queryset)

        self.assertIn(self.submission_ongoing, filtered)
        self.assertNotIn(self.submission_past, filtered)
        self.assertEqual(filtered.count(), 1)

    def test_queryset_returns_all_when_no_value(self):
        filter_instance = self._get_filter()
        filter_instance.value = lambda: None

        base_queryset = Submission.objects.all()
        filtered = filter_instance.queryset(self.request, base_queryset)

        self.assertIn(self.submission_ongoing, filtered)
        self.assertIn(self.submission_past, filtered)
        self.assertEqual(filtered.count(), 2)

    def test_lookups_empty_when_no_ongoing_challenges(self):
        Challenge.objects.filter(
            start_date__lte=timezone.now(),
            end_date__gte=timezone.now(),
        ).update(end_date=timezone.now() - timedelta(days=1))

        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)

        self.assertEqual(lookups, [])
