import unittest
from django.apps import AppConfig
from accounts.apps import AccountsConfig


class TestAccountsConfig(unittest.TestCase):
    def test_is_subclass_of_AppConfig(self):
        self.assertTrue(issubclass(AccountsConfig, AppConfig))


if __name__ == "__main__":
    unittest.main()
