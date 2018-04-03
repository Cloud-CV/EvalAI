import responses

from django.test import TestCase

from web.tasks import notify_admin_on_receiving_contact_message


class NotifyAdminOnContactMessage(TestCase):

    def setUp(self):
        self.name = 'user'
        self.email = 'user@domain.com'
        self.message = 'Sample message'
        self.host_url = 'https://hooks.slack.com/services/token/token/token'

    @responses.activate
    def test_notify_admin_on_contact_message(self):
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
