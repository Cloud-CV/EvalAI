from accounts.admin import JwtTokenAdmin, _get_outstanding_token_for_jwt
from accounts.models import JwtToken
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse_lazy
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.token_blacklist.models import (
    BlacklistedToken,
    OutstandingToken,
)


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)
        self.user = User.objects.create(
            username="user",
            email="user@test.com",
            password="password",
        )
        self.client.force_authenticate(user=self.user)


class JwtTokenAdminTest(BaseAPITestClass):
    def setUp(self):
        super().setUp()
        self.admin = JwtTokenAdmin(JwtToken, AdminSite())
        self.get_auth_token_url = reverse_lazy("accounts:get_auth_token")

    def test_get_outstanding_token_matches_refresh_token(self):
        response = self.client.get(self.get_auth_token_url, {})
        self.assertEqual(response.status_code, 200)

        jwt_token = JwtToken.objects.get(user=self.user)
        outstanding_token = _get_outstanding_token_for_jwt(jwt_token)

        self.assertIsNotNone(outstanding_token)
        self.assertEqual(outstanding_token.token, jwt_token.refresh_token)
        self.assertEqual(
            outstanding_token.expires_at, response.data["expires_at"]
        )

    def test_admin_displays_jwt_metadata(self):
        response = self.client.get(self.get_auth_token_url, {})
        self.assertEqual(response.status_code, 200)

        jwt_token = JwtToken.objects.get(user=self.user)
        outstanding_token = OutstandingToken.objects.filter(
            user=self.user
        ).latest("created_at")

        self.assertEqual(
            self.admin.jwt_issued_at(jwt_token), outstanding_token.created_at
        )
        self.assertEqual(
            self.admin.jwt_expires_at(jwt_token), outstanding_token.expires_at
        )
        self.assertFalse(self.admin.is_blacklisted(jwt_token))

    def test_admin_marks_blacklisted_refresh_token(self):
        self.client.get(self.get_auth_token_url, {})
        jwt_token = JwtToken.objects.get(user=self.user)
        outstanding_token = OutstandingToken.objects.get(
            token=jwt_token.refresh_token
        )

        BlacklistedToken.objects.create(token=outstanding_token)

        self.assertTrue(self.admin.is_blacklisted(jwt_token))

    def test_admin_returns_dash_when_no_outstanding_token(self):
        jwt_token = JwtToken.objects.create(
            user=self.user,
            access_token="access",
            refresh_token="refresh",
        )

        self.assertEqual(self.admin.jwt_issued_at(jwt_token), "-")
        self.assertEqual(self.admin.jwt_expires_at(jwt_token), "-")
        self.assertIsNone(self.admin.is_blacklisted(jwt_token))


class JwtTokenAdminRegistrationTest(TestCase):
    def test_jwt_token_admin_list_display_includes_expiry_fields(self):
        list_display = JwtTokenAdmin(JwtToken, AdminSite()).list_display

        self.assertIn("created_at", list_display)
        self.assertIn("modified_at", list_display)
        self.assertIn("jwt_issued_at", list_display)
        self.assertIn("jwt_expires_at", list_display)
        self.assertIn("is_blacklisted", list_display)
