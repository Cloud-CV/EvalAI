from datetime import timedelta

from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge
from hosts.models import ChallengeHost, ChallengeHostTeam
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

        self.participant = Participant.objects.create(
            user=self.user,
            team=self.participant_team,
            status=Participant.SELF,)

        self.client.force_authenticate(user=self.user)


class GetParticipantTeamTest(BaseAPITestClass):

    url = reverse_lazy('participants:get_participant_team_list')

    def setUp(self):
        super(GetParticipantTeamTest, self).setUp()

        self.user2 = User.objects.create(
            username='user2',
            email='user2@platform.com',
            password='user2_password')

        EmailAddress.objects.create(
            user=self.user2,
            email='user2@platform.com',
            primary=True,
            verified=True)

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team)

    def test_get_challenge(self):
        expected = [
            {
                "id": self.participant_team.pk,
                "team_name": self.participant_team.team_name,
                "created_by": self.user.username,
                "team_url": self.participant_team.team_url,
                "docker_repository_uri": self.participant_team.docker_repository_uri,
                "members": [
                    {
                        "member_name": self.participant.user.username,
                        "status": self.participant.status,
                        "member_id": self.participant.user.id
                    },
                    {
                        "member_name": self.participant2.user.username,
                        "status": self.participant2.status,
                        "member_id": self.participant2.user.id
                    }
                ]
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

    def test_create_participant_team_with_team_name_same_as_with_existing_team(self):

        expected = {
            "team_name": ["participant team with this team name already exists."]
        }

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # Creating team with same team name
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected)

    def test_create_participant_team_with_no_data(self):
        del self.data['team_name']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetParticularParticipantTeam(BaseAPITestClass):

    def setUp(self):
        super(GetParticularParticipantTeam, self).setUp()
        self.url = reverse_lazy('participants:get_participant_team_details',
                                kwargs={'pk': self.participant_team.pk})

        self.user2 = User.objects.create(
            username='user2',
            email='user2@platform.com',
            password='user2_password')

        EmailAddress.objects.create(
            user=self.user2,
            email='user2@platform.com',
            primary=True,
            verified=True)

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team)

    def test_get_particular_participant_team(self):
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.participant_team.team_name,
            "created_by": self.user.username,
            "team_url": self.participant_team.team_url,
            "docker_repository_uri": self.participant_team.docker_repository_uri,
            "members": [
                {
                    "member_name": self.participant.user.username,
                    "status": self.participant.status,
                    "member_id": self.participant.user.id
                },
                {
                    "member_name": self.participant2.user.username,
                    "status": self.participant2.status,
                    "member_id": self.participant2.user.id
                }
            ]
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
            "created_by": self.user.username,
            "team_url": self.participant_team.team_url,
            "docker_repository_uri": self.participant_team.docker_repository_uri
        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_participant_team_update(self):
        expected = {
            "id": self.participant_team.pk,
            "team_name": self.update_participant_team_name,
            "created_by": self.user.username,
            "team_url": self.participant_team.team_url,
            "docker_repository_uri": self.participant_team.docker_repository_uri
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

    def setUp(self):
        super(InviteParticipantToTeamTest, self).setUp()
        self.data = {
            'email': self.invite_user.email
        }
        self.url = reverse_lazy('participants:invite_participant_to_team',
                                kwargs={'pk': self.participant_team.pk})

    def test_invite_participant_to_team_with_all_data(self):
        expected = {
            'message': 'User has been successfully added to the team!'
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_invite_participant_to_team_with_no_data(self):
        del self.data['email']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_self_to_team(self):
        self.data = {
            'email': self.user.email
        }
        expected = {
            'error': 'User is already part of the team!'
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_to_other_team_which_doesnot_belong_to_user(self):
        temp_user = User.objects.create(
            username="temp_user", password="test_password")
        temp_participant_team = ParticipantTeam.objects.create(
            team_name="Test Team 1", created_by=temp_user)

        expected = {
            'error': 'You are not a member of this team!'
        }

        self.url = reverse_lazy('participants:invite_participant_to_team',
                                kwargs={'pk': temp_participant_team.pk})

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_user_which_does_not_exist_to_team(self):
        self.data = {
            'email': 'userwhichdoesnotexist@platform.com'
        }
        expected = {
            'error': 'User does not exist with this email address!'
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_participant_team_for_invite_does_not_exist(self):
        self.url = reverse_lazy('participants:invite_participant_to_team',
                                kwargs={'pk': self.participant_team.pk + 1})
        expected = {
            'error': 'Participant Team does not exist'
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_participant_to_team_when_user_cannot_be_invited(self):
        '''
        NOTE
        user: host user
        user1: participant 1
        user2: participant 2
        '''
        self.user2 = User.objects.create(
            username='user2',
            email='user2@platform.com',
            password='user2_password')

        EmailAddress.objects.create(
            user=self.user2,
            email='user2@platform.com',
            primary=True,
            verified=True)

        self.user3 = User.objects.create(
            username='user3',
            email='user3@platform.com',
            password='user3_password')

        EmailAddress.objects.create(
            user=self.user3,
            email='user3@platform.com',
            primary=True,
            verified=True)

        self.participant_team2 = ParticipantTeam.objects.create(
            team_name='Participant Team created by user 2',
            created_by=self.user2)

        self.participant_team3 = ParticipantTeam.objects.create(
            team_name='Participant Team created by user 3',
            created_by=self.user3)

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team2)

        self.participant3 = Participant.objects.create(
            user=self.user3,
            status=Participant.ACCEPTED,
            team=self.participant_team3)

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            short_description='Short description for test challenge',
            description='Description for test challenge',
            terms_and_conditions='Terms and conditions for test challenge',
            submission_guidelines='Submission guidelines for test challenge',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.client.force_authenticate(user=self.user2)

        self.challenge.participant_teams.add(self.participant_team2)
        self.challenge.participant_teams.add(self.participant_team3)

        self.data = {
            'email': self.user3.email
        }
        self.url = reverse_lazy('participants:invite_participant_to_team',
                                kwargs={'pk': self.participant_team2.pk})

        expected = {
            'error': 'Sorry, the invited user has already participated '
            'in atleast one of the challenges which you are already'
            ' a part of. Please try creating a new team and then invite.'
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class DeleteParticipantFromTeamTest(BaseAPITestClass):

    def setUp(self):
        super(DeleteParticipantFromTeamTest, self).setUp()

        self.participant = Participant.objects.create(
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
                                        'participant_pk': self.participant.pk
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

        self.user2 = User.objects.create(
            username='user2',
            email='user2@platform.com',
            password='user2_password')

        EmailAddress.objects.create(
            user=self.user2,
            email='user2@platform.com',
            primary=True,
            verified=True)

        self.participant_team2 = ParticipantTeam.objects.create(
            team_name='Team B',
            created_by=self.user2)  # created by user2 and not user

        self.participant2 = Participant.objects.create(
            user=self.user2,
            status=Participant.ACCEPTED,
            team=self.participant_team2)

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Host Team 1',
            created_by=self.user2)

        self.challenge1 = Challenge.objects.create(
            title='Test Challenge 1',
            short_description='Short description for test challenge 1',
            description='Description for test challenge 1',
            terms_and_conditions='Terms and conditions for test challenge 1',
            submission_guidelines='Submission guidelines for test challenge 1',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.challenge2 = Challenge.objects.create(
            title='Test Challenge 2',
            short_description='Short description for test challenge 2',
            description='Description for test challenge 2',
            terms_and_conditions='Terms and conditions for test challenge 2',
            submission_guidelines='Submission guidelines for test challenge 2',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            )

        self.url = reverse_lazy(
            'participants:get_teams_and_corresponding_challenges_for_a_participant',
            kwargs={'challenge_pk': self.challenge1.pk})

        self.time = timezone.now()

    def test_get_teams_and_corresponding_challenges_for_a_participant(self):

        self.challenge1.participant_teams.add(self.participant_team)
        self.challenge1.save()

        expected = {
            "challenge_participant_team_list": [
                {
                    "challenge": {
                        "id": self.challenge1.id,
                        "title": self.challenge1.title,
                        "description": self.challenge1.description,
                        "short_description": self.challenge1.short_description,
                        "terms_and_conditions": self.challenge1.terms_and_conditions,
                        "submission_guidelines": self.challenge1.submission_guidelines,
                        "evaluation_details": self.challenge1.evaluation_details,
                        "image": self.challenge1.image,
                        "start_date":
                            "{0}{1}".format(self.challenge1.start_date.isoformat(), 'Z').replace("+00:00", ""),
                        "end_date": "{0}{1}".format(self.challenge1.end_date.isoformat(), 'Z').replace("+00:00", ""),
                        "creator": {
                            "id": self.challenge_host_team.id,
                            "team_name": self.challenge_host_team.team_name,
                            "created_by": self.challenge_host_team.created_by.username,
                            "team_url": self.challenge_host_team.team_url
                            },
                        "published": self.challenge1.published,
                        "enable_forum": self.challenge1.enable_forum,
                        "anonymous_leaderboard": self.challenge1.anonymous_leaderboard,
                        "is_active": True,
                        "allowed_email_domains": [],
                        "blocked_email_domains": [],
                        "approved_by_admin": False,
                        "forum_url": self.challenge1.forum_url,
                        "is_docker_based": self.challenge1.is_docker_based,
                        "slug": self.challenge1.slug,
                        "max_docker_image_size": self.challenge1.max_docker_image_size
                    },
                    "participant_team": {
                        "id": self.participant_team.id,
                        "team_name": self.participant_team.team_name,
                        "created_by": self.participant_team.created_by.username,
                        "team_url": self.participant_team.team_url,
                        "docker_repository_uri": self.participant_team.docker_repository_uri
                    }
                }
            ],
            "is_challenge_host": False
        }
        response = self.client.get(self.url, {})
        # checking 'datetime_now' separately because of time difference in microseconds
        self.assertTrue(abs(response.data['datetime_now'] - self.time) < timedelta(seconds=1))
        # deleting field 'datetime_now' from response to check with expected response without time field
        del response.data['datetime_now']
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_participant_team_challenge_list(self):
        self.url = reverse_lazy('participants:get_participant_team_challenge_list',
                                kwargs={'participant_team_pk': self.participant_team.pk})
        expected = [
            {
                "id": self.challenge1.id,
                "title": self.challenge1.title,
                "description": self.challenge1.description,
                "short_description": self.challenge1.short_description,
                "terms_and_conditions": self.challenge1.terms_and_conditions,
                "submission_guidelines": self.challenge1.submission_guidelines,
                "evaluation_details": self.challenge1.evaluation_details,
                "image": self.challenge1.image,
                "start_date":
                    "{0}{1}".format(self.challenge1.start_date.isoformat(), 'Z').replace("+00:00", ""),
                "end_date": "{0}{1}".format(self.challenge1.end_date.isoformat(), 'Z').replace("+00:00", ""),
                "creator": {
                    "id": self.challenge_host_team.id,
                    "team_name": self.challenge_host_team.team_name,
                    "created_by": self.challenge_host_team.created_by.username,
                    "team_url": self.challenge_host_team.team_url
                    },
                "published": self.challenge1.published,
                "enable_forum": self.challenge1.enable_forum,
                "anonymous_leaderboard": self.challenge1.anonymous_leaderboard,
                "is_active": True,
                "allowed_email_domains": [],
                "blocked_email_domains": [],
                "approved_by_admin": False,
                "forum_url": self.challenge1.forum_url,
                "is_docker_based": self.challenge1.is_docker_based,
                "slug": self.challenge1.slug,
                "max_docker_image_size": self.challenge1.max_docker_image_size
            }
        ]

        self.challenge1.participant_teams.add(self.participant_team)
        self.challenge1.save()

        response = self.client.get(self.url, {})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_when_participant_team_hasnot_participated_in_any_challenge(self):

        expected = {
            "challenge_participant_team_list": [
                {
                    "challenge": None,
                    "participant_team": {
                        "id": self.participant_team.id,
                        "team_name": self.participant_team.team_name,
                        "created_by": self.participant_team.created_by.username,
                        "team_url": self.participant_team.team_url,
                        "docker_repository_uri": self.participant_team.docker_repository_uri
                    }
                }
            ],
            "is_challenge_host": False
        }
        response = self.client.get(self.url, {})
        # checking 'datetime_now' separately because of time difference in microseconds
        self.assertTrue(abs(response.data['datetime_now'] - self.time) < timedelta(seconds=1))
        # deleting field 'datetime_now' from response to check with expected response without time field
        del response.data['datetime_now']
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_when_there_is_no_participant_team_of_user(self):

        self.participant_team.delete()

        expected = {
            "challenge_participant_team_list": [],
            "is_challenge_host": False
        }

        response = self.client.get(self.url, {})
        # checking 'datetime_now' separately because of time difference in microseconds
        self.assertTrue(abs(response.data['datetime_now'] - self.time) < timedelta(seconds=1))
        # deleting field 'datetime_now' from response to check with expected response without time field
        del response.data['datetime_now']
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class RemoveSelfFromParticipantTeamTest(BaseAPITestClass):

    def setUp(self):
        super(RemoveSelfFromParticipantTeamTest, self).setUp()

        # user who create a challenge host team
        self.user2 = User.objects.create(
            username='someuser2',
            password='some_secret_password')

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Some Test Challenge Host Team',
            created_by=self.user2)

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user2,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN)

        self.challenge = Challenge.objects.create(
            title='Some Test Challenge',
            short_description='Short description for some test challenge',
            description='Description for some test challenge',
            terms_and_conditions='Terms and conditions for some test challenge',
            submission_guidelines='Submission guidelines for some test challenge',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.url = reverse_lazy('participants:remove_self_from_participant_team',
                                kwargs={'participant_team_pk': self.participant_team.pk
                                        })

    def test_when_participant_team_does_not_exist(self):
        self.url = reverse_lazy('participants:remove_self_from_participant_team',
                                kwargs={'participant_team_pk': self.participant_team.pk + 1
                                        })

        expected = {
            'error': 'ParticipantTeam does not exist!'
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

    def test_when_participant_team_has_taken_part_in_challenges(self):
        self.challenge.participant_teams.add(self.participant_team)

        expected = {
            'error': 'Sorry, you cannot delete this team since it has taken part in challenge(s)!'
        }

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_participant_team_remove_when_no_participants_exists(self):
        self.url = reverse_lazy('participants:remove_self_from_participant_team',
                                kwargs={'participant_team_pk': self.participant_team.pk,
                                        })

        self.client.delete(self.url, {})
        participant_teams = ParticipantTeam.objects.all()
        self.assertEqual(participant_teams.count(), 0)
