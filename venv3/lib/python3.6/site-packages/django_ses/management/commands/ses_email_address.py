#!/usr/bin/env python
# encoding: utf-8
from optparse import make_option

from boto.regioninfo import RegionInfo
from boto.ses import SESConnection

from django.core.management.base import BaseCommand

from django_ses import settings


def _add_options(target):
    return (
        target(
            '-a',
            '--add',
            dest='add',
            default=False,
            help="""Adds an email to your verified email address list.
                    This action causes a confirmation email message to be
                    sent to the specified address."""
        ),
        target(
            '-d',
            '--delete',
            dest='delete',
            default=False,
            help='Removes an email from your verified emails list'
        ),
        target(
            '-l',
            '--list',
            dest='list',
            default=False,
            action='store_true',
            help='Outputs all verified emails'
        )
    )


class Command(BaseCommand):
    """Verify, delete or list SES email addresses"""

    if hasattr(BaseCommand, 'option_list'):
        # Django < 1.10
        option_list = BaseCommand.option_list + _add_options(make_option)
    else:
        # Django >= 1.10
        def add_arguments(self, parser):
            _add_options(parser.add_argument)

    def handle(self, *args, **options):

        verbosity = options.get('verbosity', 0)
        add_email = options.get('add', False)
        delete_email = options.get('delete', False)
        list_emails = options.get('list', False)

        access_key_id = settings.ACCESS_KEY
        access_key = settings.SECRET_KEY
        region = RegionInfo(
            name=settings.AWS_SES_REGION_NAME,
            endpoint=settings.AWS_SES_REGION_ENDPOINT)
        proxy = settings.AWS_SES_PROXY
        proxy_port = settings.AWS_SES_PROXY_PORT
        proxy_user = settings.AWS_SES_PROXY_USER
        proxy_pass = settings.AWS_SES_PROXY_PASS


        connection = SESConnection(
                aws_access_key_id=access_key_id,
                aws_secret_access_key=access_key,
                region=region,
                proxy=proxy,
                proxy_port=proxy_port,
                proxy_user=proxy_user,
                proxy_pass=proxy_pass,
        )

        if add_email:
            if verbosity != '0':
                print("Adding email: " + add_email)
            connection.verify_email_address(add_email)
        elif delete_email:
            if verbosity != '0':
                print("Removing email: " + delete_email)
            connection.delete_verified_email_address(delete_email)
        elif list_emails:
            if verbosity != '0':
                print("Fetching list of verified emails:")
            response = connection.list_verified_email_addresses()
            emails = response['ListVerifiedEmailAddressesResponse'][
                'ListVerifiedEmailAddressesResult']['VerifiedEmailAddresses']
            for email in emails:
                print(email)
