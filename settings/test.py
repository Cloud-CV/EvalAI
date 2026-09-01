from .common import *  # noqa  # pylint: disable=wildcard-import,unused-wildcard-import

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("POSTGRES_NAME", "evalai"),
        "USER": os.environ.get(
            "POSTGRES_USER", "postgres"
        ),
        "PASSWORD": os.environ.get(
            "POSTGRES_PASSWORD", "postgres"
        ),
        "HOST": os.environ.get(
            "POSTGRES_HOST", "localhost"
        ),
        "PORT": os.environ.get("POSTGRES_PORT", 5432),
    }
}

# E-Mail Settings
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"},
    "throttling": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"},
}

TEST = True

MEDIAFILES_LOCATION = "media"
