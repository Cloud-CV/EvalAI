from .common import *  # noqa

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'evalai',
        'USER': '',
        'PASSWORD': '',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# E-Mail Settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Port number for the python-Memcached cache backend.
CACHES['default']['LOCATION'] = '127.0.0.1:11211' # noqa: ignore=F405