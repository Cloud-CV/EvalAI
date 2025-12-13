from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.test import TestCase, modify_settings 
from django.contrib.auth.models import User

from challenges.models import Challenge, ChallengePhase
from participants.models import ParticipantTeam
from jobs.models import Submission
from hosts.models import ChallengeHostTeam
from django.utils import timezone

@modify_settings(MIDDLEWARE={'remove': 'silk.middleware.SilkyMiddleware'})

class PurgeSubmissionsTest(TestCase):
    def setUp(self):

        self.user = User.objects.create_user(username='host_user', email='host@test.com', password='password')
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.host_team = ChallengeHostTeam.objects.create(team_name='Host Team', created_by=self.user)
        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            creator=self.host_team,
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=10)
        )
        self.phase = ChallengePhase.objects.create(name='Phase 1', challenge=self.challenge)

        self.participant_team = ParticipantTeam.objects.create(team_name='Part Team', created_by=self.user)
        self.submission = Submission.objects.create(
            participant_team=self.participant_team,
            challenge_phase=self.phase,
            created_by=self.user,
            status='submitted',  
            input_file='fake.txt'
        )

    def test_purge_stuck_submissions(self):

        self.assertEqual(Submission.objects.count(), 1)

        url = reverse('challenges:purge_stuck_submissions', args=[self.challenge.id])
        
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Submission.objects.count(), 0) 
        print("\n TEST PASSED: Stuck submission was purged successfully.")

    def test_purge_access_denied_for_non_host(self):
        """
        Ensure that a random user CANNOT purge submissions for a challenge they don't own.
        """
        attacker = User.objects.create_user(username='attacker', email='bad@test.com', password='password')
        self.client.force_authenticate(user=attacker)

        url = reverse('challenges:purge_stuck_submissions', args=[self.challenge.id])
        response = self.client.post(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        
        self.assertEqual(Submission.objects.count(), 1)
        print("\n SECURITY TEST PASSED: Unauthorized user was blocked.")