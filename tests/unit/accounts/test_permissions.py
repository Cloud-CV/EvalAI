from accounts.models import User
from accounts.permissions import HasVerifiedEmail
from allauth.account.models import EmailAddress
from django.test import TestCase


class TestHasVerifiedEmailPermission(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="password123",
        )
        self.unverified_email = EmailAddress.objects.create(
            user=self.user, email="test@example.com", verified=False
        )

    def test_has_permission_with_no_verified_email(self):
        permission = HasVerifiedEmail()
        request = self.client.get("/")
        request.user = self.user
        EmailAddress.objects.all().delete()
        self.assertFalse(permission.has_permission(request, None))
