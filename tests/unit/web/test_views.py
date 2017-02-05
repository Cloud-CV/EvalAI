from django.core.urlresolvers import reverse_lazy

from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from web.models import Contact

from django.test import Client
from django.test import TestCase

from web.views import page_not_found
from evalai.urls import handler404


class BaseAPITestCase(APITestCase):

    def setUp(self):
        self.client = APIClient(enforce_csrf_checks=True)

        self.message = Contact.objects.create(
            name='someuser',
            email='user@test.com',
            message='Message for Contact')


class CreateContactMessage(BaseAPITestCase):

    def setUp(self):
        super(CreateContactMessage, self).setUp()
        self.url = reverse_lazy('web:contact_us')

        self.data = {
            'name': 'New Message',
            'email': 'newuser@test.com',
            'message': 'New Message for Conatct'
        }

    def test_create_contact_message_with_all_data(self):
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_contact_message_with_no_data(self):
        del self.data['message']
        response = self.client.post(self.url, self.data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TestErrorPages(TestCase):

    def test_error_handlers_404(self):
        self.assertTrue(handler404.endswith('.page_not_found'))
        c = Client()
        request = c.get("/abc")
        response = page_not_found(request)
        self.assertEqual(request.status_code, response.status_code)
        self.assertIn('Error 404', unicode(response))
