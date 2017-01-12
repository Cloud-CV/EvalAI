from django.test import Client
from django.test import TestCase

from evalai.views import page_not_found
from evalai.urls import handler404


class TestErrorPages(TestCase):

    def test_error_handlers_404(self):
        self.assertTrue(handler404.endswith('.page_not_found'))
        c = Client()
        request = c.get("/abc")
        response = page_not_found(request)
        self.assertEqual(request.status_code, response.status_code)
        self.assertIn('404', unicode(response))
