from accounts.models import JwtToken, Profile, UserStatus
from django.contrib.auth.models import User
from django.test import TestCase


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

    def test_is_complete_when_profile_is_incomplete(self):
        """Test that is_complete returns False when required fields are missing."""
        # Profile starts empty
        self.assertFalse(self.profile.is_complete)

    def test_is_complete_when_user_name_is_missing(self):
        """Test that is_complete returns False when user name is missing."""
        self.profile.address_street = "123 Main St"
        self.profile.address_city = "Springfield"
        self.profile.address_state = "IL"
        self.profile.address_country = "USA"
        self.profile.university = "Test University"
        self.profile.save()
        # User first_name and last_name not set
        self.assertFalse(self.profile.is_complete)

    def test_is_complete_when_address_is_missing(self):
        """Test that is_complete returns False when address fields are missing."""
        self.user.first_name = "John"
        self.user.last_name = "Doe"
        self.user.save()
        # Address fields not set
        self.assertFalse(self.profile.is_complete)

    def test_is_complete_when_profile_is_complete(self):
        """Test that is_complete returns True when all required fields are filled."""
        self.user.first_name = "John"
        self.user.last_name = "Doe"
        self.user.save()
        self.profile.address_street = "123 Main St"
        self.profile.address_city = "Springfield"
        self.profile.address_state = "IL"
        self.profile.address_country = "USA"
        self.profile.university = "Test University"
        self.profile.save()
        self.assertTrue(self.profile.is_complete)

    def test_is_complete_with_whitespace_only_values(self):
        """Test that is_complete returns False when fields contain only whitespace."""
        self.user.first_name = "John"
        self.user.last_name = "   "  # whitespace only
        self.user.save()
        self.profile.address_street = "123 Main St"
        self.profile.address_city = "Springfield"
        self.profile.address_state = "IL"
        self.profile.address_country = "USA"
        self.profile.university = "Test University"
        self.profile.save()
        self.assertFalse(self.profile.is_complete)

    def test_is_complete_when_university_is_missing(self):
        """Test that is_complete returns False when university is missing."""
        self.user.first_name = "John"
        self.user.last_name = "Doe"
        self.user.save()
        self.profile.address_street = "123 Main St"
        self.profile.address_city = "Springfield"
        self.profile.address_state = "IL"
        self.profile.address_country = "USA"
        # university not set
        self.profile.save()
        self.assertFalse(self.profile.is_complete)

    def test_get_full_name(self):
        """Test the get_full_name method."""
        self.user.first_name = "John"
        self.user.last_name = "Doe"
        self.user.save()
        self.assertEqual(self.profile.get_full_name(), "John Doe")

    def test_get_full_name_with_only_first_name(self):
        """Test get_full_name when only first name is set."""
        self.user.first_name = "John"
        self.user.last_name = ""
        self.user.save()
        self.assertEqual(self.profile.get_full_name(), "John")


class JwtTokenTestCase(BaseTestCase):
    def setUp(self):
        super(JwtTokenTestCase, self).setUp()
        self.jwt_token = JwtToken.objects.create(user=self.user)

    def test__str__(self):
        self.assertEqual(
            "{}".format(self.jwt_token.user), self.jwt_token.__str__()
        )
