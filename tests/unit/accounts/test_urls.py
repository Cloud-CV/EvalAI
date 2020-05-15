from allauth.account.models import EmailAddress

from django.urls import reverse_lazy
from django.contrib.auth.models import User

from rest_framework.test import APITestCase, APIClient


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

        self.client.force_authenticate(user=self.user)


class TestStringMethods(BaseAPITestClass):
    def test_disable_user(self):
        url = reverse_lazy("accounts:disable_user")
        self.assertEqual(str(url), "/api/accounts/user/disable")

        url = reverse_lazy("accounts:get_auth_token")
        self.assertEqual(str(url), "/api/accounts/user/get_auth_token")

    def test_resend_email_verification(self):
        url = reverse_lazy("accounts:resend_email_confirmation")
        self.assertEqual(str(url), "/api/accounts/user/resend_email_verification/")
