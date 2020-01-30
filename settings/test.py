from .common import *  # noqa

DEBUG = False

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
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.dummy.DummyCache"}
}

THIRD_PARTY_APPS += ["django_dramatiq"]
INSTALLED_APPS = DEFAULT_APPS + THIRD_PARTY_APPS + OUR_APPS

DRAMATIQ_BROKER = {
    "BROKER": "dramatiq_sqs.SQSBroker",
    "OPTIONS": {
        "endpoint_url": os.environ.get("AWS_SQS_ENDPOINT_URL", "http://localhost:9324"),
        "region_name": os.environ.get("AWS_DEFAULT_REGION", "elasticmq"),
        "aws_access_key_id": os.environ.get("AWS_ACCESS_KEY_ID", "x"),
        "aws_secret_access_key": os.environ.get("AWS_SECRET_ACCESS_KEY", "x"),
    },
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

TEST = True
