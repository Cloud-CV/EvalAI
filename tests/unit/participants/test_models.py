from django.test import TestCase
from django.contrib.auth.models import User

from participants.models import Participant, ParticipantTeam


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="user", email="user@test.com", password="password"
        )
        self.participant_team = ParticipantTeam.objects.create(
            team_name="Participant Team", created_by=self.user
        )


class ParticipantTestCase(BaseTestCase):
    def setUp(self):
        super(ParticipantTestCase, self).setUp()
        self.participant = Participant.objects.create(
            user=self.user,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

    def test__str__(self):
        self.assertEqual(
            "{}".format(self.participant.user), self.participant.__str__()
        )


class ParticipantTeamTestCase(BaseTestCase):
    def setUp(self):
        super(ParticipantTeamTestCase, self).setUp()
        self.participant = Participant.objects.create(
            user=self.user,
            status=Participant.ACCEPTED,
            team=self.participant_team,
        )

    def test__str__(self):
        self.assertEqual(
            self.participant_team.team_name, self.participant_team.__str__()
        )

    def test_get_all_participants_email(self):
        self.assertEqual(
            [self.participant.user.email],
            self.participant_team.get_all_participants_email(),
        )
