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
