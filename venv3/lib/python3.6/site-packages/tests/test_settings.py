from django.test import TestCase
from django.conf import settings
from tests.utils import unload_django_ses


class SettingsImportTest(TestCase):
    def test_aws_access_key_given(self):
        settings.AWS_ACCESS_KEY_ID = "Yjc4MzQ4MGYzMTBhOWY3ODJhODhmNTBkN2QwY2IyZTdhZmU1NDM1ZQo"
        settings.AWS_SECRET_ACCESS_KEY = "NTBjYzAzNzVlMTA0N2FiMmFlODlhYjY5OTYwZjNkNjZmMWNhNzRhOQo"
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.ACCESS_KEY, settings.AWS_ACCESS_KEY_ID)
        self.assertEqual(django_ses.settings.SECRET_KEY, settings.AWS_SECRET_ACCESS_KEY)

    def test_ses_access_key_given(self):
        settings.AWS_SES_ACCESS_KEY_ID = "YmM2M2QwZTE3ODk3NTJmYzZlZDc1MDY0ZmJkMDZjZjhmOTU0MWQ4MAo"
        settings.AWS_SES_SECRET_ACCESS_KEY = "NDNiMzRjNzlmZGU0ZDAzZTQxNTkwNzdkNWE5Y2JlNjk4OGFkM2UyZQo"
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.ACCESS_KEY, settings.AWS_SES_ACCESS_KEY_ID)
        self.assertEqual(django_ses.settings.SECRET_KEY, settings.AWS_SES_SECRET_ACCESS_KEY)

    def test_proxy_settings_given(self):
        settings.AWS_SES_PROXY = "some.proxy.host.tld"
        settings.AWS_SES_PROXY_PORT = 1234
        settings.AWS_SES_PROXY_USER = 'some-user-id'
        settings.AWS_SES_PROXY_PASS = 'secret'
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.AWS_SES_PROXY, settings.AWS_SES_PROXY)
        self.assertEqual(django_ses.settings.AWS_SES_PROXY_PORT, settings.AWS_SES_PROXY_PORT)
        self.assertEqual(django_ses.settings.AWS_SES_PROXY_USER, settings.AWS_SES_PROXY_USER)
        self.assertEqual(django_ses.settings.AWS_SES_PROXY_PASS, settings.AWS_SES_PROXY_PASS)

    def test_ses_configuration_set_given(self):
        settings.AWS_SES_CONFIGURATION_SET = "test-set"
        unload_django_ses()
        import django_ses
        self.assertEqual(django_ses.settings.AWS_SES_CONFIGURATION_SET, settings.AWS_SES_CONFIGURATION_SET)
