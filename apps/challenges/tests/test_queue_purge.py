from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from django.urls import reverse
from challenges.models import Challenge, ChallengePhase
from hosts.models import ChallengeHostTeam, ChallengeHost
from unittest.mock import patch

class QueuePurgeAPITestCase(APITestCase):

    def setUp(self):
        # Create a user and challenge host team
        self.user = User.objects.create_user(username='hostuser', password='testpass')
        self.host_team = ChallengeHostTeam.objects.create(team_name='Host Team', created_by=self.user)
        self.challenge = Challenge.objects.create(title='Test Challenge', creator=self.host_team, published=True)
        self.challenge_phase = ChallengePhase.objects.create(name='Phase 1', challenge=self.challenge)

        # Make host relationship
        self.challenge_host = ChallengeHost.objects.create(user=self.user, team_name=self.host_team, status=ChallengeHost.ACCEPTED)
        self.url = reverse('purge_challenge_queue', kwargs={'challenge_pk': self.challenge.pk})

    def test_purge_unauthenticated(self):
        response = self.client.post(self.url, {'scope': 'all', 'dry_run': False})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_purge_forbidden_for_non_host(self):
        non_host_user = User.objects.create_user(username='nonhost', password='pass')
        self.client.force_authenticate(user=non_host_user)
        response = self.client.post(self.url, {'scope': 'all', 'dry_run': False})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    @patch('challenges.services.QueuePurgeService.purge_queue')
    def test_purge_success(self, mock_purge):
        mock_purge.return_value = {
            'purged': {'pending': 5, 'running': 2, 'total': 7},
            'skipped': 0,
            'took_ms': 123,
            'notes': 'Purged successfully',
            'queues': ['submission_1_1']
        }
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'scope': 'all', 'dry_run': False})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('purged', response.data)
        self.assertEqual(response.data['purged']['total'], 7)

    def test_purge_invalid_scope(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.post(self.url, {'scope': 'invalid-scope', 'dry_run': False})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_purge_challenge_not_found(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('purge_challenge_queue', kwargs={'challenge_pk': 9999})
        response = self.client.post(url, {'scope': 'all', 'dry_run': False})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
