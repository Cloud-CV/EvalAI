from django.urls import reverse_lazy
from rest_framework.test import APITestCase, APIClient
import unittest
from hosts.models import ChallengeHost, ChallengeHostTeam

class BaseAPITestClass(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            email="user@test.com",
            password='secret_password')

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Team_name',
            created_by=self.user)

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN)

        self.client.force_authenticate(user=self.user)

class TestStringMethods(unittest.TestCase,BaseAPITestClass):
	def test_a(self):
		print self
		url = reverse_lazy('hosts:get_challenge_host_team_list')
		self.assertEqual(url, '/api/hosts/challenge_host_team/')
		
		url = reverse_lazy('hosts:get_challenge_host_team_details',kwargs={'pk': self.challenge_host.pk})
		print url
		self.assertEqual(url, '/challenge_host_team/1')
		
		url = reverse_lazy('hosts:create_challenge_host_team')
		print url
		self.assertEqual(url, '/create_challenge_host_team/')

		url = reverse_lazy('get_challenge_host_list',kwargs={'challenge_host_team_pk':self.challenge_host_team.pk})
		print url
		self.assertEqual(url, '/challenge_host_team/1/challenge_host/')

		url = reverse_lazy('get_challenge_host_list',kwargs={'challenge_host_team_pk':self.challenge_host_team.pk})
		print url
		self.assertEqual(url, '/challenge_host_team/1/challenge_host/')

		url = reverse_lazy('get_challenge_host_details',kwargs={'challenge_host_team_pk':self.challenge_host_team.pk,'pk':self.challenge_host.pk})
		print url
		self.assertEqual(url, '/challenge_host_team/1/challenge_host/1')

		url = reverse_lazy('gremove_self_from_challenge_host_team',kwargs={'challenge_host_team_pk':self.challenge_host_team.pk})
		print url
		self.assertEqual(url, '/remove_self_from_challenge_host/1')


	if __name__ == '__main__':
unittest.main()
