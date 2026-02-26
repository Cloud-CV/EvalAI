from base.utils import get_user_by_email
from django.contrib.auth.models import User
from django.test import TestCase


class GetUserByEmailTest(TestCase):
    def test_returns_user_for_unique_email(self):
        user = User.objects.create_user(
            username="alice", email="alice@example.com", password="password"
        )
        result = get_user_by_email("alice@example.com")
        self.assertEqual(result.pk, user.pk)

    def test_raises_for_nonexistent_email(self):
        with self.assertRaises(User.DoesNotExist):
            get_user_by_email("ghost@example.com")

    def test_returns_oldest_when_duplicates_exist(self):
        older = User.objects.create_user(
            username="bob_old", email="bob@example.com", password="password"
        )
        User.objects.create_user(
            username="bob_new", email="bob@example.com", password="password"
        )
        result = get_user_by_email("bob@example.com")
        self.assertEqual(result.pk, older.pk)
