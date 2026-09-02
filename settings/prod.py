import os

import sentry_sdk
from django.core.exceptions import ImproperlyConfigured
from sentry_sdk.integrations.django import DjangoIntegration

from .common import *  # noqa: F403  # pylint: disable=wildcard-import,unused-wildcard-import

_INSECURE_SECRET_KEYS = {"", "random_secret_key", "some-secret-key"}
if (
    not SECRET_KEY  # noqa: F405
    or str(SECRET_KEY).strip() in _INSECURE_SECRET_KEYS  # noqa: F405
):
    raise ImproperlyConfigured(
        "SECRET_KEY must be set to a unique value in production."
    )


def _sentry_before_send(event, hint):
    """Drop noise before it becomes a Sentry issue.

    1. OSError write/broken-pipe errors - harmless client disconnects.
    2. Log records emitted by challenge evaluation scripts. The submission
       worker imports and runs host-uploaded scripts in-process under the
       ``challenge_data.challenge_<id>`` logger namespace, so any
       ``logger.error(...)`` a challenge host leaves in their code would
       otherwise surface as a high-priority EvalAI issue we cannot fix.
       Genuine evaluate() failures still reach Sentry via the worker's own
       ``logger.exception(...)`` wrappers and the ``evaluation_module_error``
       field on the Challenge.
    """
    if str(event.get("logger", "")).startswith("challenge_data"):
        return None

    exc_info = hint.get("exc_info")
    if exc_info:
        exc_type, exc_value = exc_info[0], exc_info[1]
        if exc_type is OSError:
            message = str(exc_value).lower()
            if "write error" in message or "broken pipe" in message:
                return None
    return event


DEBUG = False

ALLOWED_HOSTS = ["eval.ai"]

# Database
# https://docs.djangoproject.com/en/1.10.2/ref/settings/#databases

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = (
    "https://evalai.s3.amazonaws.com",
    "https://eval.ai",
    "http://beta.eval.ai:9999",
)

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

INSTALLED_APPS += ("storages",)  # noqa

AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_SES_REGION_NAME = os.environ.get("AWS_SES_REGION_NAME")
AWS_SES_REGION_ENDPOINT = os.environ.get("AWS_SES_REGION_ENDPOINT")
AWS_SES_CONFIGURATION_SET = os.environ.get("AWS_SES_CONFIGURATION_SET")
AWS_SES_MESSAGE_TAGS = {"environment": "production"}

# Amazon S3 Configurations
# django-storages builds every media and static URL from this, so setting it
# to a CloudFront domain moves all asset traffic onto the CDN without
# touching the stored file paths. Leaving it unset keeps the bucket as the
# origin, which makes rolling the CDN back a config change rather than a
# deploy.
# An empty value counts as unset: clearing the variable in an env file is
# written `AWS_S3_CUSTOM_DOMAIN=`, which is an empty string rather than an
# absent key, and that is exactly how the CDN gets rolled back. Taking it
# literally would build "https:///static/" and break every asset.
AWS_S3_CUSTOM_DOMAIN = (
    os.environ.get("AWS_S3_CUSTOM_DOMAIN", "").strip()
    or "%s.s3.amazonaws.com" % AWS_STORAGE_BUCKET_NAME
)

# static files configuration on S3
STATICFILES_LOCATION = "static"
STATICFILES_STORAGE = "settings.custom_storages.StaticStorage"
STATIC_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, STATICFILES_LOCATION)

# Media files configuration on S3
# Derived from the same domain as STATIC_URL so the two cannot drift apart
# and serve half the assets from the CDN and half straight from S3.
MEDIAFILES_LOCATION = "media"
MEDIA_URL = "https://%s/%s/" % (AWS_S3_CUSTOM_DOMAIN, MEDIAFILES_LOCATION)
DEFAULT_FILE_STORAGE = "settings.custom_storages.MediaStorage"

# Setup Email Backend related settings
EMAIL_BACKEND = "django_ses.SESBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD")
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER")
EMAIL_PORT = os.environ.get("EMAIL_PORT")
EMAIL_USE_TLS = os.environ.get("EMAIL_USE_TLS")

# Hide API Docs on production environment
REST_FRAMEWORK_DOCS = {"HIDE_DOCS": True}

# Port number for the python-memcached cache backend.
CACHES["default"]["LOCATION"] = os.environ.get(  # noqa: F405
    "MEMCACHED_LOCATION"
)

# Initialize Sentry SDK
sentry_sdk.init(
    dsn=os.environ.get("SENTRY_URL"),
    integrations=[DjangoIntegration()],
    before_send=_sentry_before_send,
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for
    # performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
    profiles_sample_rate=1.0,
    send_default_pii=True,
    environment=os.environ.get("ENVIRONMENT"),
)

# https://docs.djangoproject.com/en/1.10/ref/settings/#secure-proxy-ssl-header
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

LOGGING["root"] = {  # noqa
    "level": "INFO",
    "handlers": ["console", "logfile"],
}

CELERY_WORKER_MAX_TASKS_PER_CHILD = 200
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = 50 * 60  # 50 minutes
CELERY_TASK_TIME_LIMIT = 60 * 60  # 60 minutes
