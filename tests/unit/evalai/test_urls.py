from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from rest_framework.test import APITestCase, APIClient


class BaseAPITestClass(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username='someuser',
            email="user@test.com",
            password='secret_password'
            )

        self.client.force_authenticate(user=self.user)


class TestEvalAiUrls(BaseAPITestClass):

    def test_evalai_urls(self):
        url = reverse_lazy('obtain_expiring_auth_token')
        self.assertEqual(url, '/api/auth/login')

        url = reverse_lazy('account_confirm_email', kwargs={'key': 1111})
        self.assertEqual(url, '/api/auth/registration/account-confirm-email/1111/')

        url = reverse_lazy('password_reset_confirm',
                           kwargs={'uidb64': urlsafe_base64_encode(force_bytes(self.user.pk)),
                                   'token': default_token_generator.make_token(self.user)})
        self.assertEqual(url, '/auth/api/password/reset/confirm/' +
                         urlsafe_base64_encode(force_bytes(self.user.pk)).decode() + '/' +
                         str(default_token_generator.make_token(self.user)))
