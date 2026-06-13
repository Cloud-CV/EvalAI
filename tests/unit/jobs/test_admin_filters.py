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
from jobs.admin_filters import (
    ActiveChallengePhaseFilter,
    TopActiveChallengesFilter,
    _get_top_challenge_ids,
)
from jobs.models import Submission
from participants.models import Participant, ParticipantTeam


class GetTopChallengeIdsTest(TestCase):
    """Tests for _get_top_challenge_ids() helper."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="topidsuser", password="12345"
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Top IDs Host Team", created_by=self.user
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Top IDs Participant", created_by=self.user
        )
        Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team,
        )
        now = timezone.now()

        self.active_challenge = Challenge.objects.create(
            title="Active Challenge",
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=10),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )
        self.old_challenge = Challenge.objects.create(
            title="Old Challenge",
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=40),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

        try:
            os.makedirs("/tmp/evalai_test_top_ids")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai_test_top_ids"):
            self.active_phase = ChallengePhase.objects.create(
                name="Active Phase",
                codename="active-phase",
                description="Desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=10),
                end_date=now + timedelta(days=10),
                challenge=self.active_challenge,
                test_annotation=SimpleUploadedFile(
                    "active.txt", b"x", content_type="text/plain"
                ),
            )
            self.old_phase = ChallengePhase.objects.create(
                name="Old Phase",
                codename="old-phase",
                description="Desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=60),
                end_date=now - timedelta(days=40),
                challenge=self.old_challenge,
                test_annotation=SimpleUploadedFile(
                    "old.txt", b"x", content_type="text/plain"
                ),
            )

        Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.active_phase,
            created_by=self.user,
            status="submitted",
            input_file=self.active_phase.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
            submitted_at=now - timedelta(days=5),
        )
        sub_old = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.old_phase,
            created_by=self.user,
            status="submitted",
            input_file=self.old_phase.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
        )
        Submission.objects.filter(pk=sub_old.pk).update(
            submitted_at=now - timedelta(days=45)
        )

    def tearDown(self):
        if os.path.exists("/tmp/evalai_test_top_ids"):
            shutil.rmtree("/tmp/evalai_test_top_ids")

    def test_returns_ids_of_challenges_with_recent_submissions(self):
        result = _get_top_challenge_ids()
        self.assertIn(self.active_challenge.id, result)
        self.assertNotIn(self.old_challenge.id, result)

    def test_returns_empty_when_no_recent_submissions(self):
        Submission.objects.filter(
            submitted_at__gte=timezone.now() - timedelta(days=30)
        ).delete()
        result = _get_top_challenge_ids()
        self.assertEqual(result, [])

    def test_returns_at_most_10_ids(self):
        now = timezone.now()
        for i in range(15):
            challenge = Challenge.objects.create(
                title=f"Challenge {i}",
                start_date=now - timedelta(days=10),
                end_date=now + timedelta(days=10),
                published=True,
                approved_by_admin=True,
                is_disabled=False,
                creator=self.challenge_host_team,
            )
            with self.settings(MEDIA_ROOT="/tmp/evalai_test_top_ids"):
                phase = ChallengePhase.objects.create(
                    name=f"Phase {i}",
                    codename=f"phase-{i}-{challenge.id}",
                    description="Desc",
                    leaderboard_public=False,
                    is_public=True,
                    start_date=now - timedelta(days=10),
                    end_date=now + timedelta(days=10),
                    challenge=challenge,
                    test_annotation=SimpleUploadedFile(
                        f"t{i}.txt", b"x", content_type="text/plain"
                    ),
                )
                Submission.objects.create(
                    participant_team=self.participant_team,
                    challenge_phase=phase,
                    created_by=self.user,
                    status="submitted",
                    input_file=phase.test_annotation,
                    method_name="Test",
                    method_description="Desc",
                    project_url="http://test/",
                    publication_url="http://test/",
                    submitted_at=now - timedelta(days=1),
                )
        result = _get_top_challenge_ids()
        self.assertLessEqual(len(result), 10)


class TopActiveChallengesFilterTest(TestCase):
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

        # Challenge with recent submissions (should appear)
        self.active_challenge = Challenge.objects.create(
            title="Active Challenge",
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=10),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

        # Challenge with old submissions (should not appear)
        self.old_challenge = Challenge.objects.create(
            title="Old Challenge",
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=40),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

        # Challenge with recent submissions but unpublished
        self.unpublished_challenge = Challenge.objects.create(
            title="Unpublished Challenge",
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=5),
            published=False,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

        # Challenge with recent submissions but disabled
        self.disabled_challenge = Challenge.objects.create(
            title="Disabled Challenge",
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=5),
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
            self.active_phase = ChallengePhase.objects.create(
                name="Active Phase",
                codename="active-phase",
                description="Phase desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=10),
                end_date=now + timedelta(days=10),
                challenge=self.active_challenge,
                test_annotation=test_annotation,
            )
            self.old_phase = ChallengePhase.objects.create(
                name="Old Phase",
                codename="old-phase",
                description="Phase desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=60),
                end_date=now - timedelta(days=40),
                challenge=self.old_challenge,
                test_annotation=SimpleUploadedFile(
                    "old.txt", b"content", content_type="text/plain"
                ),
            )
            self.unpublished_phase = ChallengePhase.objects.create(
                name="Unpublished Phase",
                codename="unpublished-phase",
                description="Phase desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=5),
                end_date=now + timedelta(days=5),
                challenge=self.unpublished_challenge,
                test_annotation=SimpleUploadedFile(
                    "unpub.txt", b"content", content_type="text/plain"
                ),
            )
            self.disabled_phase = ChallengePhase.objects.create(
                name="Disabled Phase",
                codename="disabled-phase",
                description="Phase desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=5),
                end_date=now + timedelta(days=5),
                challenge=self.disabled_challenge,
                test_annotation=SimpleUploadedFile(
                    "disabled.txt", b"content", content_type="text/plain"
                ),
            )

        # Recent submission (within last 30 days)
        self.submission_recent = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.active_phase,
            created_by=self.user,
            status="submitted",
            input_file=self.active_phase.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
        )
        Submission.objects.filter(pk=self.submission_recent.pk).update(
            submitted_at=now - timedelta(days=5)
        )
        # Old submission (more than 30 days ago)
        self.submission_old = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.old_phase,
            created_by=self.user,
            status="submitted",
            input_file=self.old_phase.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
        )
        Submission.objects.filter(pk=self.submission_old.pk).update(
            submitted_at=now - timedelta(days=45)
        )
        # Recent submission to unpublished challenge
        self.submission_unpublished = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.unpublished_phase,
            created_by=self.user,
            status="submitted",
            input_file=self.unpublished_phase.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
            submitted_at=now - timedelta(days=5),
        )
        # Recent submission to disabled challenge
        self.submission_disabled = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.disabled_phase,
            created_by=self.user,
            status="submitted",
            input_file=self.disabled_phase.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
            submitted_at=now - timedelta(days=5),
        )

        self.model_admin = SubmissionAdmin(Submission, AdminSite())
        self.request = None

    def tearDown(self):
        if os.path.exists("/tmp/evalai_test_filters"):
            shutil.rmtree("/tmp/evalai_test_filters")

    def _get_filter(self):
        return TopActiveChallengesFilter(
            self.request, {}, Submission, self.model_admin
        )

    def test_lookups_returns_challenges_with_recent_submissions(self):
        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)
        lookup_labels = [label for (_pk, label) in lookups]

        # Should include challenge with recent submissions
        self.assertTrue(
            any("Active Challenge" in label for label in lookup_labels)
        )
        # Should not include challenge with old submissions (>30 days)
        self.assertFalse(
            any("Old Challenge" in label for label in lookup_labels)
        )

    def test_lookups_excludes_unpublished_and_disabled(self):
        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)
        lookup_labels = [label for (_pk, label) in lookups]

        self.assertFalse(
            any("Unpublished Challenge" in label for label in lookup_labels)
        )
        self.assertFalse(
            any("Disabled Challenge" in label for label in lookup_labels)
        )

    def test_lookups_shows_submission_count(self):
        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)
        lookup_labels = [label for (_pk, label) in lookups]

        # Labels should include submission count in parentheses
        self.assertTrue(
            any("Active Challenge (1)" in label for label in lookup_labels)
        )

    def test_lookups_ordered_by_submission_count_descending(self):
        now = timezone.now()
        # Create another challenge with more recent submissions
        challenge_popular = Challenge.objects.create(
            title="Popular Challenge",
            start_date=now - timedelta(days=10),
            end_date=now + timedelta(days=10),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )
        with self.settings(MEDIA_ROOT="/tmp/evalai_test_filters"):
            phase_popular = ChallengePhase.objects.create(
                name="Popular Phase",
                codename="popular-phase",
                description="Desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=10),
                end_date=now + timedelta(days=10),
                challenge=challenge_popular,
                test_annotation=SimpleUploadedFile(
                    "pop.txt", b"x", content_type="text/plain"
                ),
            )
            # Create 3 submissions for popular challenge
            for i in range(3):
                Submission.objects.create(
                    participant_team=self.participant_team,
                    challenge_phase=phase_popular,
                    created_by=self.user,
                    status="submitted",
                    input_file=phase_popular.test_annotation,
                    method_name=f"Test {i}",
                    method_description="Desc",
                    project_url="http://test/",
                    publication_url="http://test/",
                    submitted_at=now - timedelta(days=i + 1),
                )

        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)

        # Popular Challenge (3 submissions) should come before Active Challenge
        # (1)
        if len(lookups) >= 2:
            first_label = lookups[0][1]
            self.assertIn("Popular Challenge", first_label)
            self.assertIn("(3)", first_label)

    def test_lookups_limited_to_10_challenges(self):
        now = timezone.now()
        # Create 15 challenges with recent submissions
        for i in range(15):
            challenge = Challenge.objects.create(
                title=f"Challenge {i}",
                start_date=now - timedelta(days=10),
                end_date=now + timedelta(days=10),
                published=True,
                approved_by_admin=True,
                is_disabled=False,
                creator=self.challenge_host_team,
            )
            with self.settings(MEDIA_ROOT="/tmp/evalai_test_filters"):
                phase = ChallengePhase.objects.create(
                    name=f"Phase {i}",
                    codename=f"phase-{i}-{challenge.id}",
                    description="Desc",
                    leaderboard_public=False,
                    is_public=True,
                    start_date=now - timedelta(days=10),
                    end_date=now + timedelta(days=10),
                    challenge=challenge,
                    test_annotation=SimpleUploadedFile(
                        f"test{i}.txt", b"x", content_type="text/plain"
                    ),
                )
                Submission.objects.create(
                    participant_team=self.participant_team,
                    challenge_phase=phase,
                    created_by=self.user,
                    status="submitted",
                    input_file=phase.test_annotation,
                    method_name="Test",
                    method_description="Desc",
                    project_url="http://test/",
                    publication_url="http://test/",
                    submitted_at=now - timedelta(days=1),
                )

        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)

        # Should be limited to 10
        self.assertLessEqual(len(lookups), 10)

    def test_queryset_filters_by_challenge_when_value_set(self):
        filter_instance = self._get_filter()
        filter_instance.value = lambda: str(self.active_challenge.id)

        base_queryset = Submission.objects.all()
        filtered = filter_instance.queryset(self.request, base_queryset)

        self.assertIn(self.submission_recent, filtered)
        self.assertNotIn(self.submission_old, filtered)

    def test_queryset_returns_all_when_no_value(self):
        filter_instance = self._get_filter()
        filter_instance.value = lambda: None

        base_queryset = Submission.objects.all()
        filtered = filter_instance.queryset(self.request, base_queryset)

        # All submissions should be present when no filter applied
        self.assertIn(self.submission_recent, filtered)
        self.assertIn(self.submission_old, filtered)

    def test_lookups_empty_when_no_recent_submissions(self):
        # Delete all recent submissions
        Submission.objects.filter(
            submitted_at__gte=timezone.now() - timedelta(days=30)
        ).delete()

        filter_instance = self._get_filter()
        lookups = filter_instance.lookups(self.request, self.model_admin)

        self.assertEqual(lookups, [])


class ActiveChallengePhaseFilterTest(TestCase):
    """Tests for ActiveChallengePhaseFilter: phases scoped to selected challenge."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="phaseuser", password="12345"
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Phase Test Host Team", created_by=self.user
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Phase Participant Team", created_by=self.user
        )
        Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team,
        )
        now = timezone.now()

        self.challenge_a = Challenge.objects.create(
            title="Challenge A",
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=5),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )
        self.challenge_b = Challenge.objects.create(
            title="Challenge B",
            start_date=now - timedelta(days=5),
            end_date=now + timedelta(days=5),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )

        try:
            os.makedirs("/tmp/evalai_test_filters_phase")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai_test_filters_phase"):
            test_file = SimpleUploadedFile(
                "test.txt", b"content", content_type="text/plain"
            )
            self.phase_a1 = ChallengePhase.objects.create(
                name="Phase A1",
                codename="phase-a1",
                description="Desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=5),
                end_date=now + timedelta(days=5),
                challenge=self.challenge_a,
                test_annotation=test_file,
            )
            self.phase_a2 = ChallengePhase.objects.create(
                name="Phase A2",
                codename="phase-a2",
                description="Desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=5),
                end_date=now + timedelta(days=5),
                challenge=self.challenge_a,
                test_annotation=SimpleUploadedFile(
                    "a2.txt", b"x", content_type="text/plain"
                ),
            )
            self.phase_b1 = ChallengePhase.objects.create(
                name="Phase B1",
                codename="phase-b1",
                description="Desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=5),
                end_date=now + timedelta(days=5),
                challenge=self.challenge_b,
                test_annotation=SimpleUploadedFile(
                    "b1.txt", b"x", content_type="text/plain"
                ),
            )

        self.submission_a1 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.phase_a1,
            created_by=self.user,
            status="submitted",
            input_file=self.phase_a1.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
        )
        self.submission_b1 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.phase_b1,
            created_by=self.user,
            status="submitted",
            input_file=self.phase_b1.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
        )

        self.model_admin = SubmissionAdmin(Submission, AdminSite())

    def tearDown(self):
        if os.path.exists("/tmp/evalai_test_filters_phase"):
            shutil.rmtree("/tmp/evalai_test_filters_phase")

    def _request(self, get_dict=None):
        req = type("Request", (), {"GET": get_dict or {}})()
        return req

    def _get_filter(self, request):
        return ActiveChallengePhaseFilter(
            request, {}, Submission, self.model_admin
        )

    def test_lookups_when_challenge_selected_returns_only_that_challenges_phases(
        self,
    ):
        request = self._request({"challenge": str(self.challenge_a.id)})
        filter_instance = self._get_filter(request)
        lookups = filter_instance.lookups(request, self.model_admin)

        lookup_phase_names = [label for (_pk, label) in lookups]
        self.assertIn("Phase A1", lookup_phase_names)
        self.assertIn("Phase A2", lookup_phase_names)
        self.assertNotIn("Phase B1", lookup_phase_names)
        self.assertEqual(len(lookups), 2)

    def test_lookups_when_challenge_not_selected_returns_phases_from_top_active_only(
        self,
    ):
        """When no challenge selected, only phases from top active challenges appear."""
        request = self._request()
        filter_instance = self._get_filter(request)
        lookups = filter_instance.lookups(request, self.model_admin)

        lookup_labels = [label for (_pk, label) in lookups]
        # challenge_a and challenge_b have recent submissions, so their phases
        # appear
        self.assertTrue(
            any(
                "Challenge A" in label and "Phase A1" in label
                for label in lookup_labels
            )
        )
        self.assertTrue(
            any(
                "Challenge B" in label and "Phase B1" in label
                for label in lookup_labels
            )
        )
        self.assertEqual(len(lookups), 3)

    def test_lookups_when_no_challenge_selected_excludes_phases_from_inactive_challenges(
        self,
    ):
        """Phases from challenges without recent submissions should not appear."""
        now = timezone.now()
        inactive_challenge = Challenge.objects.create(
            title="Inactive Challenge",
            start_date=now - timedelta(days=60),
            end_date=now - timedelta(days=40),
            published=True,
            approved_by_admin=True,
            is_disabled=False,
            creator=self.challenge_host_team,
        )
        with self.settings(MEDIA_ROOT="/tmp/evalai_test_filters_phase"):
            inactive_phase = ChallengePhase.objects.create(
                name="Inactive Phase",
                codename="inactive-phase",
                description="Desc",
                leaderboard_public=False,
                is_public=True,
                start_date=now - timedelta(days=60),
                end_date=now - timedelta(days=40),
                challenge=inactive_challenge,
                test_annotation=SimpleUploadedFile(
                    "inactive.txt", b"x", content_type="text/plain"
                ),
            )
        sub_inactive = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=inactive_phase,
            created_by=self.user,
            status="submitted",
            input_file=inactive_phase.test_annotation,
            method_name="Test",
            method_description="Desc",
            project_url="http://test/",
            publication_url="http://test/",
        )
        Submission.objects.filter(pk=sub_inactive.pk).update(
            submitted_at=now - timedelta(days=45)
        )

        request = self._request()
        filter_instance = self._get_filter(request)
        lookups = filter_instance.lookups(request, self.model_admin)
        lookup_labels = [label for (_pk, label) in lookups]

        # Inactive challenge's phase should NOT appear
        self.assertFalse(
            any("Inactive Challenge" in label for label in lookup_labels)
        )

    def test_lookups_when_no_challenge_selected_returns_empty_if_no_top_challenges(
        self,
    ):
        """When no top challenges exist, phase lookups return empty list."""
        Submission.objects.filter(
            submitted_at__gte=timezone.now() - timedelta(days=30)
        ).delete()

        request = self._request()
        filter_instance = self._get_filter(request)
        lookups = filter_instance.lookups(request, self.model_admin)

        self.assertEqual(lookups, [])

    def test_queryset_filters_by_phase_when_value_set(self):
        request = self._request()
        filter_instance = self._get_filter(request)
        filter_instance.value = lambda: str(self.phase_a1.id)

        base_queryset = Submission.objects.all()
        filtered = filter_instance.queryset(request, base_queryset)

        self.assertIn(self.submission_a1, filtered)
        self.assertNotIn(self.submission_b1, filtered)
        self.assertEqual(filtered.count(), 1)

    def test_queryset_returns_all_when_no_value(self):
        request = self._request()
        filter_instance = self._get_filter(request)
        filter_instance.value = lambda: None

        base_queryset = Submission.objects.all()
        filtered = filter_instance.queryset(request, base_queryset)

        self.assertIn(self.submission_a1, filtered)
        self.assertIn(self.submission_b1, filtered)
        self.assertEqual(filtered.count(), 2)
