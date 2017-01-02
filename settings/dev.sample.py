from .common import *  # noqa: ignore=F405

# Database
# https://docs.djangoproject.com/en/1.10.2/ref/settings/#databases

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'HOST': 'db',
        'PORT': 5432,
    }
}

# E-Mail Settings
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

# DJANGO-SPAGHETTI-AND-MEATBALLS SETTINGS
INSTALLED_APPS += [ # noqa: ignore=F405
    'django_spaghetti',
    'autofixture'
]

SPAGHETTI_SAUCE = {
    'apps': ['auth', 'accounts', 'analytics', 'base', 'challenges', 'hosts', 'jobs', 'participants', 'web'],
    'show_fields': True,
}

# Port number for the python-Memcached cache backend.
CACHES['default']['LOCATION'] = '127.0.0.1:11211' # noqa: ignore=F405
