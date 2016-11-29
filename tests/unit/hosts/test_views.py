from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from hosts.models import ChallengeHostTeam


class BaseAPITestClass(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            password='secret_password')

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.client.force_authenticate(user=self.user)


class GetChallengeHostTeamTest(BaseAPITestClass):
    url = reverse_lazy('hosts:get_challenge_host_team_list')

    def test_get_challenge_host_team(self):
        expected = [
            {
                "id": self.challenge_host_team.pk,
                "team_name": self.challenge_host_team.team_name,
                "created_by": self.challenge_host_team.created_by.pk
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateChallengeHostTeamTest(BaseAPITestClass):
    url = reverse_lazy('hosts:get_challenge_host_team_list')

    def setUp(self):
        super(CreateChallengeHostTeamTest, self).setUp()
        self.data = {
            'team_name': 'Test team'
        }

    def test_create_challenge_host_team_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_host_team_with_no_data(self):
        del self.data['team_name']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetParticularChallengeHostTeam(BaseAPITestClass):

    def setUp(self):
        super(GetParticularChallengeHostTeam, self).setUp()
        self.url = reverse_lazy('hosts:get_challenge_host_team_details', kwargs={'pk': self.challenge_host_team.pk})

    def test_get_particular_challenge_host_team(self):
        expected = {
            "id": self.challenge_host_team.pk,
            "team_name": self.challenge_host_team.team_name,
            "created_by": self.user.id
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UpdateParticularChallengeHostTeam(BaseAPITestClass):

    def setUp(self):
        super(UpdateParticularChallengeHostTeam, self).setUp()
        self.url = reverse_lazy('hosts:get_challenge_host_team_details', kwargs={'pk': self.challenge_host_team.pk})
        self.data = {
            'team_name': 'Test Team'
        }
        self.partial_update_team_name = 'Partial Update Test Team'
        self.update_team_name = 'All Update Test Team'

    def test_particular_challenge_host_team_partial_update(self):
        self.data = {
            'team_name': self.partial_update_team_name
        }
        expected = {
            "id": self.challenge_host_team.pk,
            "team_name": self.partial_update_team_name,
            "created_by": self.user.id
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_update(self):
        self.data = {
            'team_name': self.update_team_name
        }
        expected = {
            "id": self.challenge_host_team.pk,
            "team_name": self.update_team_name,
            "created_by": self.user.id
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_update_with_no_data(self):
        self.data = {
            'team_name': ''
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_particular_challenge_host_team_does_not_exist(self):
        self.url = reverse_lazy('hosts:get_challenge_host_team_details', kwargs={'pk': self.challenge_host_team.pk + 1})
        expected = {
            'error': 'ChallengeHostTeam does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class DeleteParticularChallengeHostTeam(BaseAPITestClass):

    def setUp(self):
        super(DeleteParticularChallengeHostTeam, self).setUp()
        self.url = reverse_lazy('hosts:get_challenge_host_team_details', kwargs={'pk': self.challenge_host_team.pk})

    def test_particular_challenge_host_team_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
