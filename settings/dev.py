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
        "USER": os.environ.get(  # noqa: ignore=F405
            "POSTGRES_USER", "postgres"
        ),  # noqa: ignore=F405
        "PASSWORD": os.environ.get(  # noqa: ignore=F405
            "POSTGRES_PASSWORD", "postgres"
        ),  # noqa: ignore=F405
        "HOST": os.environ.get(  # noqa: ignore=F405
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
THIRD_PARTY_APPS += [  # noqa: ignore=F405
    "django_dramatiq",
    "django_spaghetti",
    "autofixture",
    "debug_toolbar",
    "django_extensions",
    "silk",
]

INSTALLED_APPS = DEFAULT_APPS + OUR_APPS + THIRD_PARTY_APPS  # noqa

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

DRAMATIQ_BROKER = {
    "BROKER": "dramatiq_sqs.SQSBroker",
    "OPTIONS": {
        "endpoint_url": os.environ.get('AWS_SQS_ENDPOINT', 'http://127.0.0.1:9324'),  # noqa: ignore=F405
        "region_name": os.environ.get('AWS_SQS_REGION', 'us-east-1'),  # noqa: ignore=F405
        "aws_access_key_id": os.environ.get('AWS_ACCESS_KEY_ID', 'x'),  # noqa: ignore=F405
        "aws_secret_access_key": os.environ.get('AWS_SECRET_ACCESS_KEY', 'x'),  # noqa: ignore=F405
    },
    "NAMESPACE": "dramatiq_sqs_tests",
    "MIDDLEWARE": [
        "dramatiq.middleware.Prometheus",
        "dramatiq.middleware.AgeLimit",
        "dramatiq.middleware.TimeLimit",
        "dramatiq.middleware.Callbacks",
        "dramatiq.middleware.Retries",
        "django_dramatiq.middleware.AdminMiddleware",
        "django_dramatiq.middleware.DbConnectionsMiddleware",
    ],
}

# Defines which database should be used to persist Task objects when the
# AdminMiddleware is enabled.  The default value is "default"
DRAMATIQ_TASKS_DATABASE = "evalai"

# Prevents Datetime warning by showing errors
warnings.filterwarnings(
    "error",
    r"DateTimeField .* received a naive datetime",
    RuntimeWarning,
    r"django\.db\.models\.fields",
)
