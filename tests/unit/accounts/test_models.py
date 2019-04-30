from django.contrib.auth.models import User
from django.test import TestCase

from accounts.models import Profile, UserStatus


class BaseTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create(
            username="user", email="user@test.com", password="password"
        )


class UserStatusTestCase(BaseTestCase):
    def setUp(self):
        super(UserStatusTestCase, self).setUp()
        self.user_status = UserStatus.objects.create(
            name="user", status=UserStatus.UNKNOWN
        )

    def test__str__(self):
        self.assertEqual(self.user_status.name, self.user_status.__str__())


class ProfileTestCase(BaseTestCase):
    def setUp(self):
        super(ProfileTestCase, self).setUp()
        self.profile = Profile.objects.get(user=self.user)

    def test__str__(self):
        self.assertEqual(
            "{}".format(self.profile.user), self.profile.__str__()
        )
