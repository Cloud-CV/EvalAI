from .common import *

import os

# Database
# https://docs.djangoproject.com/en/1.10.2/ref/settings/#databases

DEBUG = False

DATABASES = {    
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('RDS_NAME', ''),
        'USER' : os.environ.get('RDS_USER', ''),
        'PASSWORD' : os.environ.get('RDS_PASSWORD', ''),
        'HOST' : os.environ.get('RDS_HOST', ''),
        'PORT' : '5432',
    }
}

INSTALLED_APPS += ('storages',)

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID', '')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY', '')

# Amazon S3 Configurations
AWS_STORAGE_BUCKET_NAME = "evalai-static"

STATICFILES_STORAGE = 'custom_storages.StaticStorage'
STATICFILES_LOCATION = 'static'
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)

MEDIAFILES_LOCATION = 'media'
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = 'custom_storages.MediaStorage'
