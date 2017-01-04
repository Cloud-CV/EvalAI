from django.core.urlresolvers import reverse, resolve
from django.test import TestCase

from evalai.urls import * # noqa: ignore=F405


class TestURLs(TestCase):

    def test_obtain_expiring_auth_token(self):
        url = reverse('obtain_expiring_auth_token')
        self.assertEqual(url, '/api/auth/login')

        resolver = resolve('/api/auth/login')
        self.assertEqual(resolver.view_name, 'obtain_expiring_auth_token')
