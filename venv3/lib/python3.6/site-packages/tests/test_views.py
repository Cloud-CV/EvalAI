import json
try:
    from unittest import mock
except ImportError:
    import mock

from django.core.urlresolvers import reverse
from django.test import TestCase

from django_ses.signals import bounce_received, complaint_received
from django_ses import utils as ses_utils


class HandleBounceTest(TestCase):
    """
    Test the bounce web hook handler.
    """
    def setUp(self):
        self._old_bounce_receivers = bounce_received.receivers
        bounce_received.receivers = []

        self._old_complaint_receivers = complaint_received.receivers
        complaint_received.receivers = []

    def tearDown(self):
        bounce_received.receivers = self._old_bounce_receivers
        complaint_received.receivers = self._old_complaint_receivers

    def test_handle_bounce(self):
        """
        Test handling a normal bounce request.
        """
        req_mail_obj = {
            "timestamp":"2012-05-25T14:59:38.623-07:00",
            "messageId":"000001378603177f-7a5433e7-8edb-42ae-af10-f0181f34d6ee-000000",
            "source":"sender@example.com",
            "destination":[
                "recipient1@example.com",
                "recipient2@example.com",
                "recipient3@example.com",
                "recipient4@example.com"
            ]
        }
        req_bounce_obj = {
            'bounceType': 'Permanent',
            'bounceSubType': 'General',
            'bouncedRecipients': [
                {
                    "status":"5.0.0",
                    "action":"failed",
                    "diagnosticCode":"smtp; 550 user unknown",
                    "emailAddress":"recipient1@example.com",
                },
                {
                    "status":"4.0.0",
                    "action":"delayed",
                    "emailAddress":"recipient2@example.com",
                }
            ],
            "reportingMTA": "example.com",
            "timestamp":"2012-05-25T14:59:38.605-07:00",
            "feedbackId":"000001378603176d-5a4b5ad9-6f30-4198-a8c3-b1eb0c270a1d-000000",
        }

        message_obj = {
            'notificationType': 'Bounce',
            'mail': req_mail_obj,
            'bounce': req_bounce_obj,
        }

        notification = {
            "Type" : "Notification",
            "MessageId" : "22b80b92-fdea-4c2c-8f9d-bdfb0c7bf324",
            "TopicArn" : "arn:aws:sns:us-east-1:123456789012:MyTopic",
            "Subject" : "AWS Notification Message",
            "Message" : json.dumps(message_obj),
            "Timestamp" : "2012-05-02T00:54:06.655Z",
            "SignatureVersion" : "1",
            "Signature" : "",
            "SigningCertURL" : "",
            "UnsubscribeURL" : ""
        }

        def _handler(sender, mail_obj, bounce_obj, **kwargs):
            _handler.called = True
            self.assertEqual(req_mail_obj, mail_obj)
            self.assertEqual(req_bounce_obj, bounce_obj)
        _handler.called = False
        bounce_received.connect(_handler)

        # Mock the verification
        with mock.patch.object(ses_utils, 'verify_bounce_message') as verify:
            verify.return_value = True

            self.client.post(reverse('django_ses_bounce'),
                             json.dumps(notification), content_type='application/json')

        self.assertTrue(_handler.called)

    def test_handle_complaint(self):
        """
        Test handling a normal complaint request.
        """
        req_mail_obj = {
            "timestamp":"2012-05-25T14:59:38.623-07:00",
            "messageId":"000001378603177f-7a5433e7-8edb-42ae-af10-f0181f34d6ee-000000",
            "source":"sender@example.com",
            "destination": [
                "recipient1@example.com",
                "recipient2@example.com",
                "recipient3@example.com",
                "recipient4@example.com",
            ]
        }
        req_complaint_obj = {
            "userAgent":"Comcast Feedback Loop (V0.01)",
            "complainedRecipients": [
                {
                    "emailAddress":"recipient1@example.com",
                }
            ],
            "complaintFeedbackType":"abuse",
            "arrivalDate":"2009-12-03T04:24:21.000-05:00",
            "timestamp":"2012-05-25T14:59:38.623-07:00",
            "feedbackId":"000001378603177f-18c07c78-fa81-4a58-9dd1-fedc3cb8f49a-000000",
        }

        message_obj = {
            'notificationType': 'Complaint',
            'mail': req_mail_obj,
            'complaint': req_complaint_obj,
        }

        notification = {
            "Type" : "Notification",
            "MessageId" : "22b80b92-fdea-4c2c-8f9d-bdfb0c7bf324",
            "TopicArn" : "arn:aws:sns:us-east-1:123456789012:MyTopic",
            "Subject" : "AWS Notification Message",
            "Message" : json.dumps(message_obj),
            "Timestamp" : "2012-05-02T00:54:06.655Z",
            "SignatureVersion" : "1",
            "Signature" : "",
            "SigningCertURL" : "",
            "UnsubscribeURL" : ""
        }

        def _handler(sender, mail_obj, complaint_obj, **kwargs):
            _handler.called = True
            self.assertEqual(req_mail_obj, mail_obj)
            self.assertEqual(req_complaint_obj, complaint_obj)
        _handler.called = False
        complaint_received.connect(_handler)

        # Mock the verification
        with mock.patch.object(ses_utils, 'verify_bounce_message') as verify:
            verify.return_value = True

            self.client.post(reverse('django_ses_bounce'),
                             json.dumps(notification), content_type='application/json')

        self.assertTrue(_handler.called)
