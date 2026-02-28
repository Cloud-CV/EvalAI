import os
from unittest.mock import MagicMock, patch

from accounts.models import JwtToken
from allauth.account.models import EmailAddress
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken


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


class DisableUserTest(BaseAPITestClass):

    url = reverse_lazy("accounts:disable_user")

    def test_disable_user(self):
        response = self.client.post(self.url, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)


# need to add form for image later
class TestUpdateUser(BaseAPITestClass):
    def test_cannot_update_username(self):
        self.url = reverse_lazy("rest_user_details")
        self.data = {
            "username": "anotheruser",
            "affiliation": "some_affiliation",
            "github_url": "https://github.url",
            "google_scholar_url": "https://google-scholar.url",
            "linkedin_url": "https://linkedin.url",
            "password": "secret_password",
        }
        response = self.client.put(
            os.path.join("api", "auth", str(self.url)), self.data
        )
        self.assertNotContains(response, "anotheruser")
        self.assertContains(response, "someuser")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class GetAuthTokenTest(BaseAPITestClass):

    url = reverse_lazy("accounts:get_auth_token")

    def test_get_auth_token(self):
        response = self.client.get(self.url, {})
        token = JwtToken.objects.get(user=self.user)
        outstanding_token = OutstandingToken.objects.filter(
            user=self.user
        ).order_by("-created_at")[0]
        expected_data = {
            "token": "{}".format(token.refresh_token),
            "expires_at": outstanding_token.expires_at,
        }
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)


class ResendEmailVerificationTestClass(APITestCase):
    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.user = User.objects.create(
            username="someuser",
            email="user@test.com",
            password="secret_password",
        )

        EmailAddress.objects.create(
            user=self.user, email="user@test.com", primary=True, verified=False
        )

        self.client.force_authenticate(user=self.user)

        self.url = reverse_lazy("accounts:resend_email_confirmation")

    def test_resend_throttles(self):
        # Running 3 iterations because the throttle rate is 3/hour. The very
        # next request will be throttled.
        for _ in range(3):
            response = self.client.post(self.url, {})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.post(self.url, {})
        self.assertEqual(
            response.status_code, status.HTTP_429_TOO_MANY_REQUESTS
        )


class UpdateEmailTest(BaseAPITestClass):

    url = reverse_lazy("accounts:update_email")

    @patch("accounts.views.send_email_confirmation")
    @patch("accounts.adapter.dns.resolver.resolve")
    def test_update_email_success(self, mock_resolve, mock_send_conf):
        mock_resolve.return_value = [MagicMock()]
        response = self.client.post(
            self.url, {"email": "new@valid-domain.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("confirmation email", response.data["message"])
        self.assertTrue(
            EmailAddress.objects.filter(
                user=self.user, email="new@valid-domain.com", verified=False
            ).exists()
        )
        mock_send_conf.assert_called_once()

    @patch("accounts.views.send_email_confirmation")
    @patch("accounts.adapter.dns.resolver.resolve")
    def test_update_email_invalid_mx(self, mock_resolve, mock_send_conf):
        import dns.resolver as _dns_resolver

        mock_resolve.side_effect = _dns_resolver.NXDOMAIN()
        response = self.client.post(
            self.url, {"email": "user@bad-domain.xyz"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        mock_send_conf.assert_not_called()

    def test_update_email_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(
            self.url, {"email": "new@test.com"}, format="json"
        )
        self.assertIn(
            response.status_code,
            [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN],
        )

    @patch("accounts.views.send_email_confirmation")
    def test_update_email_same_as_current(self, mock_send_conf):
        response = self.client.post(
            self.url, {"email": "user@test.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already your current", response.data["error"])
        mock_send_conf.assert_not_called()

    def test_update_email_empty_fails(self):
        response = self.client.post(self.url, {"email": ""}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Email is required", response.data["error"])

    @patch("accounts.views.send_email_confirmation")
    @patch("accounts.adapter.dns.resolver.resolve")
    def test_update_email_already_used_by_other_user(
        self, mock_resolve, mock_send_conf
    ):
        mock_resolve.return_value = [MagicMock()]
        User.objects.create(
            username="otheruser",
            email="other@valid-domain.com",
            password="password",
        )
        response = self.client.post(
            self.url, {"email": "other@valid-domain.com"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("already in use", response.data["error"])
        mock_send_conf.assert_not_called()

    @patch("accounts.adapter.dns.resolver.resolve")
    def test_email_bounced_flag_cleared_on_confirmation(self, mock_resolve):
        mock_resolve.return_value = [MagicMock()]
        self.user.profile.email_bounced = True
        self.user.profile.save()

        from accounts.adapter import EvalAIAccountAdapter

        adapter = EvalAIAccountAdapter()
        new_email_obj = EmailAddress.objects.create(
            user=self.user,
            email="confirmed@test.com",
            primary=False,
            verified=False,
        )
        new_email_obj.verified = True
        new_email_obj.save()
        adapter.confirm_email(request=None, email_address=new_email_obj)

        self.user.profile.refresh_from_db()
        self.assertFalse(self.user.profile.email_bounced)
        self.assertIsNone(self.user.profile.email_bounced_at)


class RefreshAuthTokenTest(BaseAPITestClass):

    url = reverse_lazy("accounts:refresh_auth_token")

    def test_refresh_auth_token(self):
        url = reverse_lazy("accounts:get_auth_token")
        response = self.client.get(url, {})
        token = JwtToken.objects.get(user=self.user)
        outstanding_token = OutstandingToken.objects.filter(
            user=self.user
        ).order_by("-created_at")[0]
        expected_data = {
            "token": "{}".format(token.refresh_token),
            "expires_at": outstanding_token.expires_at,
        }

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, expected_data)

        response = self.client.get(self.url, {})
        with self.assertRaises(TokenError) as context:
            RefreshToken(token.refresh_token)
        self.assertTrue("Token is blacklisted" in str(context.exception))
