from django.test import TestCase
from django.test.client import RequestFactory

from evalai import urls
from evalai import views

class TestErrorPages(TestCase):

    def test_error_handlers(self):
        self.assertTrue(urls.handler404.endswith('.handler404'))
        self.assertTrue(urls.handler500.endswith('.handler500'))
        factory = RequestFactory()
        request = factory.get('/')
        response = handler404(request)
        self.assertEqual(response.status_code, 404)
        self.assertIn('404 Not Found!!', unicode(response))
        response = handler500(request)
        self.assertEqual(response.status_code, 500)
        self.assertIn('500 Internal Server Error', unicode(response))
