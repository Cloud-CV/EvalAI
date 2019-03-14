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
            verified=False)

        self.client.force_authenticate(user=self.user)


class ResendEmailThrottleTest(BaseAPITestClass):

    url = reverse_lazy('accounts:resend_email')

    def test_resend_throttles(self):
        for _ in range(3):
            response = self.client.post(self.url, {})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
