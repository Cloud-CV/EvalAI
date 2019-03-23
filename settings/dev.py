from .common import *  # noqa: ignore=F405

import warnings

# Database
# https://docs.djangoproject.com/en/1.10.2/ref/settings/#databases

DEBUG = True

ALLOWED_HOSTS = ["*"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("POSTGRES_NAME", "evalai"),  # noqa: ignore=F405
        "USER": os.environ.get(
            "POSTGRES_USER", "postgres"
        ),  # noqa: ignore=F405
        "PASSWORD": os.environ.get(
            "POSTGRES_PASSWORD", "postgres"
        ),  # noqa: ignore=F405
        "HOST": os.environ.get(
            "POSTGRES_HOST", "localhost"
        ),  # noqa: ignore=F405
        "PORT": os.environ.get("POSTGRES_PORT", 5432),  # noqa: ignore=F405
    }
}

# E-Mail Settings
EMAIL_HOST = "localhost"
EMAIL_PORT = 1025
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

ACCOUNT_DEFAULT_HTTP_PROTOCOL = "http"

# DJANGO-SPAGHETTI-AND-MEATBALLS SETTINGS
INSTALLED_APPS += [  # noqa: ignore=F405
    "django_spaghetti",
    "autofixture",
    "debug_toolbar",
    "django_extensions",
    "silk",
]

SPAGHETTI_SAUCE = {
    "apps": [
        "auth",
        "accounts",
        "analytics",
        "base",
        "challenges",
        "hosts",
        "jobs",
        "participants",
        "web",
    ],
    "show_fields": True,
}

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
}

MEDIA_URL = "/media/"

MIDDLEWARE += [  # noqa: ignore=F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "silk.middleware.SilkyMiddleware",
]

SILKY_PYTHON_PROFILER = True

# Prevents Datetime warning by showing errors
warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)
