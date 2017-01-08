from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
import unittest


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
        self.assertEqual(url, '/accounts/user/disable/')

    if __name__ == '__main__':
        unittest.main()
