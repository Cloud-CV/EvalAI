import os
import shutil

from datetime import timedelta

from django.core.urlresolvers import reverse_lazy
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge, ChallengePhase
from participants.models import Participant, ParticipantTeam
from hosts.models import ChallengeHost, ChallengeHostTeam


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
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN)

        self.participant_team = ParticipantTeam.objects.create(
            team_name='Participant Team for Challenge',
            created_by=self.user)

        self.client.force_authenticate(user=self.user)


class GetChallengeTest(BaseAPITestClass):
    url = reverse_lazy('challenges:get_challenge_list')

    def setUp(self):
        super(GetChallengeTest, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_list',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk})

    def test_get_challenge(self):
        expected = [
            {
                "id": self.challenge.pk,
                "title": self.challenge.title,
                "description": self.challenge.description,
                "terms_and_conditions": self.challenge.terms_and_conditions,
                "submission_guidelines": self.challenge.submission_guidelines,
                "evaluation_details": self.challenge.evaluation_details,
                "image": None,
                "start_date": "{0}{1}".format(self.challenge.start_date.isoformat(), 'Z').replace("+00:00", ""),
                "end_date": "{0}{1}".format(self.challenge.end_date.isoformat(), 'Z').replace("+00:00", ""),
                "creator": {
                    "id": self.challenge.creator.pk,
                    "team_name": self.challenge.creator.team_name,
                    "created_by": self.challenge.creator.created_by.username
                },
                "published": self.challenge.published,
                "enable_forum": self.challenge.enable_forum,
                "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
                "is_active": True
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_for_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_challenge_list',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk + 1})
        expected = {
            'error': 'ChallengeHostTeam does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class CreateChallengeTest(BaseAPITestClass):

    def setUp(self):
        super(CreateChallengeTest, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_list',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk})
        self.data = {
            'title': 'New Test Challenge',
            'description': 'Description for new test challenge',
            'terms_and_conditions': 'Terms and conditions for new test challenge',
            'submission_guidelines': 'Submission guidelines for new test challenge',
            "creator": {
                "id": self.challenge_host_team.pk,
                "team_name": self.challenge_host_team.team_name,
                "created_by": self.challenge_host_team.created_by.pk
            },
            'published': False,
            'enable_forum': True,
            'anonymous_leaderboard': False,
            'start_date': timezone.now() - timedelta(days=2),
            'end_date': timezone.now() + timedelta(days=1),
        }

    def test_create_challenge_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_with_no_data(self):
        del self.data['title']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_challenge_host_team_ownership(self):
        del self.data['creator']
        self.challenge_host.delete()
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetParticularChallenge(BaseAPITestClass):

    def setUp(self):
        super(GetParticularChallenge, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_detail',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk,
                                        'pk': self.challenge.pk})

    def test_get_particular_challenge(self):
        expected = {
            "id": self.challenge.pk,
            "title": self.challenge.title,
            "description": self.challenge.description,
            "terms_and_conditions": self.challenge.terms_and_conditions,
            "submission_guidelines": self.challenge.submission_guidelines,
            "evaluation_details": self.challenge.evaluation_details,
            "image": None,
            "start_date": "{0}{1}".format(self.challenge.start_date.isoformat(), 'Z').replace("+00:00", ""),
            "end_date": "{0}{1}".format(self.challenge.end_date.isoformat(), 'Z').replace("+00:00", ""),
            "creator": {
                "id": self.challenge.creator.pk,
                "team_name": self.challenge.creator.team_name,
                "created_by": self.challenge.creator.created_by.username
            },
            "published": self.challenge.published,
            "enable_forum": self.challenge.enable_forum,
            "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
            "is_active": True
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_challenge_detail',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk,
                                        'pk': self.challenge.pk + 1})
        expected = {
            'error': 'Challenge does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_host_team_for_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_challenge_detail',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk + 1,
                                        'pk': self.challenge.pk})
        expected = {
            'error': 'ChallengeHostTeam does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class UpdateParticularChallenge(BaseAPITestClass):

    def setUp(self):
        super(UpdateParticularChallenge, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_detail',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk,
                                        'pk': self.challenge.pk})

        self.partial_update_challenge_title = 'Partial Update Test Challenge'
        self.update_challenge_title = 'Update Test Challenge'
        self.update_submission_guidelines = 'Update Submission Guidelines'
        self.data = {
            'title': self.update_challenge_title,
            'submission_guidelines': self.update_submission_guidelines
        }

    def test_particular_challenge_partial_update(self):
        self.partial_update_data = {
            'title': self.partial_update_challenge_title
        }
        expected = {
            "id": self.challenge.pk,
            "title": self.partial_update_challenge_title,
            "description": self.challenge.description,
            "terms_and_conditions": self.challenge.terms_and_conditions,
            "submission_guidelines": self.challenge.submission_guidelines,
            "evaluation_details": self.challenge.evaluation_details,
            "image": None,
            "start_date": None,
            "end_date": None,
            "creator": self.challenge.creator.pk,
            "published": self.challenge.published,
            "enable_forum": self.challenge.enable_forum,
            "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
            "is_active": True,
            "start_date": "{0}{1}".format(self.challenge.start_date.isoformat(), 'Z').replace("+00:00", ""),
            "end_date": "{0}{1}".format(self.challenge.end_date.isoformat(), 'Z').replace("+00:00", ""),

        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_update(self):
        expected = {
            "id": self.challenge.pk,
            "title": self.update_challenge_title,
            "description": self.challenge.description,
            "terms_and_conditions": self.challenge.terms_and_conditions,
            "submission_guidelines": self.update_submission_guidelines,
            "evaluation_details": self.challenge.evaluation_details,
            "image": None,
            "start_date": None,
            "end_date": None,
            "creator": self.challenge.creator.pk,
            "published": self.challenge.published,
            "enable_forum": self.challenge.enable_forum,
            "anonymous_leaderboard": self.challenge.anonymous_leaderboard,
            "is_active": True,
            "start_date": "{0}{1}".format(self.challenge.start_date.isoformat(), 'Z').replace("+00:00", ""),
            "end_date": "{0}{1}".format(self.challenge.end_date.isoformat(), 'Z').replace("+00:00", ""),
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_update_with_no_data(self):
        self.data = {
            'title': ''
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteParticularChallenge(BaseAPITestClass):

    def setUp(self):
        super(DeleteParticularChallenge, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_detail',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk,
                                        'pk': self.challenge.pk})

    def test_particular_challenge_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class MapChallengeAndParticipantTeam(BaseAPITestClass):

    def setUp(self):
        super(MapChallengeAndParticipantTeam, self).setUp()
        self.url = reverse_lazy('challenges:add_participant_team_to_challenge',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'participant_team_pk': self.participant_team.pk})

        # user who create a challenge host team
        self.user2 = User.objects.create(
            username='someuser2',
            password='some_secret_password')
        # user who maps a participant team to a challenge
        self.user3 = User.objects.create(
            username='someuser3',
            password='some_secret_password')

        self.challenge_host_team2 = ChallengeHostTeam.objects.create(
            team_name='Some Test Challenge Host Team',
            created_by=self.user2)

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user2,
            team_name=self.challenge_host_team2,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN)

        self.challenge_host3 = ChallengeHost.objects.create(
            user=self.user3,
            team_name=self.challenge_host_team2,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN)

        self.challenge2 = Challenge.objects.create(
            title='Some Test Challenge',
            description='Description for some test challenge',
            terms_and_conditions='Terms and conditions for some test challenge',
            submission_guidelines='Submission guidelines for some test challenge',
            creator=self.challenge_host_team2,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.participant_team2 = ParticipantTeam.objects.create(
            team_name='Some Participant Team',
            created_by=self.user3)

        self.participant2 = Participant.objects.create(
            user=self.user3,
            status=Participant.SELF,
            team=self.participant_team2)

    def test_map_challenge_and_participant_team_together(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # to check when the api is hit again
        expected = {
            'message': 'Team already exists',
            'challenge_id': self.challenge.pk,
            'participant_team_id': self.participant_team.pk
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_when_challenge_host_maps_a_participant_team_with_his_challenge(self):
        self.url = reverse_lazy('challenges:add_participant_team_to_challenge',
                                kwargs={'challenge_pk': self.challenge2.pk,
                                        'participant_team_pk': self.participant_team2.pk})
        expected = {
            'message': 'Sorry, You cannot participate in your own challenge!',
            'challenge_id': self.challenge2.pk,
            'participant_team_id': self.participant_team2.pk
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_for_mapping_with_participant_team_does_not_exist(self):
        self.url = reverse_lazy('challenges:add_participant_team_to_challenge',
                                kwargs={'challenge_pk': self.challenge.pk + 2,
                                        'participant_team_pk': self.participant_team.pk})
        expected = {
            'error': 'Challenge does not exist'
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_participant_team_for_mapping_with_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:add_participant_team_to_challenge',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'participant_team_pk': self.participant_team.pk + 2})
        expected = {
            'error': 'ParticipantTeam does not exist'
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class DisableChallengeTest(BaseAPITestClass):

    def setUp(self):
        super(DisableChallengeTest, self).setUp()

        self.user1 = User.objects.create(
            username='otheruser',
            password='other_secret_password')

        self.challenge_host_team1 = ChallengeHostTeam.objects.create(
            team_name='Other Test Challenge Host Team',
            created_by=self.user1)

        self.challenge2 = Challenge.objects.create(
            title='Other Test Challenge',
            description='Description for other test challenge',
            terms_and_conditions='Terms and conditions for other test challenge',
            submission_guidelines='Submission guidelines for other test challenge',
            creator=self.challenge_host_team1,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        self.url = reverse_lazy('challenges:disable_challenge',
                                kwargs={'pk': self.challenge.pk})

    def test_disable_a_challenge(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_particular_challenge_for_disable_does_not_exist(self):
        self.url = reverse_lazy('challenges:disable_challenge',
                                kwargs={'pk': self.challenge.pk + 2})
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_user_does_not_have_permission_to_disable_particular_challenge(self):
        self.url = reverse_lazy('challenges:disable_challenge',
                                kwargs={'pk': self.challenge2.pk})
        expected = {
            'error': 'Sorry, you do not have permission to disable this challenge'
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetAllChallengesTest(BaseAPITestClass):
    url = reverse_lazy('challenges:get_all_challenges')

    def setUp(self):
        super(GetAllChallengesTest, self).setUp()
        self.url = reverse_lazy('challenges:get_all_challenges',
                                kwargs={'challenge_time': "PAST"})

        # Present challenge
        self.challenge2 = Challenge.objects.create(
            title='Test Challenge 2',
            description='Description for test challenge 2',
            terms_and_conditions='Terms and conditions for test challenge 2',
            submission_guidelines='Submission guidelines for test challenge 2',
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        # Past Challenge challenge
        self.challenge3 = Challenge.objects.create(
            title='Test Challenge 3',
            description='Description for test challenge 3',
            terms_and_conditions='Terms and conditions for test challenge 3',
            submission_guidelines='Submission guidelines for test challenge 3',
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() - timedelta(days=1),
        )

        # Future challenge
        self.challenge4 = Challenge.objects.create(
            title='Test Challenge 4',
            description='Description for test challenge 4',
            terms_and_conditions='Terms and conditions for test challenge 4',
            submission_guidelines='Submission guidelines for test challenge 4',
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

    def test_get_past_challenges(self):
        expected = [
            {
                "id": self.challenge3.pk,
                "title": self.challenge3.title,
                "description": self.challenge3.description,
                "terms_and_conditions": self.challenge3.terms_and_conditions,
                "submission_guidelines": self.challenge3.submission_guidelines,
                "evaluation_details": self.challenge3.evaluation_details,
                "image": None,
                "start_date": "{0}{1}".format(self.challenge3.start_date.isoformat(), 'Z').replace("+00:00", ""),
                "end_date": "{0}{1}".format(self.challenge3.end_date.isoformat(), 'Z').replace("+00:00", ""),
                "creator": {
                    "id": self.challenge3.creator.pk,
                    "team_name": self.challenge3.creator.team_name,
                    "created_by": self.challenge3.creator.created_by.username,
                },
                "published": self.challenge3.published,
                "enable_forum": self.challenge3.enable_forum,
                "anonymous_leaderboard": self.challenge3.anonymous_leaderboard,
                "is_active": False,
            }
        ]
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], expected)

    def test_get_present_challenges(self):
        self.url = reverse_lazy('challenges:get_all_challenges',
                                kwargs={'challenge_time': "PRESENT"})

        expected = [
            {
                "id": self.challenge2.pk,
                "title": self.challenge2.title,
                "description": self.challenge2.description,
                "terms_and_conditions": self.challenge2.terms_and_conditions,
                "submission_guidelines": self.challenge2.submission_guidelines,
                "evaluation_details": self.challenge2.evaluation_details,
                "image": None,
                "start_date": "{0}{1}".format(self.challenge2.start_date.isoformat(), 'Z').replace("+00:00", ""),
                "end_date": "{0}{1}".format(self.challenge2.end_date.isoformat(), 'Z').replace("+00:00", ""),
                "creator": {
                    "id": self.challenge2.creator.pk,
                    "team_name": self.challenge2.creator.team_name,
                    "created_by": self.challenge2.creator.created_by.username,
                },
                "published": self.challenge2.published,
                "enable_forum": self.challenge2.enable_forum,
                "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
                "is_active": True,
            }
        ]
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], expected)

    def test_get_future_challenges(self):
        self.url = reverse_lazy('challenges:get_all_challenges',
                                kwargs={'challenge_time': "FUTURE"})

        expected = [
            {
                "id": self.challenge4.pk,
                "title": self.challenge4.title,
                "description": self.challenge4.description,
                "terms_and_conditions": self.challenge4.terms_and_conditions,
                "submission_guidelines": self.challenge4.submission_guidelines,
                "evaluation_details": self.challenge4.evaluation_details,
                "image": None,
                "start_date": "{0}{1}".format(self.challenge4.start_date.isoformat(), 'Z').replace("+00:00", ""),
                "end_date": "{0}{1}".format(self.challenge4.end_date.isoformat(), 'Z').replace("+00:00", ""),
                "creator": {
                    "id": self.challenge4.creator.pk,
                    "team_name": self.challenge4.creator.team_name,
                    "created_by": self.challenge4.creator.created_by.username,
                },
                "published": self.challenge4.published,
                "enable_forum": self.challenge4.enable_forum,
                "anonymous_leaderboard": self.challenge4.anonymous_leaderboard,
                "is_active": False,
            }
        ]
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], expected)

    def test_get_all_challenges(self):
        self.url = reverse_lazy('challenges:get_all_challenges',
                                kwargs={'challenge_time': "ALL"})

        expected = [
            {
                "id": self.challenge2.pk,
                "title": self.challenge2.title,
                "description": self.challenge2.description,
                "terms_and_conditions": self.challenge2.terms_and_conditions,
                "submission_guidelines": self.challenge2.submission_guidelines,
                "evaluation_details": self.challenge2.evaluation_details,
                "image": None,
                "start_date": "{0}{1}".format(self.challenge2.start_date.isoformat(), 'Z').replace("+00:00", ""),
                "end_date": "{0}{1}".format(self.challenge2.end_date.isoformat(), 'Z').replace("+00:00", ""),
                "creator": {
                    "id": self.challenge2.creator.pk,
                    "team_name": self.challenge2.creator.team_name,
                    "created_by": self.challenge2.creator.created_by.username,
                },
                "published": self.challenge2.published,
                "enable_forum": self.challenge2.enable_forum,
                "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
                "is_active": True,
            },
            {
                "id": self.challenge3.pk,
                "title": self.challenge3.title,
                "description": self.challenge3.description,
                "terms_and_conditions": self.challenge3.terms_and_conditions,
                "submission_guidelines": self.challenge3.submission_guidelines,
                "evaluation_details": self.challenge3.evaluation_details,
                "image": None,
                "start_date": "{0}{1}".format(self.challenge3.start_date.isoformat(), 'Z').replace("+00:00", ""),
                "end_date": "{0}{1}".format(self.challenge3.end_date.isoformat(), 'Z').replace("+00:00", ""),
                "creator": {
                    "id": self.challenge3.creator.pk,
                    "team_name": self.challenge3.creator.team_name,
                    "created_by": self.challenge3.creator.created_by.username,
                },
                "published": self.challenge3.published,
                "enable_forum": self.challenge3.enable_forum,
                "anonymous_leaderboard": self.challenge3.anonymous_leaderboard,
                "is_active": False,
            },
            {
                "id": self.challenge4.pk,
                "title": self.challenge4.title,
                "description": self.challenge4.description,
                "terms_and_conditions": self.challenge4.terms_and_conditions,
                "submission_guidelines": self.challenge4.submission_guidelines,
                "evaluation_details": self.challenge4.evaluation_details,
                "image": None,
                "start_date": "{0}{1}".format(self.challenge4.start_date.isoformat(), 'Z').replace("+00:00", ""),
                "end_date": "{0}{1}".format(self.challenge4.end_date.isoformat(), 'Z').replace("+00:00", ""),
                "creator": {
                    "id": self.challenge4.creator.pk,
                    "team_name": self.challenge4.creator.team_name,
                    "created_by": self.challenge4.creator.created_by.username,
                },
                "published": self.challenge4.published,
                "enable_forum": self.challenge4.enable_forum,
                "anonymous_leaderboard": self.challenge4.anonymous_leaderboard,
                "is_active": False,
            }
        ]
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], expected)

    def test_incorrent_url_pattern_challenges(self):
        self.url = reverse_lazy('challenges:get_all_challenges',
                                kwargs={'challenge_time': "INCORRECT"})
        expected = {'error': 'Wrong url pattern!'}
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.data, expected)


class GetChallengeByPk(BaseAPITestClass):

    def setUp(self):
        super(GetChallengeByPk, self).setUp()

        self.challenge3 = Challenge.objects.create(
            title='Test Challenge 3',
            description='Description for test challenge 3',
            terms_and_conditions='Terms and conditions for test challenge 3',
            submission_guidelines='Submission guidelines for test challenge 3',
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() - timedelta(days=1),
        )

    def test_get_challenge_by_pk_when_challenge_exists(self):
        self.url = reverse_lazy('challenges:get_challenge_by_pk',
                                kwargs={'pk': self.challenge3.pk})

        expected = {
            "id": self.challenge3.pk,
            "title": self.challenge3.title,
            "description": self.challenge3.description,
            "terms_and_conditions": self.challenge3.terms_and_conditions,
            "submission_guidelines": self.challenge3.submission_guidelines,
            "evaluation_details": self.challenge3.evaluation_details,
            "image": None,
            "start_date": "{0}{1}".format(self.challenge3.start_date.isoformat(), 'Z').replace("+00:00", ""),
            "end_date": "{0}{1}".format(self.challenge3.end_date.isoformat(), 'Z').replace("+00:00", ""),
            "creator": {
                "id": self.challenge3.creator.pk,
                "team_name": self.challenge3.creator.team_name,
                "created_by": self.challenge3.creator.created_by.username,
            },
            "published": self.challenge3.published,
            "enable_forum": self.challenge3.enable_forum,
            "anonymous_leaderboard": self.challenge3.anonymous_leaderboard,
            "is_active": False,
        }

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_by_pk_when_challenge_does_not_exists(self):
        self.url = reverse_lazy('challenges:get_challenge_by_pk',
                                kwargs={'pk': self.challenge3.pk + 10})
        expected = {
            'error': 'Challenge does not exist!'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class BaseChallengePhaseClass(BaseAPITestClass):

    def setUp(self):
        super(BaseChallengePhaseClass, self).setUp()
        try:
            os.makedirs('/tmp/evalai')
        except OSError:
            pass

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge_phase = ChallengePhase.objects.create(
                name='Challenge Phase',
                description='Description for Challenge Phase',
                leaderboard_public=False,
                is_public=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   'Dummy file content', content_type='text/plain')
            )

    def tearDown(self):
        shutil.rmtree('/tmp/evalai')


class GetChallengePhaseTest(BaseChallengePhaseClass):

    def setUp(self):
        super(GetChallengePhaseTest, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_phase_list',
                                kwargs={'challenge_pk': self.challenge.pk})

    def test_get_challenge_phase(self):
        expected = [
            {
                "id": self.challenge_phase.id,
                "name": self.challenge_phase.name,
                "description": self.challenge_phase.description,
                "leaderboard_public": self.challenge_phase.leaderboard_public,
                "start_date": "{0}{1}".format(self.challenge_phase.start_date.isoformat(), 'Z').replace("+00:00", ""),
                "end_date": "{0}{1}".format(self.challenge_phase.end_date.isoformat(), 'Z').replace("+00:00", ""),
                "challenge": self.challenge_phase.challenge.pk,
                "is_public": self.challenge_phase.is_public,
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_for_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_challenge_phase_list',
                                kwargs={'challenge_pk': self.challenge.pk + 1})
        expected = {
            'error': 'Challenge does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class CreateChallengePhaseTest(BaseChallengePhaseClass):

    def setUp(self):
        super(CreateChallengePhaseTest, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_phase_list',
                                kwargs={'challenge_pk': self.challenge.pk})
        self.data = {
            'name': 'New Challenge Phase',
            'description': 'Description for new challenge phase'
        }

    @override_settings(MEDIA_ROOT='/tmp/evalai')
    def test_create_challenge_phase_with_all_data(self):
        self.data['test_annotation'] = SimpleUploadedFile('another_test_file.txt',
                                                          'Another Dummy file content',
                                                          content_type='text/plain')
        response = self.client.post(self.url, self.data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_phase_with_no_data(self):
        del self.data['name']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetParticularChallengePhase(BaseChallengePhaseClass):

    def setUp(self):
        super(GetParticularChallengePhase, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_phase_detail',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'pk': self.challenge_phase.pk})

    def test_get_particular_challenge_phase(self):
        expected = {
            "id": self.challenge_phase.id,
            "name": self.challenge_phase.name,
            "description": self.challenge_phase.description,
            "leaderboard_public": self.challenge_phase.leaderboard_public,
            "start_date": "{0}{1}".format(self.challenge_phase.start_date.isoformat(), 'Z').replace("+00:00", ""),
            "end_date": "{0}{1}".format(self.challenge_phase.end_date.isoformat(), 'Z').replace("+00:00", ""),
            "challenge": self.challenge_phase.challenge.pk,
            "is_public": self.challenge_phase.is_public
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_challenge_phase_detail',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'pk': self.challenge_phase.pk + 1})
        expected = {
            'error': 'ChallengePhase does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_host_team_for_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_challenge_phase_detail',
                                kwargs={'challenge_pk': self.challenge.pk + 1,
                                        'pk': self.challenge_phase.pk})
        expected = {
            'error': 'Challenge does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class UpdateParticularChallengePhase(BaseChallengePhaseClass):

    def setUp(self):
        super(UpdateParticularChallengePhase, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_phase_detail',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'pk': self.challenge_phase.pk})

        self.partial_update_challenge_phase_name = 'Partial Update Challenge Phase Name'
        self.update_challenge_phase_title = 'Update Challenge Phase Name'
        self.update_description = 'Update Challenge Phase Description'
        self.data = {
            'name': self.update_challenge_phase_title,
            'description': self.update_description,
        }

    def test_particular_challenge_phase_partial_update(self):
        self.partial_update_data = {
            'name': self.partial_update_challenge_phase_name
        }
        expected = {
            "id": self.challenge_phase.id,
            "name": self.partial_update_challenge_phase_name,
            "description": self.challenge_phase.description,
            "leaderboard_public": self.challenge_phase.leaderboard_public,
            "start_date": "{0}{1}".format(self.challenge_phase.start_date.isoformat(), 'Z').replace("+00:00", ""),
            "end_date": "{0}{1}".format(self.challenge_phase.end_date.isoformat(), 'Z').replace("+00:00", ""),
            "challenge": self.challenge_phase.challenge.pk,
            "is_public": self.challenge_phase.is_public
        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @override_settings(MEDIA_ROOT='/tmp/evalai')
    def test_particular_challenge_phase_update(self):

        self.update_test_annotation = SimpleUploadedFile('update_test_sample_file.txt',
                                                         'Dummy update file content', content_type='text/plain')
        self.data['test_annotation'] = self.update_test_annotation
        response = self.client.put(self.url, self.data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_update_with_no_data(self):
        self.data = {
            'name': ''
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteParticularChallengePhase(BaseChallengePhaseClass):

    def setUp(self):
        super(DeleteParticularChallengePhase, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_phase_detail',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'pk': self.challenge_phase.pk})

    def test_particular_challenge_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
