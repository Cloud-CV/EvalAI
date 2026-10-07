from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_expiring_authtoken.models import ExpiringToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import JwtToken
from accounts.token_revocation import revoke_all_user_tokens


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


class RevokeAllUserTokensTest(BaseAPITestClass):
    def test_revoke_all_user_tokens_deletes_api_token(self):
        api_token = ExpiringToken.objects.create(user=self.user)

        revoke_all_user_tokens(self.user)

        self.assertFalse(ExpiringToken.objects.filter(pk=api_token.pk).exists())

    def test_revoke_all_user_tokens_blacklists_jwt_and_deletes_record(self):
        refresh = RefreshToken.for_user(self.user)
        jwt_token = JwtToken.objects.create(
            user=self.user,
            refresh_token=str(refresh),
            access_token=str(refresh.access_token),
        )
        outstanding_token = OutstandingToken.objects.filter(user=self.user).latest(
            "created_at"
        )

        revoke_all_user_tokens(self.user)

        self.assertFalse(JwtToken.objects.filter(pk=jwt_token.pk).exists())
        self.assertTrue(
            BlacklistedToken.objects.filter(token=outstanding_token).exists()
        )
        with self.assertRaises(TokenError):
            RefreshToken(str(refresh))


class PasswordChangeTokenRevocationTest(BaseAPITestClass):
    url = reverse_lazy("rest_password_change")

    def setUp(self):
        super().setUp()
        self.api_token = ExpiringToken.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION="Token {}".format(self.api_token.key))

    def test_password_change_revokes_existing_api_token(self):
        response = self.client.post(
            "/api/auth/password/change/",
            {
                "old_password": "secret_password",
                "new_password1": "new_secret_password",
                "new_password2": "new_secret_password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            ExpiringToken.objects.filter(pk=self.api_token.pk).exists()
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new_secret_password"))

    def test_password_change_revokes_jwt_credentials(self):
        refresh = RefreshToken.for_user(self.user)
        JwtToken.objects.create(
            user=self.user,
            refresh_token=str(refresh),
            access_token=str(refresh.access_token),
        )
        outstanding_token = OutstandingToken.objects.filter(user=self.user).latest(
            "created_at"
        )

        response = self.client.post(
            "/api/auth/password/change/",
            {
                "old_password": "secret_password",
                "new_password1": "new_secret_password",
                "new_password2": "new_secret_password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(JwtToken.objects.filter(user=self.user).exists())
        self.assertTrue(
            BlacklistedToken.objects.filter(token=outstanding_token).exists()
        )


class PasswordResetConfirmTokenRevocationTest(BaseAPITestClass):
    url = reverse_lazy("rest_password_reset_confirm")

    def setUp(self):
        super().setUp()
        self.api_token = ExpiringToken.objects.create(user=self.user)
        self.uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        self.token = default_token_generator.make_token(self.user)

    def test_password_reset_confirm_revokes_existing_credentials(self):
        refresh = RefreshToken.for_user(self.user)
        JwtToken.objects.create(
            user=self.user,
            refresh_token=str(refresh),
            access_token=str(refresh.access_token),
        )
        outstanding_token = OutstandingToken.objects.filter(user=self.user).latest(
            "created_at"
        )

        response = self.client.post(
            "/api/auth/password/reset/confirm/",
            {
                "uid": self.uid,
                "token": self.token,
                "new_password1": "reset_secret_password",
                "new_password2": "reset_secret_password",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(
            ExpiringToken.objects.filter(pk=self.api_token.pk).exists()
        )
        self.assertFalse(JwtToken.objects.filter(user=self.user).exists())
        self.assertTrue(
            BlacklistedToken.objects.filter(token=outstanding_token).exists()
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("reset_secret_password"))
