from datetime import timedelta

from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge, ChallengePhase
from participants.models import Participant, ParticipantTeam
from jobs.models import Submission
from hosts.models import ChallengeHostTeam
from django.test import override_settings

@override_settings(
    MIDDLEWARE=[
        mw for mw in (
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'django.middleware.clickjacking.XFrameOptionsMiddleware',
        )
    ]
)
class TestSubmissionWorkflow(APITestCase):
    def setUp(self):
        self.client = APIClient()

        # user
        self.user = User.objects.create_user(
            username="user",
            email="user@test.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)

        # participant team
        self.participant_team = ParticipantTeam.objects.create(
            team_name="team",
            created_by=self.user,
        )
        Participant.objects.create(
            user=self.user,
            team=self.participant_team,
            status=Participant.SELF,
        )
        # challenge host team 
        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Host Team",
            created_by=self.user,
)

        self.challenge = Challenge.objects.create(
            title="Test Challenge",
            creator=self.challenge_host_team,  
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=2),
            published=True,
            approved_by_admin=True,
)      
        self.challenge.participant_teams.add(self.participant_team)

        # INACTIVE phase
        self.challenge_phase = ChallengePhase.objects.create(
            name="Phase 1",
            challenge=self.challenge,
            start_date=timezone.now() - timedelta(days=10),
            end_date=timezone.now() - timedelta(days=5),
            is_public=True,
        )

        self.url = reverse(
            "jobs:challenge_submission",
            kwargs={
                "challenge_id": self.challenge.pk,
                "challenge_phase_id": self.challenge_phase.pk,
            },
        )

    def test_submission_rejected_when_phase_inactive(self):
        """
        Ensure submissions are rejected and no Submission object is created
        when the challenge phase is inactive.
        """
        before_count = Submission.objects.count()

        response = self.client.post(self.url, data={},format = 'multipart')

        self.assertIn(response.status_code, (403,406))
        self.assertEqual(Submission.objects.count(), before_count)
