from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings
from rest_framework_docs.settings import DRFSettings


class DRFDocsViewTests(TestCase):

    SETTINGS_HIDE_DOCS = {
        'HIDE_DOCS': True  # Default: False
    }

    def setUp(self):
        super(DRFDocsViewTests, self).setUp()

    def test_settings_module(self):

        settings = DRFSettings()

        self.assertEqual(settings.get_setting("HIDE_DOCS"), False)
        self.assertEqual(settings.get_setting("TEST"), None)

    def test_index_view_with_endpoints(self):
        """
        Should load the drf focs view with all the endpoints.
        NOTE: Views that do **not** inherit from DRF's "APIView" are not included.
        """
        response = self.client.get(reverse('drfdocs'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["endpoints"]), 11)

        # Test the login view
        self.assertEqual(response.context["endpoints"][0].name_parent, "accounts")
        self.assertEqual(response.context["endpoints"][0].allowed_methods, ['POST', 'OPTIONS'])
        self.assertEqual(response.context["endpoints"][0].path, "/accounts/login/")
        self.assertEqual(response.context["endpoints"][0].docstring, "A view that allows users to login providing their username and password.")
        self.assertEqual(len(response.context["endpoints"][0].fields), 2)
        self.assertEqual(response.context["endpoints"][0].fields[0]["type"], "CharField")
        self.assertTrue(response.context["endpoints"][0].fields[0]["required"])

        self.assertEqual(response.context["endpoints"][1].name_parent, "accounts")
        self.assertEqual(response.context["endpoints"][1].allowed_methods, ['POST', 'OPTIONS'])
        self.assertEqual(response.context["endpoints"][1].path, "/accounts/login2/")
        self.assertEqual(response.context["endpoints"][1].docstring, "A view that allows users to login providing their username and password. Without serializer_class")
        self.assertEqual(len(response.context["endpoints"][1].fields), 2)
        self.assertEqual(response.context["endpoints"][1].fields[0]["type"], "CharField")
        self.assertTrue(response.context["endpoints"][1].fields[0]["required"])

        # The view "OrganisationErroredView" (organisations/(?P<slug>[\w-]+)/errored/) should contain an error.
        self.assertEqual(str(response.context["endpoints"][9].errors), "'test_value'")

    def test_index_search_with_endpoints(self):
        response = self.client.get("%s?search=reset-password" % reverse("drfdocs"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["endpoints"]), 2)
        self.assertEqual(response.context["endpoints"][1].path, "/accounts/reset-password/confirm/")
        self.assertEqual(len(response.context["endpoints"][1].fields), 3)

    @override_settings(REST_FRAMEWORK_DOCS=SETTINGS_HIDE_DOCS)
    def test_index_view_docs_hidden(self):
        """
        Should prevent the docs from loading the "HIDE_DOCS" is set
        to "True" or undefined under settings
        """
        response = self.client.get(reverse('drfdocs'))

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.reason_phrase.upper(), "NOT FOUND")
