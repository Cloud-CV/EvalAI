from base.utils import get_user_by_email
from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase, TransactionTestCase


def _drop_email_unique_constraint():
    with connection.cursor() as cursor:
        cursor.execute(
            "ALTER TABLE auth_user DROP CONSTRAINT IF EXISTS auth_user_email_unique"
        )


def _add_email_unique_constraint():
    with connection.cursor() as cursor:
        cursor.execute(
            "SELECT 1 FROM pg_constraint WHERE conname = %s",
            ["auth_user_email_unique"],
        )
        if cursor.fetchone():
            return
        cursor.execute(
            "ALTER TABLE auth_user ADD CONSTRAINT auth_user_email_unique "
            "UNIQUE (email)"
        )


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


class GetUserByEmailDuplicateTest(TransactionTestCase):
    """Uses TransactionTestCase and drops unique constraint to test duplicate-email behavior."""

    def setUp(self):
        _drop_email_unique_constraint()

    def tearDown(self):
        # Remove duplicate users before re-adding unique constraint
        User.objects.filter(username__in=("bob_old", "bob_new")).delete()
        _add_email_unique_constraint()

    def test_returns_oldest_when_duplicates_exist(self):
        older = User.objects.create_user(
            username="bob_old", email="bob@example.com", password="password"
        )
        User.objects.create_user(
            username="bob_new", email="bob@example.com", password="password"
        )
        result = get_user_by_email("bob@example.com")
        self.assertEqual(result.pk, older.pk)
