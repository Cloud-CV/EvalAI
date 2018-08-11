# -*- coding: utf-8 -*-

import email

from django.conf import settings as django_settings
from django.utils.encoding import smart_str
from django.core.mail import send_mail
from django.test import TestCase

from boto.ses import SESConnection

import django_ses
from django_ses import settings

# random key generated with `openssl genrsa 512`
DKIM_PRIVATE_KEY = '''
-----BEGIN RSA PRIVATE KEY-----
MIIBOwIBAAJBALCKsjD8UUxBESo1OLN6gptp1lD0U85AgXGL571/SQ3k61KhAQ8h
hL3lnfQKn/XCl2oCXscEwgJv43IUs+VETWECAwEAAQJAQ8XK6GFEuHhWJZTu4n/K
ee0keEmDjq9WwgdKfIXLvsgaaNxCObhzv7G5rPU+U/3z1/0CtGR+DOPgoiaI/5HM
XQIhAN4h+o2WzRrz+dD/+zMGC9h1KEFvukIoP62kLOxW0eg/AiEAy3VD+UkRni4H
6UEJgCe0oZIiBCxj12/wUHFj1cfJYl8CICsndsGjFl2yIEpWMLsM5ag7uoJb7leD
8jsNthyEEWuJAiEAjeF6w26HEK286pZmD66gskN74TkrbuMqzI4mNsCZ2TUCIQCJ
HuuR7wc0HJ/cfVi8Kgm5B+sHY9/7KDWAYGGnbGgCNA==
-----END RSA PRIVATE KEY-----
'''
DKIM_PUBLIC_KEY = 'MFwwDQYJKoZIhvcNAQEBBQADSwAwSAJBALCKsjD8UUxBESo1OLN6gptp1lD0U85AgXGL571/SQ3k61KhAQ8hhL3lnfQKn/XCl2oCXscEwgJv43IUs+VETWECAwEAAQ=='


class SESConfigurationSetTester(object):

    def __init__(self, configuration_set):
        self.message = None
        self.dkim_domain = None
        self.dkim_key = None
        self.dkim_selector = None
        self.dkim_headers = ()
        self.configuration_set = configuration_set

    def __call__(self, message, dkim_domain=None, dkim_key=None,
                 dkim_selector=None, dkim_headers=()):
        self.message = message
        self.dkim_domain = dkim_domain
        self.dkim_key = dkim_key
        self.dkim_selector = dkim_selector
        self.dkim_headers = dkim_headers
        return self.configuration_set


class FakeSESConnection(SESConnection):
    '''
    A fake SES connection for testing purposes.It behaves similarly
    to django's dummy backend
    (https://docs.djangoproject.com/en/dev/topics/email/#dummy-backend)

    Emails sent with send_raw_email is stored in ``outbox`` attribute
    which is a list of kwargs received by ``send_raw_email``.
    '''
    outbox = []

    def __init__(self, *args, **kwargs):
        self.outbox.append(kwargs)

    def send_raw_email(self, **kwargs):
        self.outbox.append(kwargs)
        response = {
            'SendRawEmailResponse': {
                'SendRawEmailResult': {
                    'MessageId': 'fake_message_id',
                },
                'ResponseMetadata': {
                    'RequestId': 'fake_request_id',
                },
            }
        }
        return response


class FakeSESBackend(django_ses.SESBackend):
    '''
    A fake SES backend for testing purposes. It overrides the real SESBackend's
    get_rate_limit method so we can run tests without valid AWS credentials.
    '''

    def get_rate_limit(self):
        return 10


