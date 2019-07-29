import os
import shutil

from datetime import timedelta

from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge, ChallengePhase
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission
from participants.models import ParticipantTeam, Participant


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.user2 = User.objects.create(
            username="otheruser",
            email="otheruser@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="otheruser@test.com",
            primary=True,
            verified=True,
        )

        self.user3 = User.objects.create(
            username="user3",
            email="user3@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user3,
            email="user3@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            short_description="Short description for test challenge",
            description="Description for test challenge",
            terms_and_conditions="Terms and conditions for test challenge",
            submission_guidelines="Submission guidelines for test challenge",
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.challenge1 = Challenge.objects.create(
            title="Test Challenge 1",
            short_description="Short description for test challenge 1",
            description="Description for test challenge 1",
            terms_and_conditions="Terms and conditions for test challenge 1",
            submission_guidelines="Submission guidelines for test challenge 1",
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.challenge2 = Challenge.objects.create(
            title="Test Challenge 2",
            short_description="Short description for test challenge 2",
            description="Description for test challenge 2",
            terms_and_conditions="Terms and conditions for test challenge 2",
            submission_guidelines="Submission guidelines for test challenge 2",
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user2
        )

        self.participant_team3 = ParticipantTeam.objects.create(
            team_name="Participant Team3", created_by=self.user3
        )

        self.participant = Participant.objects.create(
            user=self.user2,
            status=Participant.SELF,
            team=self.participant_team,
        )

        self.participant3 = Participant.objects.create(
            user=self.user3,
            status=Participant.SELF,
            team=self.participant_team3,
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
                codename="Phase Code Name",
            )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase1 = ChallengePhase.objects.create(
                name="Challenge Phase 1",
                description="Description for Challenge Phase 1",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge1,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                codename="Phase Code Name1",
            )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase2 = ChallengePhase.objects.create(
                name="Challenge Phase 2",
                description="Description for Challenge Phase 1",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge1,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                codename="Phase Code Name2",
            )

        with self.settings(MEDIA_ROOT="/tmp/evalai"):
            self.challenge_phase3 = ChallengePhase.objects.create(
                name="Challenge Phase 3",
                description="Description for Challenge Phase 3",
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge2,
                test_annotation=SimpleUploadedFile(
                    "test_sample_file.txt",
                    b"Dummy file content",
                    content_type="text/plain",
                ),
                codename="Phase Code Name2",
            )
        self.client.force_authenticate(user=self.user)

    def tearDown(self):
        shutil.rmtree("/tmp/evalai")


class GetParticipantTeamTest(BaseAPITestClass):
    def setUp(self):
        super(GetParticipantTeamTest, self).setUp()
        self.url = reverse_lazy(
            "analytics:get_participant_team_count",
            kwargs={"challenge_pk": self.challenge.pk},
        )

        self.challenge.participant_teams.add(self.participant_team)

    def test_get_participant_team_count(self):

        expected = {"participant_team_count": 1}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_participant_team_count_when_challenge_does_not_exist(self):

        self.url = reverse_lazy(
            "analytics:get_participant_team_count",
            kwargs={"challenge_pk": self.challenge.pk + 10},
        )

        expected = {
            "detail": "Challenge {} does not exist".format(
                self.challenge.pk + 10
            )
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetParticipantCountTest(BaseAPITestClass):
    def setUp(self):
        super(GetParticipantCountTest, self).setUp()
        self.url = reverse_lazy(
            "analytics:get_participant_count",
            kwargs={"challenge_pk": self.challenge.pk},
        )

        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.participant_teams.add(self.participant_team3)

    def test_get_participant_team_count(self):

        expected = {"participant_count": 2}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_participant_team_count_when_challenge_doe_not_exist(self):

        self.url = reverse_lazy(
            "analytics:get_participant_count",
            kwargs={"challenge_pk": self.challenge.pk + 10},
        )

        expected = {
            "detail": "Challenge {} does not exist".format(
                self.challenge.pk + 10
            )
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetSubmissionCountForChallengeTest(BaseAPITestClass):
    def setUp(self):
        super(GetSubmissionCountForChallengeTest, self).setUp()
        self.url = reverse_lazy(
            "analytics:get_submission_count",
            kwargs={"challenge_id": self.challenge.pk, "duration": "DAILY"},
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

    def test_get_participant_team_count_when_challenge_does_not_exist(self):

        self.url = reverse_lazy(
            "analytics:get_submission_count",
            kwargs={
                "challenge_pk": self.challenge.pk + 10,
                "duration": "DAILY",
            },
        )

        expected = {
            "detail": "Challenge {} does not exist".format(
                self.challenge.pk + 10
            )
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_incorrect_url_pattern_submission_count(self):
        self.url = reverse_lazy(
            "analytics:get_submission_count",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "duration": "INCORRECT",
            },
        )
        expected = {"error": "Wrong URL pattern!"}
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.data, expected)

    def test_get_daily_submission_count(self):
        self.url = reverse_lazy(
            "analytics:get_submission_count",
            kwargs={"challenge_pk": self.challenge.pk, "duration": "DAILY"},
        )
        expected = {"submission_count": 1}
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_get_weekly_submission_count(self):
        self.url = reverse_lazy(
            "analytics:get_submission_count",
            kwargs={"challenge_pk": self.challenge.pk, "duration": "WEEKLY"},
        )
        expected = {"submission_count": 1}
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_get_monthly_submission_count(self):
        self.url = reverse_lazy(
            "analytics:get_submission_count",
            kwargs={"challenge_pk": self.challenge.pk, "duration": "MONTHLY"},
        )
        expected = {"submission_count": 1}
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)

    def test_get_all_submission_count(self):
        self.url = reverse_lazy(
            "analytics:get_submission_count",
            kwargs={"challenge_pk": self.challenge.pk, "duration": "ALL"},
        )
        expected = {"submission_count": 1}
        response = self.client.get(self.url, {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected)


class ChallengePhaseSubmissionCountByTeamTest(BaseAPITestClass):
    def setUp(self):
        super(ChallengePhaseSubmissionCountByTeamTest, self).setUp()
        self.url = reverse_lazy(
            "analytics:get_challenge_phase_submission_count_by_team",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission2 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission3 = Submission.objects.create(
            participant_team=self.participant_team3,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team3.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission4 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

    def test_get_challenge_phase_submission_count_by_team_when_challenge_does_not_exist(
        self
    ):
        self.url = reverse_lazy(
            "analytics:get_challenge_phase_submission_count_by_team",
            kwargs={
                "challenge_pk": self.challenge.pk + 10,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )

        expected = {
            "detail": "Challenge {} does not exist".format(
                self.challenge.pk + 10
            )
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_challenge_phase_submission_count_by_team_when_challenge_phase_does_not_exist(
        self
    ):
        self.url = reverse_lazy(
            "analytics:get_challenge_phase_submission_count_by_team",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk + 10,
            },
        )

        expected = {
            "detail": "ChallengePhase {} does not exist".format(
                self.challenge_phase.pk + 10
            )
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_challenge_phase_submission_count_by_team_for_participant_team_1(
        self
    ):
        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.participant_teams.add(self.participant_team3)

        self.url = reverse_lazy(
            "analytics:get_challenge_phase_submission_count_by_team",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )

        expected = {
            "participant_team_submission_count": self.participant_team.submissions.count(),
            "challenge_phase": self.challenge_phase.pk,
        }
        self.client.force_authenticate(user=self.user2)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_phase_submission_count_by_team_for_participant_team_3(
        self
    ):
        self.challenge.participant_teams.add(self.participant_team)
        self.challenge.participant_teams.add(self.participant_team3)

        self.url = reverse_lazy(
            "analytics:get_challenge_phase_submission_count_by_team",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )

        expected = {
            "participant_team_submission_count": self.participant_team3.submissions.count(),
            "challenge_phase": self.challenge_phase.pk,
        }
        self.client.force_authenticate(user=self.user3)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class ChallengePhaseSubmissionAnalyticsTest(BaseAPITestClass):
    def setUp(self):
        super(ChallengePhaseSubmissionAnalyticsTest, self).setUp()
        self.url = reverse_lazy(
            "analytics:get_challenge_phase_submission_analysis",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )

        self.submission1 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission2 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team.created_by,
            status="running",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission3 = Submission.objects.create(
            participant_team=self.participant_team3,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team3.created_by,
            status="failed",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission4 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team.created_by,
            status="cancelled",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission5 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team.created_by,
            status="finished",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission6 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team.created_by,
            status="finished",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission7 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.participant_team.created_by,
            status="submitting",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

    def test_get_challenge_phase_submission_analysis_when_challenge_does_not_exist(
        self
    ):
        self.url = reverse_lazy(
            "analytics:get_challenge_phase_submission_analysis",
            kwargs={
                "challenge_pk": self.challenge.pk + 10,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )

        expected = {
            "detail": "Challenge {} does not exist".format(
                self.challenge.pk + 10
            )
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_challenge_phase_submission_analysis_when_challenge_phase_does_not_exist(
        self
    ):
        self.url = reverse_lazy(
            "analytics:get_challenge_phase_submission_analysis",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk + 10,
            },
        )

        expected = {
            "detail": "ChallengePhase {} does not exist".format(
                self.challenge_phase.pk + 10
            )
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_challenge_phase_submission_analysis(self):
        self.url = reverse_lazy(
            "analytics:get_challenge_phase_submission_analysis",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )
        setattr(self.submission1, "is_flagged", True)
        setattr(self.submission1, "is_public", True)
        self.submission1.save()

        submissions = Submission.objects.filter(
            challenge_phase=self.challenge_phase,
            challenge_phase__challenge=self.challenge,
        )

        expected = {
            "total_submissions": submissions.count(),
            "participant_team_count": submissions.values("participant_team")
            .distinct()
            .count(),
            "flagged_submissions_count": submissions.filter(
                is_flagged=True
            ).count(),
            "public_submissions_count": submissions.filter(
                is_public=True
            ).count(),
            "challenge_phase": self.challenge_phase.pk,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GetLastSubmissionTimeTest(BaseAPITestClass):
    def setUp(self):
        super(GetLastSubmissionTimeTest, self).setUp()
        self.url = reverse_lazy(
            "analytics:get_last_submission_time",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_by": "challenge",
            },
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

    def test_get_last_submission_time_when_challenge_does_not_exists(self):
        self.url = reverse_lazy(
            "analytics:get_last_submission_time",
            kwargs={
                "challenge_pk": self.challenge.pk + 10,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_by": "challenge",
            },
        )
        expected = {
            "detail": "Challenge {} does not exist".format(
                self.challenge.pk + 10
            )
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_last_submission_time_when_challenge_phase_does_not_exists(
        self
    ):
        self.url = reverse_lazy(
            "analytics:get_last_submission_time",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk + 10,
                "submission_by": "challenge",
            },
        )
        expected = {
            "detail": "ChallengePhase {} does not exist".format(
                self.challenge_phase.pk + 10
            )
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_last_submission_time_when_submission_by_is_user(self):
        self.url = reverse_lazy(
            "analytics:get_last_submission_time",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_by": "user",
            },
        )
        expected = {
            "last_submission_datetime": "{0}{1}".format(
                self.submission.created_at.isoformat(), "Z"
            ).replace("+00:00", "")
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_last_submission_time_when_url_is_incorrect(self):
        self.url = reverse_lazy(
            "analytics:get_last_submission_time",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
                "submission_by": "other",
            },
        )
        expected = {"error": "Page not found!"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GetLastSubmissionDateTimeAnalysisTest(BaseAPITestClass):
    def setUp(self):
        super(GetLastSubmissionDateTimeAnalysisTest, self).setUp()
        self.url = reverse_lazy(
            "analytics:get_last_submission_datetime_analysis",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )

        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

        self.submission1 = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.challenge_phase1,
            created_by=self.challenge_host_team.created_by,
            status="submitted",
            input_file=self.challenge_phase1.test_annotation,
            method_name="Test Method",
            method_description="Test Description",
            project_url="http://testserver/",
            publication_url="http://testserver/",
            is_public=True,
        )

    def test_get_last_submission_datetime_when_challenge_does_not_exists(self):
        self.url = reverse_lazy(
            "analytics:get_last_submission_datetime_analysis",
            kwargs={
                "challenge_pk": self.challenge.pk + 10,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )
        expected = {
            "detail": "Challenge {} does not exist".format(
                self.challenge.pk + 10
            )
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_last_submission_datetime_when_challenge_phase_does_not_exists(
        self
    ):
        self.url = reverse_lazy(
            "analytics:get_last_submission_datetime_analysis",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk + 10,
            },
        )
        expected = {
            "detail": "ChallengePhase {} does not exist".format(
                self.challenge_phase.pk + 10
            )
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_last_submission_datetime_when_no_submission_is_made_to_challenge(
        self
    ):
        self.url = reverse_lazy(
            "analytics:get_last_submission_datetime_analysis",
            kwargs={
                "challenge_pk": self.challenge2.pk,
                "challenge_phase_pk": self.challenge_phase3.pk,
            },
        )
        expected = {
            "message": "You dont have any submissions in this challenge!"
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_last_submission_datetime_when_no_submission_is_made_to_challenge_phase(
        self
    ):
        self.url = reverse_lazy(
            "analytics:get_last_submission_datetime_analysis",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase2.pk,
            },
        )

        datetime = self.submission.created_at.isoformat()
        expected = {
            "last_submission_timestamp_in_challenge_phase": "You dont have any submissions in this challenge phase!",
            "last_submission_timestamp_in_challenge": "{0}{1}".format(
                datetime, "Z"
            ).replace("+00:00", ""),
            "challenge_phase": self.challenge_phase.pk,
        }
        response = self.client.get(self.url, {})
        response_data = {
            "last_submission_timestamp_in_challenge_phase": "You dont have any submissions in this challenge phase!",
            "last_submission_timestamp_in_challenge": "{0}{1}".format(
                datetime, "Z"
            ).replace("+00:00", ""),
            "challenge_phase": self.challenge_phase.pk,
        }
        self.assertEqual(response_data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_last_submission_datetime_analysis(self):
        self.url = reverse_lazy(
            "analytics:get_last_submission_datetime_analysis",
            kwargs={
                "challenge_pk": self.challenge.pk,
                "challenge_phase_pk": self.challenge_phase.pk,
            },
        )

        datetime = self.submission.created_at.isoformat()
        expected = {
            "last_submission_timestamp_in_challenge_phase": "{0}{1}".format(
                datetime, "Z"
            ).replace("+00:00", ""),
            "last_submission_timestamp_in_challenge": "{0}{1}".format(
                datetime, "Z"
            ).replace("+00:00", ""),
            "challenge_phase": self.challenge_phase.pk,
        }
        response = self.client.get(self.url, {})
        datetime = response.data[
            "last_submission_timestamp_in_challenge_phase"
        ].isoformat()
        response_data = {
            "last_submission_timestamp_in_challenge_phase": "{0}{1}".format(
                datetime, "Z"
            ).replace("+00:00", ""),
            "last_submission_timestamp_in_challenge": "{0}{1}".format(
                datetime, "Z"
            ).replace("+00:00", ""),
            "challenge_phase": self.challenge_phase.pk,
        }
        self.assertEqual(response_data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
