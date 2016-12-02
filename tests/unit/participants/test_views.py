from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge
from hosts.models import ChallengeHostTeam
from participants.models import ParticipantTeam


class BaseAPITestClass(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            password='secret_password')

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            description='Description for test challenge',
            terms_and_conditions='Terms and conditions for test challenge',
            submission_guidelines='Submission guidelines for test challenge',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False)

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team',
            challenge=self.challenge,
            created_by=self.user)

        self.client.force_authenticate(user=self.user)


class GetParticipantTeamTest(BaseAPITestClass):

    def setUp(self):
        super(GetParticipantTeamTest, self).setUp()
        self.url = reverse_lazy('participants:get_participant_team_list',
                                kwargs={'challenge_pk': self.challenge.pk})

    def test_get_challenge(self):
        expected = [
            {
                "id": self.participant_team.pk,
                "team_name": self.participant_team.team_name,
                "challenge": {
                    "id": self.challenge.pk,
                    "title": self.challenge.title,
                    "description": self.challenge.description,
                    "terms_and_conditions": self.challenge.terms_and_conditions,
                    "submission_guidelines": self.challenge.submission_guidelines,
                    "evaluation_details": self.challenge.evaluation_details,
                    "image": None,
                    "start_date": None,
                    "end_date": None,
                    "creator": {
                        "id": self.challenge.creator.pk,
                        "team_name": self.challenge.creator.team_name,
                        "created_by": self.challenge.creator.created_by.pk
                    },
                    "published": self.challenge.published,
                    "enable_forum": self.challenge.enable_forum,
                    "anonymous_leaderboard": self.challenge.anonymous_leaderboard
                },
                "created_by": self.user.pk
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_for_participant_team_does_not_exist(self):
        self.url = reverse_lazy('participants:get_participant_team_list',
                                kwargs={'challenge_pk': self.challenge.pk + 1})
        expected = {
            'error': 'Challenge does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class CreateParticipantTeamTest(BaseAPITestClass):

    def setUp(self):
        super(CreateParticipantTeamTest, self).setUp()
        self.url = reverse_lazy('participants:get_participant_team_list',
                                kwargs={'challenge_pk': self.challenge.pk})
        self.data = {
            'team_name': 'New Participant Team'
        }

    def test_create_participant_team_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_participant_team_with_no_data(self):
        del self.data['team_name']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetParticularParticipantTeam(BaseAPITestClass):

    def setUp(self):
        super(GetParticularParticipantTeam, self).setUp()
        self.url = reverse_lazy('participants:get_participant_team_details',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'pk': self.participant_team.pk})

    def test_get_particular_participant_team(self):
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.participant_team.team_name,
            "challenge": {
                "id": self.challenge.pk,
                "title": self.challenge.title,
                "description": self.challenge.description,
                "terms_and_conditions": self.challenge.terms_and_conditions,
                "submission_guidelines": self.challenge.submission_guidelines,
                "evaluation_details": self.challenge.evaluation_details,
                "image": None,
                "start_date": None,
                "end_date": None,
                "creator": {
                    "id": self.challenge.creator.pk,
                    "team_name": self.challenge.creator.team_name,
                    "created_by": self.challenge.creator.created_by.pk
                },
                "published": self.challenge.published,
                "enable_forum": self.challenge.enable_forum,
                "anonymous_leaderboard": self.challenge.anonymous_leaderboard
            },
            "created_by": self.user.pk
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_participant_team_does_not_exist(self):
        self.url = reverse_lazy('participants:get_participant_team_details',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'pk': self.participant_team.pk + 1})
        expected = {
            'error': 'ParticipantTeam does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_for_participant_team_does_not_exist(self):
        self.url = reverse_lazy('participants:get_participant_team_details',
                                kwargs={'challenge_pk': self.challenge.pk + 1,
                                        'pk': self.participant_team.pk})
        expected = {
            'error': 'Challenge does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class UpdateParticularParticipantTeam(BaseAPITestClass):

    def setUp(self):
        super(UpdateParticularParticipantTeam, self).setUp()
        self.url = reverse_lazy('participants:get_participant_team_details',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'pk': self.participant_team.pk})

        self.partial_update_participant_team_name = 'Partial Update Participant Team'
        self.update_participant_team_name = 'Update Test Participant Team'
        self.data = {
            'team_name': self.update_participant_team_name
        }

    def test_particular_participant_team_partial_update(self):
        self.partial_update_data = {
            'team_name': self.partial_update_participant_team_name
        }
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.partial_update_participant_team_name,
            "challenge": self.challenge.pk,
            "created_by": self.user.pk
        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_participant_team_update(self):
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.update_participant_team_name,
            "challenge": self.challenge.pk,
            "created_by": self.user.pk
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_participant_team_update_with_no_data(self):
        self.data = {
            'team_name': ''
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteParticularParticipantTeam(BaseAPITestClass):

    def setUp(self):
        super(DeleteParticularParticipantTeam, self).setUp()
        self.url = reverse_lazy('participants:get_participant_team_details',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'pk': self.participant_team.pk})

    def test_particular_participant_team_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