class SESBackendTest(TestCase):
    def setUp(self):
        # TODO: Fix this -- this is going to cause side effects
        django_settings.EMAIL_BACKEND = 'tests.test_backend.FakeSESBackend'
        django_ses.SESConnection = FakeSESConnection
        self.outbox = FakeSESConnection.outbox

    def tearDown(self):
        # Empty outbox everytime test finishes
        FakeSESConnection.outbox = []

    def _rfc2047_helper(self, value_to_encode):
        # references: https://docs.python.org/3/library/email.header.html, https://tools.ietf.org/html/rfc2047.html
        name, addr = email.utils.parseaddr(value_to_encode)
        name = email.header.Header(name).encode()
        return email.utils.formataddr((name, addr))

    def test_rfc2047_helper(self):
        # Ensures that the underlying email.header library code is encoding as expected, using known values
        unicode_from_addr = u'Unicode Name óóóóóó <from@example.com>'
        rfc2047_encoded_from_addr = '=?utf-8?b?VW5pY29kZSBOYW1lIMOzw7PDs8Ozw7PDsw==?= <from@example.com>'
        self.assertEqual(self._rfc2047_helper(unicode_from_addr), rfc2047_encoded_from_addr)

    def test_send_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = None

        unicode_from_addr = u'Unicode Name óóóóóó <from@example.com>'

        send_mail('subject', 'body', unicode_from_addr, ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['raw_message']))
        self.assertTrue('X-SES-CONFIGURAITON-SET' not in mail.keys())
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], self._rfc2047_helper(unicode_from_addr))
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')

    def test_configuration_set_send_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = 'test-set'
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['raw_message']))
        self.assertEqual(mail['X-SES-CONFIGURATION-SET'], 'test-set')
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], 'from@example.com')
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')

    def test_configuration_set_callable_send_mail(self):
        config_set_callable = SESConfigurationSetTester('my-config-set')
        settings.AWS_SES_CONFIGURATION_SET = config_set_callable
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()
        mail = email.message_from_string(smart_str(message['raw_message']))
        # ensure we got the correct configuration message payload
        self.assertEqual(mail['X-SES-CONFIGURATION-SET'], 'my-config-set')
        self.assertEqual(mail['subject'], 'subject')
        self.assertEqual(mail['from'], 'from@example.com')
        self.assertEqual(mail['to'], 'to@example.com')
        self.assertEqual(mail.get_payload(), 'body')
        # ensure we passed in the proper arguments to our callable
        self.assertEqual(config_set_callable.message.subject, 'subject')
        self.assertEqual(config_set_callable.dkim_domain, None)
        self.assertEqual(config_set_callable.dkim_key, None)
        self.assertEqual(config_set_callable.dkim_selector, 'ses')
        self.assertEqual(config_set_callable.dkim_headers, ('From', 'To', 'Cc', 'Subject'))

    def test_dkim_mail(self):
        settings.AWS_SES_CONFIGURATION_SET = None
        # DKIM verification uses DNS to retrieve the public key when checking
        # the signature, so we need to replace the standard query response with
        # one that always returns the test key.
        try:
            import dkim
            import dns
        except ImportError:
            return

        def dns_query(qname, rdtype):
            name = dns.name.from_text(qname)
            response = dns.message.from_text(
                    'id 1\n;ANSWER\n%s 60 IN TXT "v=DKIM1; p=%s"' %\
                            (qname, DKIM_PUBLIC_KEY))
            return dns.resolver.Answer(name, rdtype, 1, response)
        dns.resolver.query = dns_query

        settings.DKIM_DOMAIN = 'example.com'
        settings.DKIM_PRIVATE_KEY = DKIM_PRIVATE_KEY
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        message = self.outbox.pop()['raw_message']
        self.assertTrue(dkim.verify(message))
        self.assertFalse(dkim.verify(message + 'some additional text'))
        self.assertFalse(dkim.verify(
                            message.replace('from@example.com', 'from@spam.com')))

    def test_return_path(self):
        '''
        Ensure that the 'source' argument sent into send_raw_email uses
        settings.AWS_SES_RETURN_PATH, defaults to from address.
        '''
        settings.AWS_SES_RETURN_PATH = None
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        self.assertEqual(self.outbox.pop()['source'], 'from@example.com')


class SESBackendTestReturn(TestCase):
    def setUp(self):
        # TODO: Fix this -- this is going to cause side effects
        django_settings.EMAIL_BACKEND = 'tests.test_backend.FakeSESBackend'
        django_ses.SESConnection = FakeSESConnection
        self.outbox = FakeSESConnection.outbox

    def tearDown(self):
        # Empty outbox everytime test finishes
        FakeSESConnection.outbox = []

    def test_return_path(self):
        settings.AWS_SES_RETURN_PATH = "return@example.com"
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        self.assertEqual(self.outbox.pop()['source'], 'return@example.com')


class SESBackendTestProxySettings(TestCase):
    def setUp(self):
        # TODO: Fix this -- this is going to cause side effects
        django_settings.EMAIL_BACKEND = 'tests.test_backend.FakeSESBackend'
        django_ses.SESConnection = FakeSESConnection
        self.outbox = FakeSESConnection.outbox
        settings.AWS_SES_PROXY = 'some.proxy.host.tld'
        settings.AWS_SES_PROXY_PORT = 1234
        settings.AWS_SES_PROXY_USER = 'some-user-id'
        settings.AWS_SES_PROXY_PASS = 'secret'

    def test_proxy_settings(self):
        send_mail('subject', 'body', 'from@example.com', ['to@example.com'])
        # connection setup args are in the first outbox message
        connection_kwargs = self.outbox.pop(0)

        self.assertIn('proxy', connection_kwargs)
        self.assertEqual(connection_kwargs['proxy'], settings.AWS_SES_PROXY)

        self.assertIn('proxy_port', connection_kwargs)
        self.assertEqual(connection_kwargs['proxy_port'], settings.AWS_SES_PROXY_PORT)

        self.assertIn('proxy_user', connection_kwargs)
        self.assertEqual(connection_kwargs['proxy_user'], settings.AWS_SES_PROXY_USER)

        self.assertIn('proxy_pass', connection_kwargs)
        self.assertEqual(connection_kwargs['proxy_pass'], settings.AWS_SES_PROXY_PASS)
