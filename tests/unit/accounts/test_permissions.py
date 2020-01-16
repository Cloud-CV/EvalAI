from unittest import TestCase
from apps.accounts.permissions import HasVerifiedEmail


class PermissionTest(TestCase):
  def test_is_user_annoymous(self):
    is_anonymous = True
    self.assertEqual(HasVerifiedEmail.has_permission(), True)
