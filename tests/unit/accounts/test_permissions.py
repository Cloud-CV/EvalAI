import unittest, mock
from rest_framework.test import APITestCase
from rest_framework import permissions

from allauth.account.models import EmailAddress
from django.test.client import RequestFactory

from accounts.permissions import HasVerifiedEmail

class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.factory = RequestFactory()

class HasVerifiedEmailTest(BaseAPITestClass):
    def setUp(self):
        super(HasVerifiedEmailTest, self).setUp()

    def test_has_verified_email_when_request_user_is_anonymous(self):
        test_request = self.factory.get('')
        test_request.user.is_anonymous = True
        test_view = None

        self.assertTrue(HasVerifiedEmail(test_request, test_view))

    @mock.patch("accounts.permissions.EmailAddress.objects")
    def test_has_verified_email_when_verified_email_address_objects_exist(self, mock_email_objects):
        mock_email_objects.filter.return_value = mock_email_objects
        mock_email_objects.exists.return_value = True

        test_request = self.factory.get('/about')
        test_view = None
        self.assertTrue(HasVerifiedEmail(test_requqest, test_view))

    @mock.patch("accounts.permissions.EmailAddress.objects")
    def test_has_verified_email_when_verified_email_address_objects_do_not_exist(self, mock_email_objects):
        mock_email_objects.filter.return_value = mock_email_objects
        mock_email_objects.exists.return_value = False

        test_request = self.factory.get('/about')
        test_view = None
        self.assertFalse(HasVerifiedEmail(test_requqest, test_view))
