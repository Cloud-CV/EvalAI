from .common import *  # noqa: ignore=F405

import os
import raven

DEBUG = False

ALLOWED_HOSTS = ["eval.ai"]

# Database
# https://docs.djangoproject.com/en/1.10.2/ref/settings/#databases

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = ("evalai.s3.amazonaws.com", "beta.eval.ai:9999")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": os.environ.get("RDS_DB_NAME"),
        "USER": os.environ.get("RDS_USERNAME"),
        "PASSWORD": os.environ.get("RDS_PASSWORD"),
        "HOST": os.environ.get("RDS_HOSTNAME"),
        "PORT": os.environ.get("RDS_PORT"),
    }
}

DATADOG_APP_NAME = "EvalAI"
DATADOG_APP_KEY = os.environ.get("DATADOG_APP_KEY")
DATADOG_API_KEY = os.environ.get("DATADOG_API_KEY")

MIDDLEWARE += ["middleware.metrics.DatadogMiddleware"]  # noqa

INSTALLED_APPS += ("storages", "raven.contrib.django.raven_compat")  # noqa

AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_SES_REGION_NAME = os.environ.get("AWS_SES_REGION_NAME")
AWS_SES_REGION_ENDPOINT = os.environ.get("AWS_SES_REGION_ENDPOINT")

# Amazon S3 Configurations
AWS_S3_CUSTOM_DOMAIN = "%s.s3.amazonaws.com" % AWS_STORAGE_BUCKET_NAME

# static files configuration on S3
STATICFILES_LOCATION = "static"
STATICFILES_STORAGE = "settings.custom_storages.StaticStorage"
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)

# Media files configuration on S3
MEDIAFILES_LOCATION = "media"
MEDIA_URL = "http://%s.s3.amazonaws.com/%s/" % (
    AWS_STORAGE_BUCKET_NAME,
    MEDIAFILES_LOCATION,
)
DEFAULT_FILE_STORAGE = "settings.custom_storages.MediaStorage"

# Setup Email Backend related settings
DEFAULT_FROM_EMAIL = "noreply@cloudcv.org"
EMAIL_BACKEND = "django_ses.SESBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")

# Hide API Docs on production environment
REST_FRAMEWORK_DOCS = {"HIDE_DOCS": True}

# Port number for the python-memcached cache backend.
CACHES["default"]["LOCATION"] = os.environ.get(  # noqa: ignore=F405
    "MEMCACHED_LOCATION"
)  # noqa: ignore=F405

RAVEN_CONFIG = {
    "dsn": os.environ.get("SENTRY_URL"),
    # If you are using git, you can also automatically configure the
    # release based on the git info.
    "release": raven.fetch_git_sha(os.path.dirname(os.pardir)),
}

# https://docs.djangoproject.com/en/1.10/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING["root"] = {  # noqa
    "level": "INFO",
    "handlers": ["console", "sentry", "logfile"],
}

LOGGING["handlers"]["sentry"] = {  # noqa
    "level": "ERROR",
    "class": "raven.contrib.django.raven_compat.handlers.SentryHandler",
    "tags": {"custom-tag": "x"},
}
