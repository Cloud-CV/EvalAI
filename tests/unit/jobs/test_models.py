import os
import shutil
from datetime import timedelta

import pytest
import rest_framework
from challenges.models import Challenge, ChallengePhase
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.utils import timezone
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from participants.models import ParticipantTeam


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="user", email="user@test.com", password="password"
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge", created_by=self.user
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
        )

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase = ChallengePhase.objects.create(
                name="Challenge Phase",
                description="Description for Challenge Phase",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
            )

    def tearDown(self):
        shutil.rmtree("/tmp/evalai")


class SubmissionTestCase(BaseTestCase):
    def setUp(self):
        super(SubmissionTestCase, self).setUp()

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            is_public=True,
        )

    def test__str__(self):
        self.assertEqual(
            "{}".format(self.submission.id), self.submission.__str__()
        )


@pytest.mark.django_db
class TestSubmissionModel:
    def setup_method(self, method):
        self.user = User.objects.create_user(
            username="testuser", password="password"
        )
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )
        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
        )
        self.challenge_phase = ChallengePhase.objects.create(
            name="Test Phase",
            challenge=self.challenge,
            max_submissions=2,
            max_submissions_per_day=2,
            max_submissions_per_month=2,
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Test Participant Team", created_by=self.user
        )

    def test_max_submissions_per_day_reached(self):
        Submission.objects.all().delete()

        self.challenge_phase.max_submissions = 100
        self.challenge_phase.max_submissions_per_day = 2
        self.challenge_phase.max_submissions_per_month = 100
        self.challenge_phase.save()

        for _ in range(2):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now(),  # same day
            )

        with pytest.raises(
            rest_framework.exceptions.PermissionDenied,
            match=r"The maximum number of submission for today has been reached",
        ):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now(),
            )


    def test_max_submissions_limit_reached(self):
        self.challenge_phase.max_submissions = 2
        self.challenge_phase.max_submissions_per_day = 100
        self.challenge_phase.max_submissions_per_month = 100
        self.challenge_phase.save()

        Submission.objects.all().delete()
        assert Submission.objects.count() == 0

        for _ in range(2):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
            )

        with pytest.raises(
            rest_framework.exceptions.PermissionDenied,
            match=r"The maximum number of submissions has been reached",
        ):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now().replace(
                    hour=0, minute=0, second=0, microsecond=0
                ),
            )

    def test_max_submissions_per_month_reached(self):
        Submission.objects.all().delete()

        self.challenge_phase.max_submissions = 100
        self.challenge_phase.max_submissions_per_day = 100
        self.challenge_phase.max_submissions_per_month = 2
        self.challenge_phase.save()

        # Spread across days within the same month
        Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            input_file=None,
            is_public=True,
            submitted_at=timezone.now().replace(day=1),
        )

        Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.user,
            status=Submission.SUBMITTED,
            input_file=None,
            is_public=True,
            submitted_at=timezone.now().replace(day=2),
        )

        with pytest.raises(
            rest_framework.exceptions.PermissionDenied,
            match=r"The maximum number of submission for this month has been reached",
        ):
            Submission.objects.create(
                participant_team=self.participant_team,
                challenge_phase=self.challenge_phase,
                created_by=self.user,
                status=Submission.SUBMITTED,
                input_file=None,
                is_public=True,
                submitted_at=timezone.now().replace(day=3),
            )
