import json
import os
import shutil

from datetime import timedelta
from os.path import join

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.urlresolvers import reverse_lazy
from django.conf import settings
from django.contrib.auth.models import User
from django.test import override_settings
from django.utils import timezone

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from challenges.models import (Challenge,
                               ChallengeConfiguration,
                               ChallengePhase,
                               ChallengePhaseSplit,
                               DatasetSplit,
                               Leaderboard,
                               StarChallenge)
from participants.models import Participant, ParticipantTeam
from hosts.models import ChallengeHost, ChallengeHostTeam
from jobs.models import Submission


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
            approved_by_admin=False,
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
                "short_description": self.challenge.short_description,
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
            'short_description': 'Short description for new test challenge',
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
                                        'challenge_pk': self.challenge.pk})

    def test_get_particular_challenge(self):
        expected = {
            "id": self.challenge.pk,
            "title": self.challenge.title,
            "short_description": self.challenge.short_description,
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

    def test_update_challenge_when_user_is_not_its_creator(self):
        self.user1 = User.objects.create(
            username='someuser1',
            email="user1@test.com",
            password='secret_psassword')

        EmailAddress.objects.create(
            user=self.user1,
            email='user1@test.com',
            primary=True,
            verified=True)

        self.client.force_authenticate(user=self.user1)

        expected = {"detail": "Sorry, you are not allowed to perform this operation!"}

        response = self.client.put(self.url, {'title': 'Rose Challenge', 'description': 'Version 2.0'})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_challenge_when_user_is_its_creator(self):
        new_title = 'Rose Challenge'
        new_description = 'New description.'
        expected = {
            "id": self.challenge.pk,
            "title": new_title,
            "short_description": self.challenge.short_description,
            "description": new_description,
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
        response = self.client.put(self.url, {'title': new_title, 'description': new_description})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_challenge_detail',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk,
                                        'challenge_pk': self.challenge.pk + 1})
        expected = {
            'error': 'Challenge does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_host_team_for_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_challenge_detail',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk + 1,
                                        'challenge_pk': self.challenge.pk})
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
                                        'challenge_pk': self.challenge.pk})

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
            "short_description": self.challenge.short_description,
            "description": self.challenge.description,
            "terms_and_conditions": self.challenge.terms_and_conditions,
            "submission_guidelines": self.challenge.submission_guidelines,
            "evaluation_details": self.challenge.evaluation_details,
            "image": None,
            "start_date": None,
            "end_date": None,
            "creator": {
                'id': self.challenge.creator.pk,
                'team_name': self.challenge.creator.team_name,
                'created_by': self.challenge.creator.created_by.username
            },
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
            "short_description": self.challenge.short_description,
            "description": self.challenge.description,
            "terms_and_conditions": self.challenge.terms_and_conditions,
            "submission_guidelines": self.update_submission_guidelines,
            "evaluation_details": self.challenge.evaluation_details,
            "image": None,
            "start_date": None,
            "end_date": None,
            "creator": {
                'id': self.challenge.creator.pk,
                'team_name': self.challenge.creator.team_name,
                'created_by': self.challenge.creator.created_by.username
            },
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
                                        'challenge_pk': self.challenge.pk})

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

        # user invited to the participant team
        self.user4 = User.objects.create(
            username='someuser4',
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
            short_description='Short description for some test challenge',
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

        self.participant_team3 = ParticipantTeam.objects.create(
            team_name='Some Participant Team by User 4',
            created_by=self.user4)

        self.participant2 = Participant.objects.create(
            user=self.user3,
            status=Participant.SELF,
            team=self.participant_team2)

        self.participant3 = Participant.objects.create(
            user=self.user4,
            status=Participant.ACCEPTED,
            team=self.participant_team2)

        self.participant4 = Participant.objects.create(
            user=self.user4,
            status=Participant.SELF,
            team=self.participant_team3)

    def test_map_challenge_and_participant_team_together(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # to check when the api is hit again
        expected = {
            'error': 'Team already exists',
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
            'error': 'Sorry, You cannot participate in your own challenge!',
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
                                        'participant_team_pk': self.participant_team.pk + 3})
        expected = {
            'error': 'ParticipantTeam does not exist'
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_add_participant_team_to_challenge_when_some_members_have_already_participated(self):
        self.url = reverse_lazy('challenges:add_participant_team_to_challenge',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'participant_team_pk': self.participant_team2.pk})

        self.client.post(self.url, {})

        expected = {
            'error': 'Sorry, other team member(s) have already participated in the Challenge.'
            ' Please participate with a different team!',
            'challenge_id': self.challenge.pk,
            'participant_team_id': self.participant_team3.pk,
        }

        # submitting the request again as a new team
        self.url = reverse_lazy('challenges:add_participant_team_to_challenge',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'participant_team_pk': self.participant_team3.pk})

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
            short_description='Short description for other test challenge',
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
                                kwargs={'challenge_pk': self.challenge.pk})

    def test_disable_a_challenge(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_particular_challenge_for_disable_does_not_exist(self):
        self.url = reverse_lazy('challenges:disable_challenge',
                                kwargs={'challenge_pk': self.challenge.pk + 2})
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_when_user_does_not_have_permission_to_disable_particular_challenge(self):
        self.url = reverse_lazy('challenges:disable_challenge',
                                kwargs={'challenge_pk': self.challenge2.pk})
        expected = {
            'error': 'Sorry, you are not allowed to perform this operation!'
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data.values()[0], expected['error'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_disable_challenge_when_user_is_not_creator(self):
        self.url = reverse_lazy('challenges:disable_challenge',
                                kwargs={'challenge_pk': self.challenge2.pk})
        # Now allot self.user as also a host of self.challenge_host_team1
        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team1,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN)

        expected = {
            'error': 'Sorry, you are not allowed to perform this operation!'
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data.values()[0], expected['error'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_disable_a_challenge_when_user_is_not_authenticated(self):
        self.client.force_authenticate(user=None)

        expected = {
            'error': 'Authentication credentials were not provided.'
        }

        response = self.client.post(self.url, {})
        self.assertEqual(response.data.values()[0], expected['error'])
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
            short_description='Short description for test challenge 2',
            description='Description for test challenge 2',
            terms_and_conditions='Terms and conditions for test challenge 2',
            submission_guidelines='Submission guidelines for test challenge 2',
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            approved_by_admin=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        # Past Challenge challenge
        self.challenge3 = Challenge.objects.create(
            title='Test Challenge 3',
            short_description='Short description for test challenge 2',
            description='Description for test challenge 3',
            terms_and_conditions='Terms and conditions for test challenge 3',
            submission_guidelines='Submission guidelines for test challenge 3',
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            approved_by_admin=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() - timedelta(days=1),
        )

        # Future challenge
        self.challenge4 = Challenge.objects.create(
            title='Test Challenge 4',
            short_description='Short description for test challenge 4',
            description='Description for test challenge 4',
            terms_and_conditions='Terms and conditions for test challenge 4',
            submission_guidelines='Submission guidelines for test challenge 4',
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            approved_by_admin=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() + timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

    def test_get_past_challenges(self):
        expected = [
            {
                "id": self.challenge3.pk,
                "title": self.challenge3.title,
                "short_description": self.challenge3.short_description,
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
                "short_description": self.challenge2.short_description,
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
                "short_description": self.challenge4.short_description,
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
                "short_description": self.challenge2.short_description,
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
                "short_description": self.challenge3.short_description,
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
                "short_description": self.challenge4.short_description,
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
            short_description='Short description for test challenge 3',
            description='Description for test challenge 3',
            terms_and_conditions='Terms and conditions for test challenge 3',
            submission_guidelines='Submission guidelines for test challenge 3',
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

    def test_get_challenge_by_pk_when_challenge_does_not_exists(self):
        self.url = reverse_lazy('challenges:get_challenge_by_pk',
                                kwargs={'pk': self.challenge3.pk + 10})
        expected = {
            'error': 'Challenge does not exist!'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class GetChallengeBasedOnTeams(BaseAPITestClass):

    def setUp(self):
        super(GetChallengeBasedOnTeams, self).setUp()

        self.challenge_host_team2 = ChallengeHostTeam.objects.create(
            team_name='Some Test Challenge Host Team',
            created_by=self.user)

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team2,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN)

        self.challenge = Challenge.objects.create(
            title='Test Challenge',
            short_description='Short description for test challenge',
            description='Description for test challenge',
            terms_and_conditions='Terms and conditions for test challenge',
            submission_guidelines='Submission guidelines for test challenge',
            creator=self.challenge_host_team,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=True,
        )

        self.challenge2 = Challenge.objects.create(
            title='Some Test Challenge',
            short_description='Short description for some test challenge',
            description='Description for some test challenge',
            terms_and_conditions='Terms and conditions for some test challenge',
            submission_guidelines='Submission guidelines for some test challenge',
            creator=self.challenge_host_team2,
            published=True,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=True,
        )

        self.participant_team2 = ParticipantTeam.objects.create(
            team_name='Some Participant Team',
            created_by=self.user)

        self.participant2 = Participant.objects.create(
            user=self.user,
            status=Participant.SELF,
            team=self.participant_team2)

        self.challenge2.participant_teams.add(self.participant_team2)

    def test_get_challenge_when_host_team_is_given(self):
        self.url = reverse_lazy('challenges:get_challenges_based_on_teams')

        expected = [{
            "id": self.challenge2.pk,
            "title": self.challenge2.title,
            "short_description": self.challenge2.short_description,
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
                "created_by": self.challenge2.creator.created_by.username
            },
            "published": self.challenge2.published,
            "enable_forum": self.challenge2.enable_forum,
            "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
            "is_active": True
        }]

        response = self.client.get(self.url, {'host_team': self.challenge_host_team2.pk})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_participant_team_is_given(self):
        self.url = reverse_lazy('challenges:get_challenges_based_on_teams')

        expected = [{
            "id": self.challenge2.pk,
            "title": self.challenge2.title,
            "short_description": self.challenge2.short_description,
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
                "created_by": self.challenge2.creator.created_by.username
            },
            "published": self.challenge2.published,
            "enable_forum": self.challenge2.enable_forum,
            "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
            "is_active": True
        }]

        response = self.client.get(self.url, {'participant_team': self.participant_team2.pk})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_mode_is_participant(self):
        self.url = reverse_lazy('challenges:get_challenges_based_on_teams')

        expected = [{
            "id": self.challenge2.pk,
            "title": self.challenge2.title,
            "short_description": self.challenge2.short_description,
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
                "created_by": self.challenge2.creator.created_by.username
            },
            "published": self.challenge2.published,
            "enable_forum": self.challenge2.enable_forum,
            "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
            "is_active": True
        }]

        response = self.client.get(self.url, {'mode': 'participant'})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_mode_is_host(self):
        self.url = reverse_lazy('challenges:get_challenges_based_on_teams')

        expected = [
            {
                "id": self.challenge.pk,
                "title": self.challenge.title,
                "short_description": self.challenge.short_description,
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
            },
            {
                "id": self.challenge2.pk,
                "title": self.challenge2.title,
                "short_description": self.challenge2.short_description,
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
                    "created_by": self.challenge2.creator.created_by.username
                },
                "published": self.challenge2.published,
                "enable_forum": self.challenge2.enable_forum,
                "anonymous_leaderboard": self.challenge2.anonymous_leaderboard,
                "is_active": True
            }
        ]

        response = self.client.get(self.url, {'mode': 'host'})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_with_incorrect_url_pattern(self):
        self.url = reverse_lazy('challenges:get_challenges_based_on_teams')

        expected = {
            'error': 'Invalid url pattern!'
        }
        response = self.client.get(self.url, {'invalid_q_param': 'invalidvalue'})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_get_challenge_with_incorrect_url_pattern_with_all_values(self):
        self.url = reverse_lazy('challenges:get_challenges_based_on_teams')

        expected = {
            'error': 'Invalid url pattern!'
        }
        response = self.client.get(self.url, {'host_team': self.challenge_host_team2.pk,
                                              'participant_team': self.participant_team2.pk,
                                              'mode': 'participant'})
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
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   'Dummy file content', content_type='text/plain'),
                max_submissions_per_day=100000,
                max_submissions=100000,
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
                "is_active": True,
                "codename": "Phase Code Name",
                "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,
                "max_submissions": self.challenge_phase.max_submissions,
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_phase_when_user_is_not_authenticated(self):
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
                "is_active": True,
                "codename": "Phase Code Name",
                "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,
                "max_submissions": self.challenge_phase.max_submissions,
            }
        ]
        self.client.force_authenticate(user=None)
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

    def test_get_challenge_phase_when_a_phase_is_not_public(self):
        self.challenge_phase.is_public = False
        self.challenge_phase.save()

        expected = []

        self.client.force_authenticate(user=None)
        response = self.client.get(self.url, {})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateChallengePhaseTest(BaseChallengePhaseClass):

    def setUp(self):
        super(CreateChallengePhaseTest, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_phase_list',
                                kwargs={'challenge_pk': self.challenge.pk})
        self.data = {
            'name': 'New Challenge Phase',
            'description': 'Description for new challenge phase',
            'start_date': "{0}{1}".format(self.challenge_phase.start_date.isoformat(), 'Z').replace("+00:00", ""),
            'end_date': "{0}{1}".format(self.challenge_phase.end_date.isoformat(), 'Z').replace("+00:00", ""),
        }

    @override_settings(MEDIA_ROOT='/tmp/evalai')
    def test_create_challenge_phase_with_all_data(self):
        self.data['test_annotation'] = SimpleUploadedFile('another_test_file.txt',
                                                          'Another Dummy file content',
                                                          content_type='text/plain')
        self.data['codename'] = "Test Code Name"
        response = self.client.post(self.url, self.data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    @override_settings(MEDIA_ROOT='/tmp/evalai')
    def test_create_challenge_phase_with_same_codename(self):
        self.data['test_annotation'] = SimpleUploadedFile('another_test_file.txt',
                                                          'Another Dummy file content',
                                                          content_type='text/plain')

        expected = {
            'non_field_errors': ['The fields codename, challenge must make a unique set.']
        }
        response = self.client.post(self.url, self.data, format='multipart')
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_challenge_phase_with_no_data(self):
        del self.data['name']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_challenge_phase_when_user_is_not_authenticated(self):
        self.client.force_authenticate(user=None)

        expected = {
            'error': 'Authentication credentials were not provided.'
        }

        response = self.client.post(self.url, {})
        self.assertEqual(response.data.values()[0], expected['error'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_challenge_phase_when_user_is_not_creator(self):
        self.user1 = User.objects.create(
            username='otheruser',
            password='other_secret_password'
        )

        self.challenge_host_team1 = ChallengeHostTeam.objects.create(
            team_name='Other Test Challenge Host Team',
            created_by=self.user1
        )

        # Now allot self.user as also a host of self.challenge_host_team1
        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team1,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN
        )

        self.challenge2 = Challenge.objects.create(
            title='Other Test Challenge',
            short_description='Short description for other test challenge',
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

        self.url = reverse_lazy('challenges:get_challenge_phase_list',
                                kwargs={'challenge_pk': self.challenge2.pk})

        expected = {
            'error': 'Sorry, you are not allowed to perform this operation!'
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data.values()[0], expected['error'])
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


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
            "is_public": self.challenge_phase.is_public,
            "is_active": True,
            "codename": "Phase Code Name",
            "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,
            "max_submissions": self.challenge_phase.max_submissions,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_challenge_phase_when_user_is_not_its_creator(self):
        self.user1 = User.objects.create(
            username='someuser1',
            email="user1@test.com",
            password='secret_psassword')

        EmailAddress.objects.create(
            user=self.user1,
            email='user1@test.com',
            primary=True,
            verified=True)

        self.client.force_authenticate(user=self.user1)

        expected = {"detail": "Sorry, you are not allowed to perform this operation!"}

        response = self.client.put(self.url, {'name': 'Rose Phase', 'description': 'New description.'})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_update_challenge_phase_when_user_is_its_creator(self):
        new_name = 'Rose Phase'
        new_description = 'New description.'
        expected = {
            "id": self.challenge_phase.id,
            "name": new_name,
            "description": new_description,
            "leaderboard_public": self.challenge_phase.leaderboard_public,
            "start_date": "{0}{1}".format(self.challenge_phase.start_date.isoformat(), 'Z').replace("+00:00", ""),
            "end_date": "{0}{1}".format(self.challenge_phase.end_date.isoformat(), 'Z').replace("+00:00", ""),
            "challenge": self.challenge_phase.challenge.pk,
            "is_public": self.challenge_phase.is_public,
            "is_active": True,
            "codename": "Phase Code Name",
            "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,
            "max_submissions": self.challenge_phase.max_submissions,
        }
        response = self.client.put(self.url, {'name': new_name, 'description': new_description})
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

    def test_get_particular_challenge_phase_when_user_is_not_authenticated(self):
        self.client.force_authenticate(user=None)

        expected = {
            'error': 'Authentication credentials were not provided.'
        }

        response = self.client.post(self.url, {})
        self.assertEqual(response.data.values()[0], expected['error'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


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
            "is_public": self.challenge_phase.is_public,
            "is_active": True,
            "codename": "Phase Code Name",
            "max_submissions_per_day": self.challenge_phase.max_submissions_per_day,
            "max_submissions": self.challenge_phase.max_submissions,
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

    def test_particular_challenge_update_when_user_is_not_authenticated(self):
        self.client.force_authenticate(user=None)

        expected = {
            'error': 'Authentication credentials were not provided.'
        }

        response = self.client.post(self.url, {})
        self.assertEqual(response.data.values()[0], expected['error'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DeleteParticularChallengePhase(BaseChallengePhaseClass):

    def setUp(self):
        super(DeleteParticularChallengePhase, self).setUp()
        self.url = reverse_lazy('challenges:get_challenge_phase_detail',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'pk': self.challenge_phase.pk})

    def test_particular_challenge_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_particular_challenge_delete_when_user_is_not_authenticated(self):
        self.client.force_authenticate(user=None)

        expected = {
            'error': 'Authentication credentials were not provided.'
        }

        response = self.client.post(self.url, {})
        self.assertEqual(response.data.values()[0], expected['error'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class BaseChallengePhaseSplitClass(BaseAPITestClass):

    def setUp(self):
        super(BaseChallengePhaseSplitClass, self).setUp()
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

        self.dataset_split = DatasetSplit.objects.create(name="Test Dataset Split", codename="test-split")

        self.leaderboard = Leaderboard.objects.create(schema=json.dumps({'hello': 'world'}))

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            dataset_split=self.dataset_split,
            challenge_phase=self.challenge_phase,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC
            )

    def tearDown(self):
        shutil.rmtree('/tmp/evalai')


class GetChallengePhaseSplitTest(BaseChallengePhaseSplitClass):

    def setUp(self):
        super(GetChallengePhaseSplitTest, self).setUp()
        self.url = reverse_lazy('challenges:challenge_phase_split_list',
                                kwargs={'challenge_pk': self.challenge.pk})

    def test_get_challenge_phase_split(self):
        expected = [
            {
                "id": self.challenge_phase_split.id,
                "challenge_phase": self.challenge_phase.id,
                "challenge_phase_name": self.challenge_phase.name,
                "dataset_split": self.dataset_split.id,
                "dataset_split_name": self.dataset_split.name,
                "visibility": self.challenge_phase_split.visibility,
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_challenge_phase_split_when_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy('challenges:challenge_phase_split_list',
                                kwargs={'challenge_pk': self.challenge.pk})

        self.challenge.delete()

        expected = {
            'error': 'Challenge does not exist'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class CreateChallengeUsingZipFile(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='host',
            email='host@test.com',
            password='secret_password')

        EmailAddress.objects.create(
            user=self.user,
            email='user@test.com',
            primary=True,
            verified=True)

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name='Test Challenge Host Team',
            created_by=self.user)

        self.path = join(settings.BASE_DIR, 'examples', 'example1', 'test_zip_file')

        self.challenge = Challenge.objects.create(
            title='Challenge Title',
            short_description='Short description of the challenge (preferably 140 characters)',
            description=open(join(self.path, 'description.html'), 'rb').read().decode('utf-8'),
            terms_and_conditions=open(join(self.path, 'terms_and_conditions.html'), 'rb').read().decode('utf-8'),
            submission_guidelines=open(join(self.path, 'submission_guidelines.html'), 'rb').read().decode('utf-8'),
            evaluation_details=open(join(self.path, 'evaluation_details.html'), 'rb').read().decode('utf-8'),
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge_phase = ChallengePhase.objects.create(
                name='Challenge Phase',
                description=open(join(self.path, 'challenge_phase_description.html'), 'rb').read().decode('utf-8'),
                leaderboard_public=False,
                is_public=False,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile(open(join(self.path, 'test_annotation.txt'), 'rb').name,
                                                   open(join(self.path, 'test_annotation.txt'), 'rb').read(),
                                                   content_type='text/plain')
            )
        self.dataset_split = DatasetSplit.objects.create(name="Name of the dataset split",
                                                         codename="codename of dataset split")

        self.leaderboard = Leaderboard.objects.create(schema=json.dumps({
                                                      "labels": ["yes/no", "number", "others", "overall"],
                                                      "default_order_by": "overall"}))

        self.challenge_phase_split = ChallengePhaseSplit.objects.create(
            dataset_split=self.dataset_split,
            challenge_phase=self.challenge_phase,
            leaderboard=self.leaderboard,
            visibility=ChallengePhaseSplit.PUBLIC
            )

        self.zip_file = open(join(settings.BASE_DIR, 'examples', 'example1', 'test_zip_file.zip'), 'rb')

        self.test_zip_file = SimpleUploadedFile(self.zip_file.name,
                                                self.zip_file.read(),
                                                content_type='application/zip')

        self.zip_configuration = ChallengeConfiguration.objects.create(
            user=self.user,
            challenge=self.challenge,
            zip_configuration=SimpleUploadedFile(self.zip_file.name,
                                                 self.zip_file.read(),
                                                 content_type='application/zip'),
            stdout_file=None,
            stderr_file=None
            )
        self.client.force_authenticate(user=self.user)

        self.input_zip_file = SimpleUploadedFile('test_sample.zip',
                                                 'Dummy File Content',
                                                 content_type='application/zip')

    def test_create_challenge_using_zip_file_when_zip_file_is_not_uploaded(self):
        self.url = reverse_lazy('challenges:create_challenge_using_zip_file',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk})
        expected = {
            'zip_configuration': ['No file was submitted.']
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_challenge_using_zip_file_when_zip_file_is_not_uploaded_successfully(self):
        self.url = reverse_lazy('challenges:create_challenge_using_zip_file',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk})

        expected = {
            'zip_configuration': ['The submitted data was not a file. Check the encoding type on the form.']
        }
        response = self.client.post(self.url, {'zip_configuration': self.input_zip_file})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_challenge_using_zip_file_when_server_error_occurs(self):
        self.url = reverse_lazy('challenges:create_challenge_using_zip_file',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk})
        expected = {
            'error': 'A server error occured while processing zip file. Please try uploading it again!'
            }
        response = self.client.post(self.url, {'zip_configuration': self.input_zip_file}, format='multipart')
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_create_challenge_using_zip_file_when_challenge_host_team_does_not_exists(self):
        self.url = reverse_lazy('challenges:create_challenge_using_zip_file',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk+10})
        expected = {
            'detail': 'ChallengeHostTeam {} does not exist'.format(self.challenge_host_team.pk+10)
        }
        response = self.client.post(self.url, {'zip_configuration': self.input_zip_file}, format='multipart')
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_challenge_using_zip_file_when_user_is_not_authenticated(self):
        self.url = reverse_lazy('challenges:create_challenge_using_zip_file',
                                kwargs={'challenge_host_team_pk': self.challenge_host_team.pk})
        self.client.force_authenticate(user=None)

        expected = {
            'error': 'Authentication credentials were not provided.'
        }

        response = self.client.post(self.url, {})
        self.assertEqual(response.data.values()[0], expected['error'])
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GetAllSubmissionsTest(BaseAPITestClass):

    def setUp(self):
        super(GetAllSubmissionsTest, self).setUp()

        self.user5 = User.objects.create(
            username='otheruser',
            password='other_secret_password',
            email='user5@test.com',)

        self.user6 = User.objects.create(
            username='participant',
            password='secret password',
            email='user6@test.com',)

        self.user7 = User.objects.create(
            username='not a challenge host of challenge5',
            password='secret password')

        EmailAddress.objects.create(
            user=self.user5,
            email='user5@test.com',
            primary=True,
            verified=True)

        EmailAddress.objects.create(
            user=self.user6,
            email='user6@test.com',
            primary=True,
            verified=True)

        EmailAddress.objects.create(
            user=self.user7,
            email='user7@test.com',
            primary=True,
            verified=True)

        self.challenge_host_team7 = ChallengeHostTeam.objects.create(
            team_name='Other Test Challenge Host Team7',
            created_by=self.user7
        )
        self.challenge_host_team5 = ChallengeHostTeam.objects.create(
            team_name='Other Test Challenge Host Team5',
            created_by=self.user5
        )

        # Now allot self.user as also a host of self.challenge_host_team1
        self.challenge_host5 = ChallengeHost.objects.create(
            user=self.user5,
            team_name=self.challenge_host_team5,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN
        )

        self.participant_team6 = ParticipantTeam.objects.create(
            team_name='Participant Team 1 for Challenge5',
            created_by=self.user6)

        self.participant_team7 = ParticipantTeam.objects.create(
            team_name='Participant Team 2 for Challenge5',
            created_by=self.user7)

        self.participant6 = Participant.objects.create(
            user=self.user6,
            status=Participant.ACCEPTED,
            team=self.participant_team6)

        self.challenge5 = Challenge.objects.create(
            title='Other Test Challenge',
            short_description='Short description for other test challenge',
            description='Description for other test challenge',
            terms_and_conditions='Terms and conditions for other test challenge',
            submission_guidelines='Submission guidelines for other test challenge',
            creator=self.challenge_host_team5,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
        )

        try:
            os.makedirs('/tmp/evalai')
        except OSError:
            pass

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge5_phase1 = ChallengePhase.objects.create(
                name='Challenge Phase 1',
                description='Description for Challenge Phase 1',
                leaderboard_public=False,
                codename="Phase Code Name 1",
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge5,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   'Dummy file content 1', content_type='text/plain')
            )

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge5_phase2 = ChallengePhase.objects.create(
                name='Challenge Phase 2',
                description='Description for Challenge Phase',
                leaderboard_public=False,
                codename="Phase Code Name 2",
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge5,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   'Dummy file content 2', content_type='text/plain')
            )

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge5_phase3 = ChallengePhase.objects.create(
                name='Challenge Phase',
                description='Description for Challenge Phase',
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge5,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   'Dummy file content', content_type='text/plain')
            )

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.submission1 = Submission.objects.create(
                participant_team=self.participant_team6,
                challenge_phase=self.challenge5_phase3,
                created_by=self.challenge_host_team5.created_by,
                status='submitted',
                input_file=SimpleUploadedFile('test_sample_file.txt',
                                              'Dummy file content', content_type='text/plain'),
                method_name="Test Method 1",
                method_description="Test Description 1",
                project_url="http://testserver1/",
                publication_url="http://testserver1/",
                is_public=True,
            )

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.submission2 = Submission.objects.create(
                participant_team=self.participant_team6,
                challenge_phase=self.challenge5_phase1,
                created_by=self.challenge_host_team5.created_by,
                status='submitted',
                input_file=SimpleUploadedFile('test_sample_file.txt',
                                              'Dummy file content', content_type='text/plain'),
                method_name="Test Method 2",
                method_description="Test Description 2",
                project_url="http://testserver2/",
                publication_url="http://testserver2/",
                is_public=True,
            )

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.submission3 = Submission.objects.create(
                participant_team=self.participant_team6,
                challenge_phase=self.challenge5_phase1,
                created_by=self.challenge_host_team5.created_by,
                status='submitted',
                input_file=SimpleUploadedFile('test_sample_file.txt',
                                              'Dummy file content', content_type='text/plain'),
                method_name="Test Method 3",
                method_description="Test Description 3",
                project_url="http://testserver3/",
                publication_url="http://testserver3/",
                is_public=True,
            )

        self.client.force_authenticate(user=self.user6)

    def test_get_all_submissions_when_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_all_submissions_of_challenge',
                                kwargs={'challenge_pk': self.challenge5.pk+10,
                                        'challenge_phase_pk': self.challenge5_phase3.pk})
        expected = {
            'detail': 'Challenge {} does not exist'.format(self.challenge5.pk+10)
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_all_submissions_when_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy('challenges:get_all_submissions_of_challenge',
                                kwargs={'challenge_pk': self.challenge5.pk,
                                        'challenge_phase_pk': self.challenge5_phase3.pk+10})
        expected = {
            'error': 'Challenge Phase {} does not exist'.format(self.challenge5_phase3.pk+10)
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_all_submissions_when_user_is_host_of_challenge(self):
        self.url_phase1 = reverse_lazy('challenges:get_all_submissions_of_challenge',
                                       kwargs={'challenge_pk': self.challenge5.pk,
                                               'challenge_phase_pk': self.challenge5_phase1.pk})
        self.url_phase2 = reverse_lazy('challenges:get_all_submissions_of_challenge',
                                       kwargs={'challenge_pk': self.challenge5.pk,
                                               'challenge_phase_pk': self.challenge5_phase2.pk})
        self.client.force_authenticate(user=self.user5)
        submissions = [self.submission3, self.submission2]
        expected = []
        for submission in submissions:
            expected.append(
                {
                    "id": submission.id,
                    "participant_team": submission.participant_team.team_name,
                    "challenge_phase": submission.challenge_phase.name,
                    "created_by": submission.created_by.username,
                    "status": submission.status,
                    "is_public": submission.is_public,
                    "submission_number": submission.submission_number,
                    "submitted_at": "{0}{1}".format(submission.submitted_at.isoformat(), 'Z').replace("+00:00", ""),
                    'execution_time': submission.execution_time,
                    "input_file": "http://testserver%s" % (submission.input_file.url),
                    "stdout_file": None,
                    "stderr_file": None,
                    "submission_result_file": None,
                    "submission_metadata_file": None,
                    "participant_team_members_email_ids": ['user6@test.com'],
                    "participant_team_members": [{'username': 'participant', 'email': 'user6@test.com'}],
                    "created_at": submission.created_at,
                    "method_name": submission.method_name,
                }
            )
        response_phase1 = self.client.get(self.url_phase1, {})
        response_phase2 = self.client.get(self.url_phase2, {})
        self.assertEqual(response_phase1.data['results'], expected)
        self.assertEqual(response_phase1.status_code, status.HTTP_200_OK)
        self.assertEqual(response_phase2.data['results'], [])
        self.assertEqual(response_phase2.status_code, status.HTTP_200_OK)

    def test_get_all_submissions_when_user_is_participant_of_challenge(self):
        self.url = reverse_lazy('challenges:get_all_submissions_of_challenge',
                                kwargs={'challenge_pk': self.challenge5.pk,
                                        'challenge_phase_pk': self.challenge5_phase3.pk})
        self.client.force_authenticate(user=self.user6)
        expected = [
            {
                'id': self.submission1.id,
                'participant_team': self.submission1.participant_team.pk,
                'participant_team_name': self.submission1.participant_team.team_name,
                'execution_time': self.submission1.execution_time,
                'challenge_phase': self.submission1.challenge_phase.pk,
                'created_by': self.submission1.created_by.pk,
                'status': self.submission1.status,
                'input_file': "http://testserver%s" % (self.submission1.input_file.url),
                'method_name': self.submission1.method_name,
                'method_description': self.submission1.method_description,
                'project_url': self.submission1.project_url,
                'publication_url': self.submission1.publication_url,
                'stdout_file': None,
                'stderr_file': None,
                'submission_result_file': None,
                "submitted_at": "{0}{1}".format(self.submission1.submitted_at.isoformat(), 'Z').replace("+00:00", ""),
                "is_public": self.submission1.is_public,
                "when_made_public": self.submission1.when_made_public,
            }
        ]
        self.challenge5.participant_teams.add(self.participant_team6)
        self.challenge5.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data['results'], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_all_submissions_when_user_is_neither_host_nor_participant_of_challenge(self):
        self.client.force_authenticate(user=self.user7)
        self.url = reverse_lazy('challenges:get_all_submissions_of_challenge',
                                kwargs={'challenge_pk': self.challenge5.pk,
                                        'challenge_phase_pk': self.challenge5_phase3.pk})
        expected = {
            'error': 'You are neither host nor participant of the challenge!'
        }
        self.challenge5.participant_teams.add(self.participant_team6)
        self.challenge5.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DownloadAllSubmissionsFileTest(BaseAPITestClass):

    def setUp(self):
        super(DownloadAllSubmissionsFileTest, self).setUp()

        self.user1 = User.objects.create(
            username='otheruser1',
            password='other_secret_password',
            email='user1@test.com',)

        self.user2 = User.objects.create(
            username='otheruser2',
            password='other_secret_password',
            email='user2@test.com',)

        EmailAddress.objects.create(
            user=self.user1,
            email='user1@test.com',
            primary=True,
            verified=True)

        EmailAddress.objects.create(
            user=self.user2,
            email='user2@test.com',
            primary=True,
            verified=True)

        self.participant_team1 = ParticipantTeam.objects.create(
            team_name='Participant Team for Challenge8',
            created_by=self.user1)

        self.participant1 = Participant.objects.create(
            user=self.user1,
            status=Participant.ACCEPTED,
            team=self.participant_team1)

        try:
            os.makedirs('/tmp/evalai')
        except OSError:
            pass

        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.challenge_phase = ChallengePhase.objects.create(
                name='Challenge Phase',
                description='Description for Challenge Phase',
                leaderboard_public=False,
                is_public=True,
                start_date=timezone.now() - timedelta(days=2),
                end_date=timezone.now() + timedelta(days=1),
                challenge=self.challenge,
                test_annotation=SimpleUploadedFile('test_sample_file.txt',
                                                   'Dummy file content', content_type='text/plain')
            )
        with self.settings(MEDIA_ROOT='/tmp/evalai'):
            self.submission = Submission.objects.create(
                participant_team=self.participant_team1,
                challenge_phase=self.challenge_phase,
                created_by=self.participant_team1.created_by,
                status='submitted',
                input_file=SimpleUploadedFile('test_sample_file.txt',
                                              'Dummy file content', content_type='text/plain'),
                method_name="Test Method",
                method_description="Test Description",
                project_url="http://testserver/",
                publication_url="http://testserver/",
                is_public=True,
            )

        self.file_type_csv = 'csv'

        self.file_type_pdf = 'pdf'

    def test_download_all_submissions_when_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:download_all_submissions',
                                kwargs={'challenge_pk': self.challenge.pk+10,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'file_type': self.file_type_csv})
        expected = {
            'detail': 'Challenge {} does not exist'.format(self.challenge.pk+10)
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_all_submissions_when_challenge_phase_does_not_exist(self):
        self.url = reverse_lazy('challenges:download_all_submissions',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk+10,
                                        'file_type': self.file_type_csv})
        expected = {
            'error': 'Challenge Phase {} does not exist'.format(self.challenge_phase.pk+10)
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_download_all_submissions_when_file_type_is_not_csv(self):
        self.url = reverse_lazy('challenges:download_all_submissions',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'file_type': self.file_type_pdf})
        expected = {
            'error': 'The file type requested is not valid!'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_download_all_submissions_when_user_is_challenge_host(self):
        self.url = reverse_lazy('challenges:download_all_submissions',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'file_type': self.file_type_csv})
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_all_submissions_when_user_is_challenge_participant(self):
        self.url = reverse_lazy('challenges:download_all_submissions',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'file_type': self.file_type_csv})

        self.challenge.participant_teams.add(self.participant_team1)
        self.challenge.save()
        response = self.client.get(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_download_all_submissions_when_user_is_neither_a_challenge_host_nor_a_participant(self):
        self.url = reverse_lazy('challenges:download_all_submissions',
                                kwargs={'challenge_pk': self.challenge.pk,
                                        'challenge_phase_pk': self.challenge_phase.pk,
                                        'file_type': self.file_type_csv})

        self.client.force_authenticate(user=self.user2)

        expected = {
            'error': 'You are neither host nor participant of the challenge!'
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CreateLeaderboardTest(BaseAPITestClass):

    def setUp(self):
        super(CreateLeaderboardTest, self).setUp()
        self.url = reverse_lazy('challenges:create_leaderboard')
        self.data = [
            {'schema': {'key': 'value'}},
            {'schema': {'key2': 'value2'}}
            ]

    def test_create_leaderboard_with_all_data(self):
        self.url = reverse_lazy('challenges:create_leaderboard')
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_leaderboard_with_no_data(self):
        self.url = reverse_lazy('challenges:create_leaderboard')
        self.data = []
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetOrUpdateLeaderboardTest(BaseAPITestClass):

    def setUp(self):
        super(GetOrUpdateLeaderboardTest, self).setUp()
        self.leaderboard = Leaderboard.objects.create(schema=json.dumps({
                                                      "labels": ["yes/no", "number", "others", "overall"],
                                                      "default_order_by": "overall"}))

        self.url = reverse_lazy('challenges:get_or_update_leaderboard',
                                kwargs={'leaderboard_pk': self.leaderboard.pk})
        self.data = {
            'schema': {'key': 'updated schema'}
            }

    def test_get_or_update_leaderboard_when_leaderboard_doesnt_exist(self):
        self.url = reverse_lazy('challenges:get_or_update_leaderboard',
                                kwargs={'leaderboard_pk': self.leaderboard.pk+10})
        expected = {
            'detail': 'Leaderboard {} does not exist'.format(self.leaderboard.pk+10)
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_leaderboard(self):
        self.url = reverse_lazy('challenges:get_or_update_leaderboard',
                                kwargs={'leaderboard_pk': self.leaderboard.pk})
        expected = {
            'id': self.leaderboard.pk,
            'schema': self.leaderboard.schema,
        }
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_leaderboard_with_all_data(self):
        self.url = reverse_lazy('challenges:get_or_update_leaderboard',
                                kwargs={'leaderboard_pk': self.leaderboard.pk})
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_leaderboard_with_no_data(self):
        self.url = reverse_lazy('challenges:get_or_update_leaderboard',
                                kwargs={'leaderboard_pk': self.leaderboard.pk})
        del self.data['schema']
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateDatasetSplitTest(BaseAPITestClass):

    def setUp(self):
        super(CreateDatasetSplitTest, self).setUp()
        self.url = reverse_lazy('challenges:create_dataset_split')

        self.data = [
            {"name": "Dataset Split1",
             "codename": "Dataset split codename1"},
            {"name": "Dataset split2",
             "codename": "Dataset split codename2"}
        ]

    def test_create_dataset_split_with_all_data(self):
        self.url = reverse_lazy('challenges:create_dataset_split')
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_dataset_split_with_no_data(self):
        self.url = reverse_lazy('challenges:create_dataset_split')
        self.data = []
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetOrUpdateDatasetSplitTest(BaseAPITestClass):

    def setUp(self):
        super(GetOrUpdateDatasetSplitTest, self).setUp()
        self.dataset_split = DatasetSplit.objects.create(name="Name of the dataset split",
                                                         codename="codename of dataset split")

        self.url = reverse_lazy('challenges:get_or_update_dataset_split',
                                kwargs={'dataset_split_pk': self.dataset_split.pk})
        self.data = {
            'name': 'Updated Name of dataset split',
            'codename': 'Updated codename of dataset split'
            }

    def test_get_or_update_dataset_split_when_dataset_split_doesnt_exist(self):
        self.url = reverse_lazy('challenges:get_or_update_dataset_split',
                                kwargs={'dataset_split_pk': self.dataset_split.pk+10})
        expected = {
            'detail': 'DatasetSplit {} does not exist'.format(self.dataset_split.pk+10)
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_dataset_split(self):
        self.url = reverse_lazy('challenges:get_or_update_dataset_split',
                                kwargs={'dataset_split_pk': self.dataset_split.pk})
        expected = {
            'id': self.dataset_split.pk,
            'name': self.dataset_split.name,
            'codename': self.dataset_split.codename
        }
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_dataset_split_with_all_data(self):
        self.url = reverse_lazy('challenges:get_or_update_dataset_split',
                                kwargs={'dataset_split_pk': self.dataset_split.pk})
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_dataset_split_with_no_data(self):
        self.url = reverse_lazy('challenges:get_or_update_dataset_split',
                                kwargs={'dataset_split_pk': self.dataset_split.pk})
        del self.data['codename']
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateChallengePhaseSplitTest(BaseChallengePhaseSplitClass):

    def setUp(self):
        super(CreateChallengePhaseSplitTest, self).setUp()
        self.url = reverse_lazy('challenges:create_challenge_phase_split')

        self.data = [
            {"dataset_split": self.dataset_split.pk,
             "challenge_phase": self.challenge_phase.pk,
             "leaderboard": self.leaderboard.pk,
             "visibility": 1},
            {"dataset_split": self.dataset_split.pk,
             "challenge_phase": self.challenge_phase.pk,
             "leaderboard": self.leaderboard.pk,
             "visibility": 3}
            ]

    def test_create_challenge_phase_split_with_all_data(self):
        self.url = reverse_lazy('challenges:create_challenge_phase_split')
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_dataset_split_with_no_data(self):
        self.url = reverse_lazy('challenges:create_challenge_phase_split')
        self.data = []
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetOrUpdateChallengePhaseSplitTest(BaseChallengePhaseSplitClass):

    def setUp(self):
        super(GetOrUpdateChallengePhaseSplitTest, self).setUp()
        self.url = reverse_lazy('challenges:get_or_update_dataset_split',
                                kwargs={'challenge_phase_split_pk': self.challenge_phase_split.pk})
        self.leaderboard1 = Leaderboard.objects.create(schema=json.dumps({
                                                      "labels": ["yes/no", "number", "others", "overall"],
                                                      "default_order_by": "overall"}))
        self.data = {
            'leaderboard': self.leaderboard1.pk,
            }

    def test_get_or_update_dataset_split_when_dataset_split_doesnt_exist(self):
        self.url = reverse_lazy('challenges:get_or_update_challenge_phase_split',
                                kwargs={'challenge_phase_split_pk': self.challenge_phase_split.pk+10})
        expected = {
            'detail': 'ChallengePhaseSplit {} does not exist'.format(self.challenge_phase_split.pk+10)
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_dataset_split(self):
        self.url = reverse_lazy('challenges:get_or_update_challenge_phase_split',
                                kwargs={'challenge_phase_split_pk': self.challenge_phase_split.pk})
        expected = {
            'id': self.challenge_phase_split.pk,
            'dataset_split': self.dataset_split.pk,
            'leaderboard': self.leaderboard.pk,
            'challenge_phase': self.challenge_phase.pk,
            'visibility': self.challenge_phase_split.visibility
        }
        response = self.client.get(self.url)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_challenge_phase_split_with_all_data(self):
        self.url = reverse_lazy('challenges:get_or_update_challenge_phase_split',
                                kwargs={'challenge_phase_split_pk': self.challenge_phase_split.pk})
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update_dataset_split_with_no_data(self):
        self.url = reverse_lazy('challenges:get_or_update_challenge_phase_split',
                                kwargs={'challenge_phase_split_pk': self.challenge_phase_split.pk})
        del self.data['leaderboard']
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class StarChallengesTest(BaseAPITestClass):
    def setUp(self):
        super(StarChallengesTest, self).setUp()
        self.url = reverse_lazy('challenges:star_challenge',
                                kwargs={'challenge_pk': self.challenge.pk})
        self.user2 = User.objects.create(
            username='someuser2',
            email="user2@test.com",
            password='secret_password')

        EmailAddress.objects.create(
            user=self.user2,
            email='user2@test.com',
            primary=True,
            verified=True)

        self.challenge1 = Challenge.objects.create(
            title='Test Challenge1',
            short_description='Short description for test challenge1',
            description='Description for test challenge1',
            terms_and_conditions='Terms and conditions for test challenge1',
            submission_guidelines='Submission guidelines for test challenge1',
            creator=self.challenge_host_team,
            published=False,
            enable_forum=True,
            anonymous_leaderboard=False,
            start_date=timezone.now() - timedelta(days=2),
            end_date=timezone.now() + timedelta(days=1),
            approved_by_admin=False,
        )

        self.star_challenge = StarChallenge.objects.create(user=self.user,
                                                           challenge=self.challenge,
                                                           is_starred=True)
        self.client.force_authenticate(user=self.user)

    def test_star_challenge_when_challenge_does_not_exist(self):
        self.url = reverse_lazy('challenges:star_challenge',
                                kwargs={'challenge_pk': self.challenge.pk+10})

        expected = {
            'detail': 'Challenge {} does not exist'.format(self.challenge.pk+10)
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_challenge_when_user_has_starred(self):
        self.url = reverse_lazy('challenges:star_challenge',
                                kwargs={'challenge_pk': self.challenge.pk})
        expected = {
            'user': self.user.pk,
            'challenge': self.challenge.pk,
            'count': 1,
            'is_starred': True,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_user_hasnt_starred(self):
        self.url = reverse_lazy('challenges:star_challenge',
                                kwargs={'challenge_pk': self.challenge.pk})
        self.client.force_authenticate(user=self.user2)
        expected = {
            'is_starred': False,
            'count': 1,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_when_no_user_has_starred_or_unstarred_it(self):
        self.url = reverse_lazy('challenges:star_challenge',
                                kwargs={'challenge_pk': self.challenge1.pk})
        expected = {
            'is_starred': False,
            'count': 0,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_unstar_challenge(self):
        self.url = reverse_lazy('challenges:star_challenge',
                                kwargs={'challenge_pk': self.challenge.pk})
        self.star_challenge.is_starred = False
        expected = {
            'user': self.user.pk,
            'challenge': self.challenge.pk,
            'count': 0,
            'is_starred': self.star_challenge.is_starred,
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_star_challenge(self):
        self.url = reverse_lazy('challenges:star_challenge',
                                kwargs={'challenge_pk': self.challenge.pk})
        self.star_challenge.delete()
        expected = {
            'user': self.user.pk,
            'challenge': self.challenge.pk,
            'count': 1,
            'is_starred': True,
        }
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
