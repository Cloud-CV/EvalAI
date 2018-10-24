from .common import *  # noqa

DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get("POSTGRES_NAME", 'evalai'),  # noqa: ignore=F405
        'USER': os.environ.get("POSTGRES_USER", 'postgres'),  # noqa: ignore=F405
        'PASSWORD': os.environ.get("POSTGRES_PASSWORD", 'postgres'),  # noqa: ignore=F405
        'HOST': os.environ.get("POSTGRES_HOST", 'localhost'),  # noqa: ignore=F405
        'PORT': os.environ.get("POSTGRES_PORT", 5432),  # noqa: ignore=F405
    }
}

# E-Mail Settings
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

TEST = True
