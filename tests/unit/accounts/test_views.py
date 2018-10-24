import os

from rest_framework.authtoken.models import Token

from django.core.urlresolvers import reverse_lazy
from django.contrib.auth.models import User

from allauth.account.models import EmailAddress
from rest_framework import status
from rest_framework.test import APITestCase, APIClient


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

        self.client.force_authenticate(user=self.user)


class DisableUserTest(BaseAPITestClass):

    url = reverse_lazy('accounts:disable_user')

    def test_disable_user(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestUpdateUser(BaseAPITestClass):

    def test_cannot_update_username(self):
        self.url = reverse_lazy('rest_user_details')
        self.data = {
            'username': 'anotheruser',
            'affiliation': 'some_affiliation',
        }
        response = self.client.put(os.path.join('api', 'auth', str(self.url)), self.data)
        self.assertNotContains(response, 'anotheruser')
        self.assertContains(response, 'someuser')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GetAuthTokenTest(BaseAPITestClass):

    url = reverse_lazy('accounts:get_auth_token')

    def test_get_auth_token(self):
        response = self.client.get(self.url, {})
        token = Token.objects.get(user=self.user)
        expected_data = {"token": "{}".format(token)}
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)
