from allauth.account.models import EmailAddress

from django.urls import reverse_lazy
from django.contrib.auth.models import User

from rest_framework.test import APITestCase, APIClient
from rest_framework import status


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


class TestStringMethods(BaseAPITestClass):

    def test_disable_user(self):
        url = reverse_lazy('accounts:disable_user')
        self.assertEqual(unicode(url), '/api/accounts/user/disable')
