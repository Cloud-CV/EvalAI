import json

from datetime import timedelta

from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import Challenge
from participants.models import ParticipantTeam
from hosts.models import ChallengeHostTeam


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
            anonymous_leaderboard=False)

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
            'published': False,
            'enable_forum': True,
            'anonymous_leaderboard': False
        }

    def test_create_challenge_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_with_no_data(self):
        del self.data['title']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


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
            "anonymous_leaderboard": self.challenge.anonymous_leaderboard
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
            "anonymous_leaderboard": self.challenge.anonymous_leaderboard
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

    def test_map_challenge_and_participant_team_together(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_particular_challenge_for_mapping_with_participant_team_does_not_exist(self):
        self.url = reverse_lazy('challenges:add_participant_team_to_challenge',
                                kwargs={'challenge_pk': self.challenge.pk + 1,
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
                                        'participant_team_pk': self.participant_team.pk + 1})
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
            anonymous_leaderboard=False)

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


class GetPastChallengesTest(BaseAPITestClass):
    url = reverse_lazy('challenges:get_past_challenges')

    def setUp(self):
        super(GetPastChallengesTest, self).setUp()

        # Present challenge and hence should not be displayed
        self.challenge2 = Challenge.objects.create(
            title='Test Challenge 2',
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
                    "created_by": self.challenge3.creator.created_by.pk,
                },
                "published": self.challenge3.published,
                "enable_forum": self.challenge3.enable_forum,
                "anonymous_leaderboard": self.challenge3.anonymous_leaderboard,
            }
        ]
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], expected)


class GetPresentChallengesTest(BaseAPITestClass):
    url = reverse_lazy('challenges:get_present_challenges')

    def setUp(self):
        super(GetPresentChallengesTest, self).setUp()

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

    def test_get_present_challenges(self):
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
                    "created_by": self.challenge2.creator.created_by.pk,
                },
                "published": self.challenge3.published,
                "enable_forum": self.challenge3.enable_forum,
                "anonymous_leaderboard": self.challenge3.anonymous_leaderboard,
            }
        ]
        response = self.client.get(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], expected)
