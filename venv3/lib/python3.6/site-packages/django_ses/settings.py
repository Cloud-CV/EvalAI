from django.conf import settings
from boto.ses import SESConnection

__all__ = ('ACCESS_KEY', 'SECRET_KEY', 'AWS_SES_REGION_NAME',
        'AWS_SES_REGION_ENDPOINT', 'AWS_SES_AUTO_THROTTLE',
        'AWS_SES_RETURN_PATH', 'DKIM_DOMAIN', 'DKIM_PRIVATE_KEY',
        'DKIM_SELECTOR', 'DKIM_HEADERS', 'TIME_ZONE')

ACCESS_KEY = getattr(settings, 'AWS_SES_ACCESS_KEY_ID',
    getattr(settings, 'AWS_ACCESS_KEY_ID', None))

SECRET_KEY = getattr(settings, 'AWS_SES_SECRET_ACCESS_KEY',
    getattr(settings, 'AWS_SECRET_ACCESS_KEY', None))

AWS_SES_REGION_NAME = getattr(settings, 'AWS_SES_REGION_NAME',
    SESConnection.DefaultRegionName),
AWS_SES_REGION_ENDPOINT = getattr(settings, 'AWS_SES_REGION_ENDPOINT',
    SESConnection.DefaultRegionEndpoint)

AWS_SES_AUTO_THROTTLE = getattr(settings, 'AWS_SES_AUTO_THROTTLE', 0.5)
AWS_SES_RETURN_PATH = getattr(settings, 'AWS_SES_RETURN_PATH', None)
AWS_SES_PROXY = getattr(settings, 'AWS_SES_PROXY', None)
AWS_SES_PROXY_PORT = getattr(settings, 'AWS_SES_PROXY_PORT', None)
AWS_SES_PROXY_USER = getattr(settings, 'AWS_SES_PROXY_USER', None)
AWS_SES_PROXY_PASS = getattr(settings, 'AWS_SES_PROXY_PASS', None)
AWS_SES_CONFIGURATION_SET= getattr(settings, 'AWS_SES_CONFIGURATION_SET', None)

DKIM_DOMAIN = getattr(settings, "DKIM_DOMAIN", None)
DKIM_PRIVATE_KEY = getattr(settings, 'DKIM_PRIVATE_KEY', None)
DKIM_SELECTOR = getattr(settings, 'DKIM_SELECTOR', 'ses')
DKIM_HEADERS = getattr(settings, 'DKIM_HEADERS',
                        ('From', 'To', 'Cc', 'Subject'))

TIME_ZONE = settings.TIME_ZONE

VERIFY_BOUNCE_SIGNATURES = getattr(settings, 'AWS_SES_VERIFY_BOUNCE_SIGNATURES', True)

# Domains that are trusted when retrieving the certificate
# used to sign bounce messages.
BOUNCE_CERT_DOMAINS = getattr(settings, 'AWS_SNS_BOUNCE_CERT_TRUSTED_DOMAINS', (
    'amazonaws.com',
    'amazon.com',
))
