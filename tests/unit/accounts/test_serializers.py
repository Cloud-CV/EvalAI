from accounts.serializers import (
    CustomPasswordResetSerializer,
    ProfileSerializer,
)
from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.exceptions import ValidationError


class TestCustomPasswordResetSerializer(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.active_user = self.user_model.objects.create_user(
            username="active_user",
            email="active@example.com",
            password="password",
        )
        self.inactive_user = self.user_model.objects.create_user(
            username="inactive_user",
            email="inactive@example.com",
            password="password",
        )
        self.inactive_user.is_active = False
        self.inactive_user.save()

    def test_get_email_options_try_block(self):
        serializer = CustomPasswordResetSerializer(
            data={"email": self.active_user.email}
        )
        self.assertEqual(serializer.is_valid(), True)
        expected_email_options = super(
            CustomPasswordResetSerializer, serializer
        ).get_email_options()
        self.assertEqual(
            serializer.get_email_options(), expected_email_options
        )

    def test_get_email_options_except_block(self):
        serializer = CustomPasswordResetSerializer(
            data={"email": "nonexistent@example.com"}
        )
        serializer.is_valid()  # Ensure data is validated
        with self.assertRaises(ValidationError) as e:
            serializer.get_email_options()
        self.assertEqual(
            e.exception.detail,
            {"details": "User with the given email does not exist."},
        )

    def test_get_email_options_inactive_user(self):
        serializer = CustomPasswordResetSerializer(
            data={"email": self.inactive_user.email}
        )
        serializer.is_valid()  # Ensure data is validated
        with self.assertRaises(ValidationError) as e:
            serializer.get_email_options()
        self.assertEqual(
            e.exception.detail,
            {
                "details": "Account is not active. Please contact the administrator."
            },
        )


class TestProfileSerializer(TestCase):
    def setUp(self):
        self.user_model = get_user_model()
        self.user = self.user_model.objects.create_user(
            username="test_user", email="test@example.com", password="password"
        )

    def test_profile_serializer_fields(self):
        serializer = ProfileSerializer(self.user)
        expected_fields = [
            "pk",
            "email",
            "username",
            "first_name",
            "last_name",
            "affiliation",
            "github_url",
            "google_scholar_url",
            "linkedin_url",
        ]
        self.assertEqual(set(serializer.data.keys()), set(expected_fields))

    def test_profile_serializer_update(self):
        serializer = ProfileSerializer(
            self.user,
            data={
                "affiliation": "Test Affiliation",
                "github_url": "https://github.com/test",
                "google_scholar_url": "https://scholar.google.com/citations?user=test",
                "linkedin_url": "https://www.linkedin.com/in/test",
            },
        )
        self.assertTrue(serializer.is_valid())
        serializer.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.profile.affiliation, "Test Affiliation")
        self.assertEqual(
            self.user.profile.github_url, "https://github.com/test"
        )
        self.assertEqual(
            self.user.profile.google_scholar_url,
            "https://scholar.google.com/citations?user=test",
        )
        self.assertEqual(
            self.user.profile.linkedin_url, "https://www.linkedin.com/in/test"
        )
