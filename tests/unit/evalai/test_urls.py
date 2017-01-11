from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

from rest_framework.test import APITestCase, APIClient

from django.contrib.auth.models import User


class BaseAPITestClass(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            email="user@test.com",
            password='secret_password'
            )

        self.client.force_authenticate(user=self.user)


class TestChallengeUrls(BaseAPITestClass):

    def test_challenges_urls(self):
        url = reverse_lazy('obtain_expiring_auth_token')
        self.assertEqual(url, '/api/auth/login')

        url = reverse_lazy('account_confirm_email', kwargs={'key': 1111})
        self.assertEqual(url, '/api/auth/registration/account-confirm-email/1111/')

        url = reverse_lazy('password_reset_confirm', kwargs={'uidb64': urlsafe_base64_encode(force_bytes(self.user.pk)), 'token': default_token_generator.make_token(self.user), })
        self.assertEqual(url, '/api/password/reset/confirm/'+ str(urlsafe_base64_encode(force_bytes(self.user.pk))) + "/" + str(default_token_generator.make_token(self.user)) + '/')




