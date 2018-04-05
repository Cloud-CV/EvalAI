import responses

from django.core import mail
from django.conf import settings
from django.test import TestCase

from web.tasks import notify_admin_on_receiving_contact_message


class NotifyAdminOnContactMessage(TestCase):

    def setUp(self):
        self.name = 'user'
        self.email = 'user@domain.com'
        self.message = 'Sample message'
        self.host_url = 'https://hooks.slack.com/services/token/token/token'

    @responses.activate
    def test_notify_slack_channel_on_contact_message(self):
        with responses.RequestsMock() as rsps:
            rsps.add(responses.POST,
                     self.host_url,
                     status=200,
                     content_type='application/json',
                     body='ok')

            resp = notify_admin_on_receiving_contact_message(self.host_url,
                                                             self.name,
                                                             self.email,
                                                             self.message)
            self.assertEqual(resp, None)

    def test_notify_admin_via_email_on_contact_message(self):
        subject = 'EvalAI contact message received from {}'.format(self.name)
        message = self.message

        mail.send_mail(subject, message, settings.EMAIL_HOST_USER, [settings.ADMIN_EMAIL], fail_silently=False)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, subject)
