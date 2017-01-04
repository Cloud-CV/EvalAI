from django.test.client import RequestFactory
from django.test import TestCase

from evalai.views import page_not_found, internal_server_error
from evalai import urls


class TestErrorPages(TestCase):

    def test_error_handlers_404(self):
        self.assertTrue(urls.handler404.endswith('.page_not_found'))
        factory = RequestFactory()
        request = factory.get('/')
        response = page_not_found(request)
        self.assertEqual(response.status_code, 404)
        self.assertIn('Error 404', unicode(response))

    def test_error_handlers_500(self):
        self.assertTrue(urls.handler500.endswith('.internal_server_error'))
        factory = RequestFactory()
        request = factory.get('/')
        response = internal_server_error(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn('500 Internal Server Error', unicode(response))
