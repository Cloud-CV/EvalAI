import mock
from mock import Mock
from rest_framework.test import APITestCase

from django.contrib.auth.models import User, AnonymousUser
from django.test.client import RequestFactory

from accounts.permissions import HasVerifiedEmail


class BaseAPITestClass(APITestCase):
    def setUp(self):
        self.factory = RequestFactory()


class HasVerifiedEmailTest(BaseAPITestClass):
    def setUp(self):
        super(HasVerifiedEmailTest, self).setUp()

    def test_has_verified_email_when_request_user_is_anonymous(self):
        test_request = self.factory.get('challenge/')
        test_request.user = AnonymousUser()
        test_view = None

        test_has_verified_email = HasVerifiedEmail()
        self.assertTrue(test_has_verified_email.has_permission(test_request, test_view))

    @mock.patch("allauth.account.models.EmailAddress.objects")
    def test_has_verified_email_when_verified_email_address_objects_exist(self, mock_email_address_objects):
        mock_email_address_objects_filter = Mock()
        mock_email_address_objects.filter.return_value = mock_email_address_objects_filter
        mock_email_address_objects_filter.exists.return_value = True

        test_request = self.factory.get('challenge/')
        test_request.user = User()
        test_view = None
        test_has_verified_email = HasVerifiedEmail()
        self.assertTrue(test_has_verified_email.has_permission(test_request, test_view))

    @mock.patch("allauth.account.models.EmailAddress.objects")
    def test_has_verified_email_when_verified_email_address_objects_do_not_exist(self, mock_email_address_objects):
        mock_email_address_objects_filter = Mock()
        mock_email_address_objects.filter.return_value = mock_email_address_objects_filter
        mock_email_address_objects_filter.exists.return_value = False

        test_request = self.factory.get('challenge/')
        test_request.user = User()
        test_view = None
        test_has_verified_email = HasVerifiedEmail()
        self.assertFalse(test_has_verified_email.has_permission(test_request, test_view))
