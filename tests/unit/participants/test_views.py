from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge
from hosts.models import ChallengeHostTeam
from participants.models import ParticipantTeam, Participant


class BaseAPITestClass(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            email="user@test.com",
            password='secret_password')

        EmailAddress.objects.create(
            user=self.user,
            email='user@test.com',
            primary=True,
            verified=True)

        self.invite_user = User.objects.create(
            username='otheruser',
            email='other@platform.com',
            password='other_secret_password')

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team',
            created_by=self.user)

        self.client.force_authenticate(user=self.user)


class GetParticipantTeamTest(BaseAPITestClass):

    url = reverse_lazy('participants:get_participant_team_list')

    def setUp(self):
        super(GetParticipantTeamTest, self).setUp()

    def test_get_challenge(self):
        expected = [
            {
                "id": self.participant_team.pk,
                "team_name": self.participant_team.team_name,
                "created_by": self.user.username
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateParticipantTeamTest(BaseAPITestClass):

    url = reverse_lazy('participants:get_participant_team_list')

    def setUp(self):
        super(CreateParticipantTeamTest, self).setUp()
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
                                kwargs={'pk': self.participant_team.pk})

    def test_get_particular_participant_team(self):
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.participant_team.team_name,
            "created_by": self.user.username
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_participant_team_does_not_exist(self):
        self.url = reverse_lazy('participants:get_participant_team_details',
                                kwargs={'pk': self.participant_team.pk + 1})
        expected = {
            'error': 'ParticipantTeam does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class UpdateParticularParticipantTeam(BaseAPITestClass):

    def setUp(self):
        super(UpdateParticularParticipantTeam, self).setUp()
        self.url = reverse_lazy('participants:get_participant_team_details',
                                kwargs={'pk': self.participant_team.pk})

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
            "created_by": self.user.username
        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_participant_team_update(self):
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.update_participant_team_name,
            "created_by": self.user.username
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
                                kwargs={'pk': self.participant_team.pk})

    def test_particular_participant_team_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class InviteParticipantToTeamTest(BaseAPITestClass):

    url = reverse_lazy('participants:invite_participant_to_team')

    def setUp(self):
        super(InviteParticipantToTeamTest, self).setUp()
        self.data = {
            'email': self.invite_user.email
        }
        self.url = reverse_lazy('participants:invite_participant_to_team',
                                kwargs={'pk': self.participant_team.pk})

    def test_invite_participant_to_team_with_all_data(self):
        expected = {
            'message': 'User has been added successfully to the team'
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_invite_participant_to_team_with_no_data(self):
        del self.data['email']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_self_to_team(self):
        self.data = {
            'email': self.user.email
        }
        expected = {
            'email': [
                'A participant cannot invite himself'
            ]
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_user_which_does_not_exist_to_team(self):
        self.data = {
            'email': 'userwhichdoesnotexist@platform.com'
        }
        expected = {
            'email': [
                'User does not exist'
            ]
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_particular_participant_team_for_invite_does_not_exist(self):
        self.url = reverse_lazy('participants:invite_participant_to_team',
                                kwargs={'pk': self.participant_team.pk + 1})
        expected = {
            'error': 'ParticipantTeam does not exist'
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class DeleteParticipantFromTeamTest(BaseAPITestClass):

    def setUp(self):
        super(DeleteParticipantFromTeamTest, self).setUp()

        self.participant1 = Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team)

        self.user2 = User.objects.create(
            username='user2',
            email='user2@platform.com',
            password='user2_password')

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team)

        self.url = reverse_lazy('participants:delete_participant_from_team',
                                kwargs={'participant_team_pk': self.participant_team.pk,
                                        'participant_pk': self.invite_user.pk
                                        })

    def test_participant_does_not_exist_in_team(self):
        self.url = reverse_lazy('participants:delete_participant_from_team',
                                kwargs={'participant_team_pk': self.participant_team.pk,
                                        'participant_pk': self.participant2.pk + 1
                                        })

        expected = {
            'error': 'Participant does not exist'
        }

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_participant_team_does_not_exist(self):
        self.url = reverse_lazy('participants:delete_participant_from_team',
                                kwargs={'participant_team_pk': self.participant_team.pk + 1,
                                        'participant_pk': self.participant2.pk
                                        })

        expected = {
            'error': 'ParticipantTeam does not exist'
        }

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_participant_is_admin_and_wants_to_delete_himself(self):
        self.url = reverse_lazy('participants:delete_participant_from_team',
                                kwargs={'participant_team_pk': self.participant_team.pk,
                                        'participant_pk': self.participant1.pk
                                        })

        expected = {
            'error': 'You are not allowed to remove yourself since you are admin. Please delete the team if you want to do so!'  # noqa: ignore=E501
        }

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_participant_does_not_have_permissions_to_remove_another_participant(self):
        self.url = reverse_lazy('participants:delete_participant_from_team',
                                kwargs={'participant_team_pk': self.participant_team.pk,
                                        'participant_pk': self.participant2.pk
                                        })

        self.user3 = User.objects.create(
            username='user3',
            email='user3@platform.com',
            password='user3_password')

        EmailAddress.objects.create(
            user=self.user3,
            email='user3@platform.com',
            primary=True,
            verified=True)

        self.participant3 = Participant.objects.create(
            user=self.user3,
            status=Participant.ACCEPTED,
            team=self.participant_team)

        self.client.force_authenticate(user=self.user3)

        expected = {
            'error': 'Sorry, you do not have permissions to remove this participant'
        }

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_when_a_participant_is_successfully_removed_from_team(self):
        self.url = reverse_lazy('participants:delete_participant_from_team',
                                kwargs={'participant_team_pk': self.participant_team.pk,
                                        'participant_pk': self.participant2.pk
                                        })
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class GetTeamsAndCorrespondingChallengesForAParticipant(BaseAPITestClass):

    def setUp(self):
        super(GetTeamsAndCorrespondingChallengesForAParticipant, self).setUp()

        self.url = reverse_lazy(
            'participants:get_teams_and_corresponding_challenges_for_a_participant',)

        self.user2 = User.objects.create(
            username='user2',
            email='user2@platform.com',
            password='user2_password')

        EmailAddress.objects.create(
            user=self.user2,
            email='user2@platform.com',
            primary=True,
            verified=True)

        self.participant_team1 = ParticipantTeam.objects.create(
            team_name='Team A',
            created_by=self.user)

        self.participant_team2 = ParticipantTeam.objects.create(
            team_name='Team B',
            created_by=self.user2)  # created by user2 and not user

        self.participant1 = Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team1)

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team2)

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Host Team 1',
            created_by=self.user2)

        self.challenge1 = Challenge.objects.create(
            title='Test Challenge 1',
            description='Description for test challenge 1',
            terms_and_conditions='Terms and conditions for test challenge 1',
            submission_guidelines='Submission guidelines for test challenge 1',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False)

        self.challenge2 = Challenge.objects.create(
            title='Test Challenge 2',
            description='Description for test challenge 2',
            terms_and_conditions='Terms and conditions for test challenge 2',
            submission_guidelines='Submission guidelines for test challenge 2',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False)

    def test_get_teams_and_corresponding_challenges_for_a_participant(self):

        self.challenge1.participant_teams.add(self.participant_team1)
        self.challenge1.save()

        expected = {
            "challenge_participant_team_list": [
                {
                    "challenge": {
                        "id": self.challenge1.id,
                        "title": self.challenge1.title,
                        "description": self.challenge1.description,
                        "terms_and_conditions": self.challenge1.terms_and_conditions,
                        "submission_guidelines": self.challenge1.submission_guidelines,
                        "evaluation_details": self.challenge1.evaluation_details,
                        "image": self.challenge1.image,
                        "start_date": self.challenge1.start_date,
                        "end_date": self.challenge1.end_date,
                        "creator": {
                            "id": self.challenge_host_team.id,
                            "team_name": self.challenge_host_team.team_name,
                            "created_by": self.challenge_host_team.created_by.id
                        },
                        "published": self.challenge1.published,
                        "enable_forum": self.challenge1.enable_forum,
                        "anonymous_leaderboard": self.challenge1.anonymous_leaderboard,
                    },
                    "participant_team": {
                        "id": self.participant_team1.id,
                        "team_name": self.participant_team1.team_name,
                        "created_by": self.participant_team1.created_by.username
                    }
                }
            ]
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_when_participant_team_hasnot_participated_in_any_challenge(self):

        expected = {
            "challenge_participant_team_list": [
                {
                    "challenge": None,
                    "participant_team": {
                        "id": self.participant_team1.id,
                        "team_name": self.participant_team1.team_name,
                        "created_by": self.participant_team1.created_by.username
                    }
                }
            ]
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_when_there_is_no_participant_team_of_user(self):

        self.participant_team1.delete()

        expected = {
            "challenge_participant_team_list": []
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RemoveSelfFromParticipantTeamTest(BaseAPITestClass):

    def setUp(self):
        super(RemoveSelfFromParticipantTeamTest, self).setUp()

        self.participant = Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team)

        self.url = reverse_lazy('participants:remove_self_from_participant_team',
                                kwargs={'participant_team_pk': self.participant_team.pk
                                        })

    def test_when_participant_team_does_not_exist(self):
        self.url = reverse_lazy('participants:remove_self_from_participant_team',
                                kwargs={'participant_team_pk': self.participant_team.pk + 1
                                        })

        expected = {
            'error': 'ParticipantTeam does not exist'
        }

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_a_participant_is_successfully_removed_from_team(self):
        self.url = reverse_lazy('participants:remove_self_from_participant_team',
                                kwargs={'participant_team_pk': self.participant_team.pk,
                                        })
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
