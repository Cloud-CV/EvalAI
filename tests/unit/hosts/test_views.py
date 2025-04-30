from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from hosts.models import ChallengeHost, ChallengeHostTeam
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.invite_user = User.objects.create(
            username="otheruser",
            email="other@platform.com",
            password="other_secret_password",
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.client.force_authenticate(user=self.user)


class GetChallengeHostTeamTest(BaseAPITestClass):
    url = reverse_lazy("hosts:get_challenge_host_team_list")

    def setUp(self):
        super(GetChallengeHostTeamTest, self).setUp()
        self.url = reverse_lazy("hosts:get_challenge_host_team_list")

        self.user2 = User.objects.create(
            username="someuser2",
            email="user2@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user2,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.READ,
        )

    def test_get_challenge_host_team(self):
        expected = [
            {
                "id": self.challenge_host_team.pk,
                "team_name": self.challenge_host_team.team_name,
                "created_by": self.challenge_host_team.created_by.username,
                "team_url": self.challenge_host_team.team_url,
                "members": [
                    {
                        "id": self.challenge_host.id,
                        "permissions": self.challenge_host.permissions,
                        "status": self.challenge_host.status,
                        "team_name": self.challenge_host.team_name.id,
                        "user": self.challenge_host.user.username,
                    },
                    {
                        "id": self.challenge_host2.id,
                        "permissions": self.challenge_host2.permissions,
                        "status": self.challenge_host2.status,
                        "team_name": self.challenge_host2.team_name.id,
                        "user": self.challenge_host2.user.username,
                    },
                ],
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateChallengeHostTeamTest(BaseAPITestClass):
    url = reverse_lazy("hosts:get_challenge_host_team_list")

    def setUp(self):
        super(CreateChallengeHostTeamTest, self).setUp()
        self.data = {"team_name": "Test team"}

    def test_create_challenge_host_team_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_host_team_when_team_with_same_name_already_exists(
        self,
    ):

        expected = {
            "team_name": [
                "challenge host team with this team name already exists."
            ]
        }

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Trying to create a team with the same team name
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected)

    def test_create_challenge_host_team_with_no_data(self):
        del self.data["team_name"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetParticularChallengeHostTeam(BaseAPITestClass):
    def setUp(self):
        super(GetParticularChallengeHostTeam, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_team_details",
            kwargs={"pk": self.challenge_host_team.pk},
        )

        self.user2 = User.objects.create(
            username="someuser2",
            email="user2@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user2,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.READ,
        )

    def test_get_particular_challenge_host_team(self):
        expected = {
            "id": self.challenge_host_team.pk,
            "team_name": self.challenge_host_team.team_name,
            "created_by": self.user.username,
            "team_url": self.challenge_host_team.team_url,
            "members": [
                {
                    "id": self.challenge_host.id,
                    "permissions": self.challenge_host.permissions,
                    "status": self.challenge_host.status,
                    "team_name": self.challenge_host.team_name.id,
                    "user": self.challenge_host.user.username,
                },
                {
                    "id": self.challenge_host2.id,
                    "permissions": self.challenge_host2.permissions,
                    "status": self.challenge_host2.status,
                    "team_name": self.challenge_host2.team_name.id,
                    "user": self.challenge_host2.user.username,
                },
            ],
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UpdateParticularChallengeHostTeam(BaseAPITestClass):
    def setUp(self):
        super(UpdateParticularChallengeHostTeam, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_team_details",
            kwargs={"pk": self.challenge_host_team.pk},
        )
        self.data = {"team_name": "Test Team"}
        self.partial_update_team_name = "Partial Update Test Team"
        self.update_team_name = "All Update Test Team"

    def test_particular_challenge_host_team_partial_update(self):
        self.data = {"team_name": self.partial_update_team_name}
        expected = {
            "id": self.challenge_host_team.pk,
            "team_name": self.partial_update_team_name,
            "created_by": self.user.username,
            "team_url": self.challenge_host_team.team_url,
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_update(self):
        self.data = {"team_name": self.update_team_name}
        expected = {
            "id": self.challenge_host_team.pk,
            "team_name": self.update_team_name,
            "created_by": self.user.username,
            "team_url": self.challenge_host_team.team_url,
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_update_with_no_data(self):
        self.data = {"team_name": ""}
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_particular_challenge_host_team_does_not_exist(self):
        self.url = reverse_lazy(
            "hosts:get_challenge_host_team_details",
            kwargs={"pk": self.challenge_host_team.pk + 1},
        )
        expected = {"error": "ChallengeHostTeam does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class DeleteParticularChallengeHostTeam(BaseAPITestClass):
    def setUp(self):
        super(DeleteParticularChallengeHostTeam, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_team_details",
            kwargs={"pk": self.challenge_host_team.pk},
        )

    # TODO: Add test back with API
    # def test_particular_challenge_host_team_delete(self):
    #     response = self.client.delete(self.url, {})
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class GetChallengeHostTest(BaseAPITestClass):
    def setUp(self):
        super(GetChallengeHostTest, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )

    def test_get_challenge_team(self):
        expected = [
            {
                "id": self.challenge_host.pk,
                "user": self.challenge_host.user.username,
                "team_name": self.challenge_host.team_name.pk,
                "status": self.challenge_host.status,
                "permissions": self.challenge_host.permissions,
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_team_with_status_as_query_parameter(self):
        self.data = {"status": ChallengeHost.ACCEPTED}
        expected = [
            {
                "id": self.challenge_host.pk,
                "user": self.challenge_host.user.username,
                "team_name": self.challenge_host.team_name.pk,
                "status": self.challenge_host.status,
                "permissions": self.challenge_host.permissions,
            }
        ]
        response = self.client.get(self.url, self.data)
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_for_challenge_host_does_not_exist(
        self,
    ):
        self.url = reverse_lazy(
            "hosts:get_challenge_host_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk + 1},
        )
        expected = {"error": "ChallengeHostTeam does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class CreateChallengeHostTest(BaseAPITestClass):
    def setUp(self):
        super(CreateChallengeHostTest, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )
        self.data = {
            "status": ChallengeHost.SELF,
            "permissions": ChallengeHost.ADMIN,
        }

    def test_create_challenge_host_team_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_host_team_with_no_data(self):
        del self.data["status"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetParticularChallengeHost(BaseAPITestClass):
    def setUp(self):
        super(GetParticularChallengeHost, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "pk": self.challenge_host.pk,
            },
        )

    def test_get_particular_challenge_host(self):
        expected = {
            "id": self.challenge_host.pk,
            "user": self.challenge_host.user.username,
            "team_name": self.challenge_host.team_name.pk,
            "status": self.challenge_host.status,
            "permissions": self.challenge_host.permissions,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_does_not_exist(self):
        self.inavlid_challenge_pk = self.challenge_host.pk + 1
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "pk": self.inavlid_challenge_pk,
            },
        )
        expected = {
            "detail": "ChallengeHost "
            + str(self.inavlid_challenge_pk)
            + " does not exist"
        }
        response = self.client.get(self.url, {})
        self.assertDictEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_particular_challenge_host_team_for_challenge_host_does_not_exist(
        self,
    ):
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk + 1,
                "pk": self.challenge_host.pk,
            },
        )
        expected = {"error": "ChallengeHostTeam does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class UpdateParticularChallengeHost(BaseAPITestClass):
    def setUp(self):
        super(UpdateParticularChallengeHost, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "pk": self.challenge_host.pk,
            },
        )
        self.data = {
            "status": ChallengeHost.SELF,
            "permissions": ChallengeHost.WRITE,
        }
        self.partial_update_data = {"status": ChallengeHost.DENIED}

    def test_particular_challenge_host_partial_update(self):
        expected = {
            "id": self.challenge_host.pk,
            "user": self.challenge_host.user.username,
            "team_name": self.challenge_host.team_name.pk,
            "status": ChallengeHost.DENIED,
            "permissions": self.challenge_host.permissions,
        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_update(self):
        expected = {
            "id": self.challenge_host.pk,
            "user": self.challenge_host.user.username,
            "team_name": self.challenge_host.team_name.pk,
            "status": ChallengeHost.SELF,
            "permissions": ChallengeHost.WRITE,
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_update_with_no_data(self):
        self.data = {"status": ""}
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteParticularChallengeHost(BaseAPITestClass):
    def setUp(self):
        super(DeleteParticularChallengeHost, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "pk": self.challenge_host.pk,
            },
        )

    def test_particular_challenge_host_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class CreateChallengeHostAndTeam(BaseAPITestClass):

    url = reverse_lazy("hosts:create_challenge_host_team")

    def setUp(self):
        super(CreateChallengeHostAndTeam, self).setUp()
        self.data = {"team_name": "Test Challenge Host and Team"}

    def test_create_challenge_host_and_team_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_host_and_team_with_no_data(self):
        del self.data["team_name"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RemoveChallengeHostFromTeamHimselfTest(BaseAPITestClass):
    def setUp(self):
        super(RemoveChallengeHostFromTeamHimselfTest, self).setUp()

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.url = reverse_lazy(
            "hosts:remove_self_from_challenge_host_team",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )

    def test_when_challenge_host_team_does_not_exist(self):
        self.url = reverse_lazy(
            "hosts:remove_self_from_challenge_host_team",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk + 1},
        )

        expected = {"error": "ChallengeHostTeam does not exist"}

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_a_challenge_host_is_successfully_removed_from_team(self):
        self.url = reverse_lazy(
            "hosts:remove_self_from_challenge_host_team",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class InviteHostToTeamTest(BaseAPITestClass):

    url = reverse_lazy("hosts:invite_host_to_team")

    def setUp(self):
        super(InviteHostToTeamTest, self).setUp()
        self.data = {"email": self.invite_user.email}
        self.url = reverse_lazy(
            "hosts:invite_host_to_team",
            kwargs={"pk": self.challenge_host_team.pk},
        )

    def test_invite_host_to_team_with_all_data(self):
        expected = {
            "message": "User has been added successfully to the host team"
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_invite_host_to_team_with_no_data(self):
        del self.data["email"]
        expected = {"error": "User does not exist with this email address!"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_self_to_team(self):
        self.data = {"email": self.user.email}
        expected = {"error": "User is already part of the team!"}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_user_which_does_not_exist_to_team(self):
        self.data = {"email": "userwhichdoesnotexist@platform.com"}
        expected = {"error": "User does not exist with this email address!"}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_host_team_for_invite_does_not_exist(self):
        self.url = reverse_lazy(
            "hosts:invite_host_to_team",
            kwargs={"pk": self.challenge_host_team.pk + 1},
        )
        expected = {"error": "Host Team does not exist"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_requesting_user_is_not_part_of_team(self):

        # Create a new user and make a request using this user which doesn't
        # belong to any team and still trying to invite other people
        temp_user = User.objects.create(
            username="username", password="password", email="temp@example.com"
        )

        EmailAddress.objects.create(
            user=temp_user,
            email="temp@example.com",
            primary=True,
            verified=True,
        )

        self.client.force_authenticate(user=temp_user)

        self.url = reverse_lazy(
            "hosts:invite_host_to_team",
            kwargs={"pk": self.challenge_host_team.pk},
        )
        expected = {"error": "You are not a member of this team!"}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from hosts.models import ChallengeHost, ChallengeHostTeam , ChallengeHostTeamInvitation
from rest_framework import status
from rest_framework.test import APIClient, APITestCase


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=True
        )

        self.invite_user = User.objects.create(
            username="otheruser",
            email="other@platform.com",
            password="other_secret_password",
        )

        self.challenge_host_team = ChallengeHostTeam.objects.create(
            team_name="Test Challenge Host Team", created_by=self.user
        )

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.client.force_authenticate(user=self.user)


class GetChallengeHostTeamTest(BaseAPITestClass):
    url = reverse_lazy("hosts:get_challenge_host_team_list")

    def setUp(self):
        super(GetChallengeHostTeamTest, self).setUp()
        self.url = reverse_lazy("hosts:get_challenge_host_team_list")

        self.user2 = User.objects.create(
            username="someuser2",
            email="user2@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user2,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.READ,
        )

    def test_get_challenge_host_team(self):
        expected = [
            {
                "id": self.challenge_host_team.pk,
                "team_name": self.challenge_host_team.team_name,
                "created_by": self.challenge_host_team.created_by.username,
                "team_url": self.challenge_host_team.team_url,
                "members": [
                    {
                        "id": self.challenge_host.id,
                        "permissions": self.challenge_host.permissions,
                        "status": self.challenge_host.status,
                        "team_name": self.challenge_host.team_name.id,
                        "user": self.challenge_host.user.username,
                    },
                    {
                        "id": self.challenge_host2.id,
                        "permissions": self.challenge_host2.permissions,
                        "status": self.challenge_host2.status,
                        "team_name": self.challenge_host2.team_name.id,
                        "user": self.challenge_host2.user.username,
                    },
                ],
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class CreateChallengeHostTeamTest(BaseAPITestClass):
    url = reverse_lazy("hosts:get_challenge_host_team_list")

    def setUp(self):
        super(CreateChallengeHostTeamTest, self).setUp()
        self.data = {"team_name": "Test team"}

    def test_create_challenge_host_team_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_host_team_when_team_with_same_name_already_exists(
        self,
    ):

        expected = {
            "team_name": [
                "challenge host team with this team name already exists."
            ]
        }

        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Trying to create a team with the same team name
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, expected)

    def test_create_challenge_host_team_with_no_data(self):
        del self.data["team_name"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetParticularChallengeHostTeam(BaseAPITestClass):
    def setUp(self):
        super(GetParticularChallengeHostTeam, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_team_details",
            kwargs={"pk": self.challenge_host_team.pk},
        )

        self.user2 = User.objects.create(
            username="someuser2",
            email="user2@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user2,
            email="user2@test.com",
            primary=True,
            verified=True,
        )

        self.challenge_host2 = ChallengeHost.objects.create(
            user=self.user2,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.READ,
        )

    def test_get_particular_challenge_host_team(self):
        expected = {
            "id": self.challenge_host_team.pk,
            "team_name": self.challenge_host_team.team_name,
            "created_by": self.user.username,
            "team_url": self.challenge_host_team.team_url,
            "members": [
                {
                    "id": self.challenge_host.id,
                    "permissions": self.challenge_host.permissions,
                    "status": self.challenge_host.status,
                    "team_name": self.challenge_host.team_name.id,
                    "user": self.challenge_host.user.username,
                },
                {
                    "id": self.challenge_host2.id,
                    "permissions": self.challenge_host2.permissions,
                    "status": self.challenge_host2.status,
                    "team_name": self.challenge_host2.team_name.id,
                    "user": self.challenge_host2.user.username,
                },
            ],
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class UpdateParticularChallengeHostTeam(BaseAPITestClass):
    def setUp(self):
        super(UpdateParticularChallengeHostTeam, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_team_details",
            kwargs={"pk": self.challenge_host_team.pk},
        )
        self.data = {"team_name": "Test Team"}
        self.partial_update_team_name = "Partial Update Test Team"
        self.update_team_name = "All Update Test Team"

    def test_particular_challenge_host_team_partial_update(self):
        self.data = {"team_name": self.partial_update_team_name}
        expected = {
            "id": self.challenge_host_team.pk,
            "team_name": self.partial_update_team_name,
            "created_by": self.user.username,
            "team_url": self.challenge_host_team.team_url,
        }
        response = self.client.patch(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_update(self):
        self.data = {"team_name": self.update_team_name}
        expected = {
            "id": self.challenge_host_team.pk,
            "team_name": self.update_team_name,
            "created_by": self.user.username,
            "team_url": self.challenge_host_team.team_url,
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_update_with_no_data(self):
        self.data = {"team_name": ""}
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_particular_challenge_host_team_does_not_exist(self):
        self.url = reverse_lazy(
            "hosts:get_challenge_host_team_details",
            kwargs={"pk": self.challenge_host_team.pk + 1},
        )
        expected = {"error": "ChallengeHostTeam does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class DeleteParticularChallengeHostTeam(BaseAPITestClass):
    def setUp(self):
        super(DeleteParticularChallengeHostTeam, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_team_details",
            kwargs={"pk": self.challenge_host_team.pk},
        )

    # TODO: Add test back with API
    # def test_particular_challenge_host_team_delete(self):
    #     response = self.client.delete(self.url, {})
    #     self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class GetChallengeHostTest(BaseAPITestClass):
    def setUp(self):
        super(GetChallengeHostTest, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )

    def test_get_challenge_team(self):
        expected = [
            {
                "id": self.challenge_host.pk,
                "user": self.challenge_host.user.username,
                "team_name": self.challenge_host.team_name.pk,
                "status": self.challenge_host.status,
                "permissions": self.challenge_host.permissions,
            }
        ]

        response = self.client.get(self.url, {})
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_challenge_team_with_status_as_query_parameter(self):
        self.data = {"status": ChallengeHost.ACCEPTED}
        expected = [
            {
                "id": self.challenge_host.pk,
                "user": self.challenge_host.user.username,
                "team_name": self.challenge_host.team_name.pk,
                "status": self.challenge_host.status,
                "permissions": self.challenge_host.permissions,
            }
        ]
        response = self.client.get(self.url, self.data)
        self.assertEqual(response.data["results"], expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_team_for_challenge_host_does_not_exist(
        self,
    ):
        self.url = reverse_lazy(
            "hosts:get_challenge_host_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk + 1},
        )
        expected = {"error": "ChallengeHostTeam does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class CreateChallengeHostTest(BaseAPITestClass):
    def setUp(self):
        super(CreateChallengeHostTest, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_list",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )
        self.data = {
            "status": ChallengeHost.SELF,
            "permissions": ChallengeHost.ADMIN,
        }

    def test_create_challenge_host_team_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_host_team_with_no_data(self):
        del self.data["status"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GetParticularChallengeHost(BaseAPITestClass):
    def setUp(self):
        super(GetParticularChallengeHost, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "pk": self.challenge_host.pk,
            },
        )

    def test_get_particular_challenge_host(self):
        expected = {
            "id": self.challenge_host.pk,
            "user": self.challenge_host.user.username,
            "team_name": self.challenge_host.team_name.pk,
            "status": self.challenge_host.status,
            "permissions": self.challenge_host.permissions,
        }
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_does_not_exist(self):
        self.inavlid_challenge_pk = self.challenge_host.pk + 1
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "pk": self.inavlid_challenge_pk,
            },
        )
        expected = {
            "detail": "ChallengeHost "
            + str(self.inavlid_challenge_pk)
            + " does not exist"
        }
        response = self.client.get(self.url, {})
        self.assertDictEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_particular_challenge_host_team_for_challenge_host_does_not_exist(
        self,
    ):
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk + 1,
                "pk": self.challenge_host.pk,
            },
        )
        expected = {"error": "ChallengeHostTeam does not exist"}
        response = self.client.get(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)


class UpdateParticularChallengeHost(BaseAPITestClass):
    def setUp(self):
        super(UpdateParticularChallengeHost, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "pk": self.challenge_host.pk,
            },
        )
        self.data = {
            "status": ChallengeHost.SELF,
            "permissions": ChallengeHost.WRITE,
        }
        self.partial_update_data = {"status": ChallengeHost.DENIED}

    def test_particular_challenge_host_partial_update(self):
        expected = {
            "id": self.challenge_host.pk,
            "user": self.challenge_host.user.username,
            "team_name": self.challenge_host.team_name.pk,
            "status": ChallengeHost.DENIED,
            "permissions": self.challenge_host.permissions,
        }
        response = self.client.patch(self.url, self.partial_update_data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_update(self):
        expected = {
            "id": self.challenge_host.pk,
            "user": self.challenge_host.user.username,
            "team_name": self.challenge_host.team_name.pk,
            "status": ChallengeHost.SELF,
            "permissions": ChallengeHost.WRITE,
        }
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_particular_challenge_host_update_with_no_data(self):
        self.data = {"status": ""}
        response = self.client.put(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DeleteParticularChallengeHost(BaseAPITestClass):
    def setUp(self):
        super(DeleteParticularChallengeHost, self).setUp()
        self.url = reverse_lazy(
            "hosts:get_challenge_host_details",
            kwargs={
                "challenge_host_team_pk": self.challenge_host_team.pk,
                "pk": self.challenge_host.pk,
            },
        )

    def test_particular_challenge_host_delete(self):
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class CreateChallengeHostAndTeam(BaseAPITestClass):

    url = reverse_lazy("hosts:create_challenge_host_team")

    def setUp(self):
        super(CreateChallengeHostAndTeam, self).setUp()
        self.data = {"team_name": "Test Challenge Host and Team"}

    def test_create_challenge_host_and_team_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_challenge_host_and_team_with_no_data(self):
        del self.data["team_name"]
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class RemoveChallengeHostFromTeamHimselfTest(BaseAPITestClass):
    def setUp(self):
        super(RemoveChallengeHostFromTeamHimselfTest, self).setUp()

        self.challenge_host = ChallengeHost.objects.create(
            user=self.user,
            team_name=self.challenge_host_team,
            status=ChallengeHost.ACCEPTED,
            permissions=ChallengeHost.ADMIN,
        )

        self.url = reverse_lazy(
            "hosts:remove_self_from_challenge_host_team",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )

    def test_when_challenge_host_team_does_not_exist(self):
        self.url = reverse_lazy(
            "hosts:remove_self_from_challenge_host_team",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk + 1},
        )

        expected = {"error": "ChallengeHostTeam does not exist"}

        response = self.client.delete(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_a_challenge_host_is_successfully_removed_from_team(self):
        self.url = reverse_lazy(
            "hosts:remove_self_from_challenge_host_team",
            kwargs={"challenge_host_team_pk": self.challenge_host_team.pk},
        )
        response = self.client.delete(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


class InviteHostToTeamTest(BaseAPITestClass):

    url = reverse_lazy("hosts:invite_host_to_team")

    def setUp(self):
        super(InviteHostToTeamTest, self).setUp()
        self.data = {"email": self.invite_user.email}
        self.url = reverse_lazy(
            "hosts:invite_host_to_team",
            kwargs={"pk": self.challenge_host_team.pk},
        )

    def test_invite_host_to_team_with_all_data(self):
        expected = {
            "message": "User has been added successfully to the host team"
        }
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)

    def test_invite_host_to_team_with_no_data(self):
        del self.data["email"]
        expected = {"error": "User does not exist with this email address!"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_self_to_team(self):
        self.data = {"email": self.user.email}
        expected = {"error": "User is already part of the team!"}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_invite_user_which_does_not_exist_to_team(self):
        self.data = {"email": "userwhichdoesnotexist@platform.com"}
        expected = {"error": "User does not exist with this email address!"}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_particular_challenge_host_team_for_invite_does_not_exist(self):
        self.url = reverse_lazy(
            "hosts:invite_host_to_team",
            kwargs={"pk": self.challenge_host_team.pk + 1},
        )
        expected = {"error": "Host Team does not exist"}
        response = self.client.post(self.url, {})
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)

    def test_when_requesting_user_is_not_part_of_team(self):
        temp_user = User.objects.create(
            username="username", password="password", email="temp@example.com"
        )

        EmailAddress.objects.create(
            user=temp_user,
            email="temp@example.com",
            primary=True,
            verified=True,
        )

        self.client.force_authenticate(user=temp_user)

        self.url = reverse_lazy(
            "hosts:invite_host_to_team",
            kwargs={"pk": self.challenge_host_team.pk},
        )
        expected = {"error": "You are not a member of this team!"}
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

class InviteUserToTeamTest(BaseAPITestClass):
    def setUp(self):
        super(InviteUserToTeamTest, self).setUp()
        self.url = reverse_lazy("hosts:invite_user_to_team")
        self.data = {
            "email": self.invite_user.email,
            "team_id": self.challenge_host_team.id
        }

    def test_invite_user_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        expected_message = f"Invitation sent to {self.invite_user.email}"
        self.assertEqual(response.data["message"], expected_message)
        self.assertIn("invitation", response.data)

    def test_invite_user_with_missing_email(self):
        data = {"team_id": self.challenge_host_team.id}
        response = self.client.post(self.url, data)
        expected = {"error": "Email and team_id are required fields"}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_user_with_missing_team_id(self):
        data = {"email": self.invite_user.email}
        response = self.client.post(self.url, data)
        expected = {"error": "Email and team_id are required fields"}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_user_with_invalid_team(self):
        data = {
            "email": self.invite_user.email,
            "team_id": self.challenge_host_team.id + 100  # Non-existent ID
        }
        response = self.client.post(self.url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invite_unregistered_user(self):
        data = {
            "email": "unregistered@example.com",
            "team_id": self.challenge_host_team.id
        }
        response = self.client.post(self.url, data)
        expected = {"error": "User with this email is not registered on EvalAI"}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invite_existing_team_member(self):
        data = {
            "email": self.user.email,
            "team_id": self.challenge_host_team.id
        }
        response = self.client.post(self.url, data)
        expected = {"error": f"{self.user.email} is already a member of this team"}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_resend_invitation(self):
        first_response = self.client.post(self.url, self.data)
        self.assertEqual(first_response.status_code, status.HTTP_201_CREATED)
        
        second_response = self.client.post(self.url, self.data)
        self.assertEqual(second_response.status_code, status.HTTP_201_CREATED)
        expected_message = f"Invitation sent to {self.invite_user.email}"
        self.assertEqual(second_response.data["message"], expected_message)
        
        # Check if both invitations use the same invitation_key
        self.assertEqual(
            first_response.data["invitation"]["invitation_key"],
            second_response.data["invitation"]["invitation_key"]
        )

class AcceptHostInvitationTest(BaseAPITestClass):
    def setUp(self):
        super(AcceptHostInvitationTest, self).setUp()
        
        self.invitation = ChallengeHostTeamInvitation.objects.create(
            email=self.invite_user.email,
            team=self.challenge_host_team,
            invited_by=self.user,
            status="pending"
        )
        
        from datetime import timedelta
        from django.utils import timezone
        
        self.expired_invitation = ChallengeHostTeamInvitation.objects.create(
            email=self.invite_user.email,
            team=self.challenge_host_team,
            invited_by=self.user,
            status="pending"
        )
        expiry_days = self.expired_invitation.INVITATION_EXPIRY_DAYS
        self.expired_invitation.created_at = timezone.now() - timedelta(days=expiry_days + 1)
        self.expired_invitation.save()
        
        self.accepted_invitation = ChallengeHostTeamInvitation.objects.create(
            email=self.invite_user.email,
            team=self.challenge_host_team,
            invited_by=self.user,
            status="accepted"
        )
        
    def test_get_invitation_details(self):
        url = reverse_lazy(
            "hosts:accept_host_invitation",
            kwargs={"invitation_key": self.invitation.invitation_key}
        )
        
        self.client.force_authenticate(user=self.invite_user)
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], self.invitation.email)
        self.assertEqual(response.data["team"], self.invitation.team.id)
        
    def test_accept_invitation(self):
        url = reverse_lazy(
            "hosts:accept_host_invitation",
            kwargs={"invitation_key": self.invitation.invitation_key}
        )
        self.client.force_authenticate(user=self.invite_user)
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        expected_message = f"You have successfully joined {self.challenge_host_team.team_name}"
        self.assertEqual(response.data["message"], expected_message)
        self.assertIn("invitation", response.data)
        
        invitation = ChallengeHostTeamInvitation.objects.get(pk=self.invitation.pk)
        self.assertEqual(invitation.status, "accepted")
        
        challenge_host = ChallengeHost.objects.get(
            user=self.invite_user,
            team_name=self.challenge_host_team
        )
        self.assertEqual(challenge_host.status, ChallengeHost.ACCEPTED)
        self.assertEqual(challenge_host.permissions, ChallengeHost.ADMIN)
        
    def test_invalid_invitation_key(self):
        url = reverse_lazy(
            "hosts:accept_host_invitation",
            kwargs={"invitation_key": "invalid-key"}
        )
        
        # Authenticate as the invited user
        self.client.force_authenticate(user=self.invite_user)
        
        response = self.client.get(url)
        expected = {"error": "Invalid invitation key"}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
    def test_expired_invitation(self):
        url = reverse_lazy(
            "hosts:accept_host_invitation",
            kwargs={"invitation_key": self.expired_invitation.invitation_key}
        )
        
        self.client.force_authenticate(user=self.invite_user)
        
        response = self.client.get(url)
        expected = {"error": "This invitation has expired. Please request a new invitation."}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_410_GONE)
        
        invitation = ChallengeHostTeamInvitation.objects.get(pk=self.expired_invitation.pk)
        self.assertEqual(invitation.status, "expired")
        
    def test_already_used_invitation(self):
        url = reverse_lazy(
            "hosts:accept_host_invitation",
            kwargs={"invitation_key": self.accepted_invitation.invitation_key}
        )
        
        self.client.force_authenticate(user=self.invite_user)
        
        response = self.client.get(url)
        expected = {"error": "This invitation has already been used or expired"}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
    def test_email_mismatch(self):
        url = reverse_lazy(
            "hosts:accept_host_invitation",
            kwargs={"invitation_key": self.invitation.invitation_key}
        )
        
        self.client.force_authenticate(user=self.user)
        
        response = self.client.get(url)
        expected = {"error": "This invitation was sent to a different email address"}
        self.assertEqual(response.data, expected)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
