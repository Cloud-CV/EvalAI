from django.test import TestCase
from django.test.client import Client
from accounts.urls import *
from evalai.urls import *

class AccountsURLTest(TestCase):

    def setUp(self):
        self.c = Client()

    def test_disable_user(self):
        response = self.c.get('accounts/user/disable')
        self.assertEqual(response.status_code, 200)
