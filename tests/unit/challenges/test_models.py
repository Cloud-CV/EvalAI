import json
import os
import shutil

from datetime import timedelta

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth.models import User
from django.utils import timezone

from challenges.models import (
    Challenge,
    ChallengePhase,
    ChallengePhaseSplit,
    DatasetSplit,
    Leaderboard,
    LeaderboardData,
)
from hosts.models import ChallengeHostTeam
from jobs.models import Submission
from participants.models import ParticipantTeam


class BaseTestCase(TestCase):
    def setUp(self):

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
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
            published=False,
            enable_forum=True,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
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
                is_public=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                max_submissions_per_day=100000,
                max_submissions=100000,
                is_restricted_to_select_one_submission=True,
            )

        self.dataset_split = DatasetSplit.objects.create(
            name="Test Dataset Split", codename="test-split"
        )

        self.leaderboard = Leaderboard.objects.create(
            schema=json.dumps({"hello": "world"})
        )

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            dataset_split=self.dataset_split,
            challenge_phase=self.challenge_phase,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC,
        )


class ChallengeTestCase(BaseTestCase):
    def setUp(self):
        super(ChallengeTestCase, self).setUp()

        try:
            os.makedirs("/tmp/evalai")
        except OSError:
            pass

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge.image = SimpleUploadedFile(
                "test_sample_file.jpg",
                b"Dummy image content",
                content_type="image",
            )
            self.challenge.evaluation_script = SimpleUploadedFile(
                "test_sample_file.zip",
                b"Dummy zip content",
                content_type="zip",
            )
        self.challenge.save()

    def tearDown(self):
        shutil.rmtree("/tmp/evalai")

    def test__str__(self):
        self.assertEqual(self.challenge.title, self.challenge.__str__())

    def test_is_active_when_challenge_is_active(self):
        self.assertEqual(True, self.challenge.is_active)

    def test_is_active_when_challenge_is_not_active(self):
        self.challenge.end_date = timezone.now() - timedelta(days=1)
        self.challenge.save()
        self.assertEqual(False, self.challenge.is_active)

    def test_get_evaluation_script_path(self):
        self.assertEqual(
            self.challenge.evaluation_script.url,
            self.challenge.get_evaluation_script_path(),
        )

    def test_get_evaluation_script_path_when_file_is_none(self):
        self.challenge.evaluation_script = None
        self.challenge.save()
        self.assertEqual(None, self.challenge.get_evaluation_script_path())

    def test_get_image_url(self):
        self.assertEqual(
            self.challenge.image.url, self.challenge.get_image_url()
        )

    def test_get_image_url_when_image_is_none(self):
        self.challenge.image = None
        self.challenge.save()
        self.assertEqual(None, self.challenge.get_image_url())

    def test_get_start_date(self):
        self.assertEqual(
            self.challenge.start_date, self.challenge.get_start_date()
        )

    def test_get_end_date(self):
        self.assertEqual(
            self.challenge.end_date, self.challenge.get_end_date()
        )


class DatasetSplitTestCase(BaseTestCase):
    def setUp(self):
        super(DatasetSplitTestCase, self).setUp()
        self.dataset_split = DatasetSplit.objects.create(
            name="Name", codename="Codename"
        )

    def test__str__(self):
        self.assertEqual(self.dataset_split.name, self.dataset_split.__str__())


class ChallengePhaseTestCase(BaseTestCase):
    def setUp(self):
        super(ChallengePhaseTestCase, self).setUp()

    def tearDown(self):
        shutil.rmtree("/tmp/evalai")

    def test__str__(self):
        self.assertEqual(
            self.challenge_phase.name, self.challenge_phase.__str__()
        )

    def test_is_active(self):
        self.assertEqual(True, self.challenge_phase.is_active)

    def test_is_active_when_challenge_phase_is_not_active(self):
        self.challenge_phase.end_date = timezone.now() - timedelta(days=1)
        self.challenge_phase.save()
        self.assertEqual(False, self.challenge_phase.is_active)

    def test_get_start_date(self):
        self.assertEqual(
            self.challenge_phase.start_date,
            self.challenge_phase.get_start_date(),
        )

    def test_get_end_date(self):
        self.assertEqual(
            self.challenge_phase.end_date, self.challenge_phase.get_end_date()
        )

    def test_is_restricted_to_select_one_submission(self):
        self.assertEqual(
            True, self.challenge_phase.is_restricted_to_select_one_submission
        )


class LeaderboardTestCase(BaseTestCase):
    def setUp(self):
        super(LeaderboardTestCase, self).setUp()
        self.leaderboard = Leaderboard.objects.create(
            schema=json.dumps({"hello": "world"})
        )

    def test__str__(self):
        instance_id = str(self.leaderboard.id)
        self.assertEqual(instance_id, self.leaderboard.__str__())


class ChallengePhaseSplitTestCase(BaseTestCase):
    def setUp(self):
        super(ChallengePhaseSplitTestCase, self).setUp()

    def tearDown(self):
        shutil.rmtree("/tmp/evalai")

    def test__str__(self):
        challenge_phase_name = self.challenge_phase_split.challenge_phase.name
        dataset_split_name = self.challenge_phase_split.dataset_split.name
        string_to_compare = "{} : {}".format(
            challenge_phase_name, dataset_split_name
        )
        self.assertEqual(
            string_to_compare, self.challenge_phase_split.__str__()
        )


class LeaderboardDataTestCase(BaseTestCase):
    def setUp(self):
        super(LeaderboardDataTestCase, self).setUp()

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team for Challenge", created_by=self.user
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            is_public=True,
        )

        self.leaderboard_data = LeaderboardData.objects.create(
            challenge_phase_split=self.challenge_phase_split,
            submission=self.submission,
            leaderboard=self.leaderboard,
            result=json.dumps({"hello": "world"}),
        )

    def test__str__(self):
        self.assertEqual(
            "{0} : {1}".format(self.challenge_phase_split, self.submission),
            self.leaderboard_data.__str__(),
        )
