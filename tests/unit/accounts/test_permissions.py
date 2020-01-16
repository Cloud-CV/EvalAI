from unittest import TestCase
from apps.accounts.permissions import HasVerifiedEmail
from unittest.mock import patch


class PermissionTest(TestCase):
  def test_is_user_annoymous(self, request):
    request.user.is_anonymous = True
    self.assertEqual(HasVerifiedEmail.has_permission(), True)
