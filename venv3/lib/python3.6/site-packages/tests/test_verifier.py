import base64
try:
    from unittest import mock
except ImportError:
    import mock

try:
    import requests
except ImportError:
    requests = None

try:
    import M2Crypto
except ImportError:
    M2Crypto = None

from unittest import TestCase, skipIf

from django_ses.utils import BounceMessageVerifier

class BounceMessageVerifierTest(TestCase):
    """
    Test for bounce message signature verification
    """
    @skipIf(requests is None, "requests is not installed")
    @skipIf(M2Crypto is None, "M2Crypto is not installed")
    def test_load_certificate(self):
        verifier = BounceMessageVerifier({})
        with mock.patch.object(verifier, '_get_cert_url') as get_cert_url:
            get_cert_url.return_value = "http://www.example.com/"
            with mock.patch.object(requests, 'get') as request_get:
                request_get.return_value.status_code = 200
                request_get.return_value.content = "Spam"
                with mock.patch.object(M2Crypto.X509, 'load_cert_string') as load_cert_string:
                    self.assertEqual(verifier.certificate, load_cert_string.return_value)

    def test_is_verified(self):
        verifier = BounceMessageVerifier({'Signature': base64.b64encode(b'Spam & Eggs')})
        verifier._certificate = mock.Mock()
        verify_final = verifier._certificate.get_pubkey.return_value.verify_final
        verify_final.return_value = 1
        with mock.patch.object(verifier, '_get_bytes_to_sign'):
            self.assertTrue(verifier.is_verified())

        verify_final.assert_called_once_with(b'Spam & Eggs')

    def test_is_verified_bad_value(self):
        verifier = BounceMessageVerifier({'Signature': base64.b64encode(b'Spam & Eggs')})
        verifier._certificate = mock.Mock()
        verifier._certificate.get_pubkey.return_value.verify_final.return_value = 0
        with mock.patch.object(verifier, '_get_bytes_to_sign'):
            self.assertFalse(verifier.is_verified())

    def test_get_cert_url(self):
        """
        Test url trust verification
        """
        verifier = BounceMessageVerifier({
            'SigningCertURL': 'https://amazonaws.com/',
        })
        self.assertEqual(verifier._get_cert_url(), 'https://amazonaws.com/')

    def test_http_cert_url(self):
        """
        Test url trust verification. Non-https urls should be rejected.
        """
        verifier = BounceMessageVerifier({
            'SigningCertURL': 'http://amazonaws.com/',
        })
        self.assertEqual(verifier._get_cert_url(), None)

    def test_untrusted_cert_url_domain(self):
        """
        Test url trust verification. Untrusted domains should be rejected.
        """
        verifier = BounceMessageVerifier({
            'SigningCertURL': 'https://www.example.com/',
        })
        self.assertEqual(verifier._get_cert_url(), None)

    def test_get_bytes_to_sign(self):
        verifier = BounceMessageVerifier({
            'Type': 'Notification'
        })
        self.assertEqual(verifier._get_bytes_to_sign(), 'Type\nNotification\n')
