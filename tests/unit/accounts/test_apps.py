import unittest

from accounts.apps import AccountsConfig
from django.apps import AppConfig


class TestAccountsConfig(unittest.TestCase):
    def test_is_subclass_of_AppConfig(self):
        self.assertTrue(issubclass(AccountsConfig, AppConfig))


if __name__ == "__main__":
    unittest.main()
