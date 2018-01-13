import os

from django.core.urlresolvers import reverse_lazy

from django.contrib.auth.models import User
from django.core import mail
from django.utils.encoding import force_text

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
        response = self.client.put(os.path.join('api', 'auth', self.url), self.data)
        self.assertNotContains(response, 'anotheruser')
        self.assertContains(response, 'someuser')
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class TestPassReset(BaseAPITestClass):

    def _generate_uid_and_token(self, user):
        result = {}
        from django.utils.encoding import force_bytes
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode

        result['uid'] = urlsafe_base64_encode(force_bytes(user.pk))
        result['token'] = default_token_generator.make_token(user)
        return result

    def test_pass_reset(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create(
            username='someother',
            email="user@test.com",
            password='secret_password')
        url_kwargs = self._generate_uid_and_token(self.user)
        self.url = reverse_lazy('accounts:token_verify')
        response = self.client.post(self.url, {'uid': url_kwargs['uid'], 'token': url_kwargs['token']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(self.url, {'uid': url_kwargs['uid'], 'token': 'abcd'})
        self.assertNotEqual(response.status_code, status.HTTP_200_OK)

    def test_check_pass(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.url = reverse_lazy('rest_password_reset_confirm')
        self.data = {
            'new_password1': 'somepassword',
            'new_password2': 'somepassword',
            'uid': 'abc',
            'token': 'sometoken',
            'host': 'example.com',
        }
        response = self.client.post(self.url, self.data)
        self.user = User.objects.create(
            username='someother',
            email="user@test.com",
            password='secret_password')

        mail_count = len(mail.outbox)
        url_kwargs = self._generate_uid_and_token(self.user)
        data = {
            'new_password1': 'newpassword',
            'new_password2': 'newpassword',
            'uid': force_text(url_kwargs['uid']),
            'token': url_kwargs['token'],
            'host': 'localhost'
        }
        response = self.client.post(self.url, data=data, status_code=200)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(mail.outbox), mail_count + 1)
