import copy

from django.core.management import call_command
from django.test import TestCase

from django_ses.models import SESStat

from boto.ses import SESConnection


data_points = [
    {
        'Complaints': '1',
        'Timestamp': '2012-01-01T02:00:00Z',
        'DeliveryAttempts': '2',
        'Bounces': '3',
        'Rejects': '4'
    },
    {
        'Complaints': '1',
        'Timestamp': '2012-01-03T02:00:00Z',
        'DeliveryAttempts': '2',
        'Bounces': '3',
        'Rejects': '4'
    },
    {
        'Complaints': '1',
        'Timestamp': '2012-01-03T03:00:00Z',
        'DeliveryAttempts': '2',
        'Bounces': '3',
        'Rejects': '4'
    }
]


def fake_get_statistics(self):
    return {
        'GetSendStatisticsResponse': {
            'GetSendStatisticsResult': {
                'SendDataPoints': data_points
            },
            'ResponseMetadata': {
                'RequestId': '1'
            }
        }
    }


def fake_connection_init(self, *args, **kwargs):
    pass


class SESCommandTest(TestCase):

    def setUp(self):
        SESConnection.get_send_statistics = fake_get_statistics
        SESConnection.__init__ = fake_connection_init

    def test_get_statistics(self):
        # Test the get_ses_statistics management command
        call_command('get_ses_statistics')

        # Test that days with a single data point is saved properly
        stat = SESStat.objects.get(date='2012-01-01')
        self.assertEqual(stat.complaints, 1)
        self.assertEqual(stat.delivery_attempts, 2)
        self.assertEqual(stat.bounces, 3)
        self.assertEqual(stat.rejects, 4)

        # Test that days with multiple data points get saved properly
        stat = SESStat.objects.get(date='2012-01-03')
        self.assertEqual(stat.complaints, 2)
        self.assertEqual(stat.delivery_attempts, 4)
        self.assertEqual(stat.bounces, 6)
        self.assertEqual(stat.rejects, 8)

        # Changing data points should update database records too
        data_points_copy = copy.deepcopy(data_points)
        data_points_copy[0]['Complaints'] = '2'
        data_points_copy[0]['DeliveryAttempts'] = '3'
        data_points_copy[0]['Bounces'] = '4'
        data_points_copy[0]['Rejects'] = '5'

        def fake_get_statistics_copy(self):
            return {
                'GetSendStatisticsResponse': {
                    'GetSendStatisticsResult': {
                        'SendDataPoints': data_points_copy
                    },
                    'ResponseMetadata': {
                        'RequestId': '1'
                    }
                }
            }
        SESConnection.get_send_statistics = fake_get_statistics_copy
        call_command('get_ses_statistics')
        stat = SESStat.objects.get(date='2012-01-01')
        self.assertEqual(stat.complaints, 2)
        self.assertEqual(stat.delivery_attempts, 3)
        self.assertEqual(stat.bounces, 4)
        self.assertEqual(stat.rejects, 5)
