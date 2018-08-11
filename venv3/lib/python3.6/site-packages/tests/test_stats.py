from django.test import TestCase

from django_ses.views import (emails_parse, stats_to_list, quota_parse,
    sum_stats)

# Mock of what boto's SESConnection.get_send_statistics() returns
STATS_DICT = {
    u'GetSendStatisticsResponse': {
        u'GetSendStatisticsResult': {
            u'SendDataPoints': [
                {
                    u'Bounces': u'1',
                    u'Complaints': u'0',
                    u'DeliveryAttempts': u'11',
                    u'Rejects': u'0',
                    u'Timestamp': u'2011-02-28T13:50:00Z',
                },
                {
                    u'Bounces': u'1',
                    u'Complaints': u'0',
                    u'DeliveryAttempts': u'3',
                    u'Rejects': u'0',
                    u'Timestamp': u'2011-02-24T23:35:00Z',
                },
                {
                    u'Bounces': u'0',
                    u'Complaints': u'2',
                    u'DeliveryAttempts': u'8',
                    u'Rejects': u'0',
                    u'Timestamp': u'2011-02-24T16:35:00Z',
                },
                {
                    u'Bounces': u'0',
                    u'Complaints': u'2',
                    u'DeliveryAttempts': u'33',
                    u'Rejects': u'0',
                    u'Timestamp': u'2011-02-25T20:35:00Z',
                },
                {
                    u'Bounces': u'0',
                    u'Complaints': u'0',
                    u'DeliveryAttempts': u'3',
                    u'Rejects': u'3',
                    u'Timestamp': u'2011-02-28T23:35:00Z',
                },
                {
                    u'Bounces': u'0',
                    u'Complaints': u'0',
                    u'DeliveryAttempts': u'2',
                    u'Rejects': u'3',
                    u'Timestamp': u'2011-02-25T22:50:00Z',
                },
                {
                    u'Bounces': u'0',
                    u'Complaints': u'0',
                    u'DeliveryAttempts': u'6',
                    u'Rejects': u'0',
                    u'Timestamp': u'2011-03-01T13:20:00Z',
                },
            ],
        }
    }
}

QUOTA_DICT = {
    u'GetSendQuotaResponse': {
        u'GetSendQuotaResult': {
            u'Max24HourSend': u'10000.0',
            u'MaxSendRate': u'5.0',
            u'SentLast24Hours': u'1677.0'
        },
        u'ResponseMetadata': {
            u'RequestId': u'8f100233-44e7-11e0-a926-a198963635d8'
        }
    }
}

VERIFIED_EMAIL_DICT = {
    u'ListVerifiedEmailAddressesResponse': {
        u'ListVerifiedEmailAddressesResult': {
            u'VerifiedEmailAddresses': [
                u'test2@example.com',
                u'test1@example.com',
                u'test3@example.com'
            ]
        },
        u'ResponseMetadata': {
            u'RequestId': u'9afe9c18-44ed-11e0-802a-25a1a14c5a6e'
        }
    }
}


class StatParsingTest(TestCase):
    def setUp(self):
        self.stats_dict = STATS_DICT
        self.quota_dict = QUOTA_DICT
        self.emails_dict = VERIFIED_EMAIL_DICT

    def test_stat_to_list(self):
        expected_list = [
            {
                u'Bounces': u'0',
                u'Complaints': u'2',
                u'DeliveryAttempts': u'8',
                u'Rejects': u'0',
                u'Timestamp': u'2011-02-24T16:35:00Z',
            },
            {
                u'Bounces': u'1',
                u'Complaints': u'0',
                u'DeliveryAttempts': u'3',
                u'Rejects': u'0',
                u'Timestamp': u'2011-02-24T23:35:00Z',
            },
            {
                u'Bounces': u'0',
                u'Complaints': u'2',
                u'DeliveryAttempts': u'33',
                u'Rejects': u'0',
                u'Timestamp': u'2011-02-25T20:35:00Z',
            },
            {
                u'Bounces': u'0',
                u'Complaints': u'0',
                u'DeliveryAttempts': u'2',
                u'Rejects': u'3',
                u'Timestamp': u'2011-02-25T22:50:00Z',
            },
            {
                u'Bounces': u'1',
                u'Complaints': u'0',
                u'DeliveryAttempts': u'11',
                u'Rejects': u'0',
                u'Timestamp': u'2011-02-28T13:50:00Z',
            },
            {
                u'Bounces': u'0',
                u'Complaints': u'0',
                u'DeliveryAttempts': u'3',
                u'Rejects': u'3',
                u'Timestamp': u'2011-02-28T23:35:00Z',
            },
            {
                u'Bounces': u'0',
                u'Complaints': u'0',
                u'DeliveryAttempts': u'6',
                u'Rejects': u'0',
                u'Timestamp': u'2011-03-01T13:20:00Z',
            },
        ]
        actual = stats_to_list(self.stats_dict, localize=False)

        self.assertEqual(len(actual), len(expected_list))
        self.assertEqual(actual, expected_list)

    def test_quota_parse(self):
        expected = {
            u'Max24HourSend': u'10000.0',
            u'MaxSendRate': u'5.0',
            u'SentLast24Hours': u'1677.0',
        }
        actual = quota_parse(self.quota_dict)

        self.assertEqual(actual, expected)

    def test_emails_parse(self):
        expected_list = [
            u'test1@example.com',
            u'test2@example.com',
            u'test3@example.com',
        ]
        actual = emails_parse(self.emails_dict)

        self.assertEqual(len(actual), len(expected_list))
        self.assertEqual(actual, expected_list)

    def test_sum_stats(self):
        expected = {
            'Bounces': 2,
            'Complaints': 4,
            'DeliveryAttempts': 66,
            'Rejects': 6,
        }

        stats = stats_to_list(self.stats_dict)
        actual = sum_stats(stats)

        self.assertEqual(actual, expected)
