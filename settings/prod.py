from .common import *  # noqa
from settings import custom_storages

import os


DEBUG = True

ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/1.10.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('RDS_DB_NAME', ""),
        'USER': os.environ.get('RDS_USERNAME', ""),
        'PASSWORD': os.environ.get('RDS_PASSWORD', ""),
        'HOST': os.environ.get('RDS_HOSTNAME', ""),
        'PORT': os.environ.get('RDS_PORT', ""),
    }
}

INSTALLED_APPS += ('storages',)  # noqa

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')

# Amazon S3 Configurations
AWS_STORAGE_BUCKET_NAME = "evalai-static"
STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
S3_URL = 'http://%s.s3.amazonaws.com/' % AWS_STORAGE_BUCKET_NAME
STATIC_URL = S3_URL
MEDIAFILES_LOCATION = 'media'
MEDIA_URL = 'http://%s.s3.amazonaws.com/%s/' % (AWS_STORAGE_BUCKET_NAME, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'

# Setup Email Bacend related settings
DEFAULT_FROM_EMAIL = "noreply@cloudcv.org"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_PORT = os.environ.get("EMAIL_PORT", "")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS", "")
