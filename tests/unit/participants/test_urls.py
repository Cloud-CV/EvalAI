from django.urls import reverse_lazy
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress
from rest_framework.test import APITestCase, APIClient

from participants.models import ParticipantTeam


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


class TestStringMethods(BaseAPITestClass):

    def test_participants_urls(self):
        url = reverse_lazy('participants:get_participant_team_list')
        self.assertEqual(unicode(url), '/api/participants/participant_team')

        url = reverse_lazy('participants:get_participant_team_details',
                           kwargs={'pk': self.participant_team.pk})
        self.assertEqual(unicode(
            url), '/api/participants/participant_team/' + str(self.participant_team.pk))

        url = reverse_lazy('participants:invite_participant_to_team',
                           kwargs={'pk': self.participant_team.pk})
        self.assertEqual(unicode(url), '/api/participants/participant_team/' +
                         str(self.participant_team.pk) + '/invite')

        url = reverse_lazy('participants:delete_participant_from_team',
                           kwargs={'participant_team_pk': self.participant_team.pk,
                                   'participant_pk': self.invite_user.pk})
        self.assertEqual(unicode(url), '/api/participants/participant_team/' + str(self.participant_team.pk) +
                         '/participant/' + str(self.invite_user.pk))

        url = reverse_lazy('participants:get_teams_and_corresponding_challenges_for_a_participant')
        self.assertEqual(unicode(url), '/api/participants/participant_teams/challenges/user')

        url = reverse_lazy('participants:remove_self_from_participant_team',
                           kwargs={'participant_team_pk': self.participant_team.pk})
        self.assertEqual(unicode(url), '/api/participants/remove_self_from_participant_team/' +
                         str(self.participant_team.pk))

        url = reverse_lazy('participants:participants_list_based_on_team',
                           kwargs={'pk': self.participant_team.pk})
        self.assertEqual(unicode(
            url), '/api/participants/participants_list_based_on_team/' + str(self.participant_team.pk))
        