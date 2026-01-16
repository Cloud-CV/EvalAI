from .prod import *  # noqa: ignore=F405  # pylint: disable=wildcard-import,unused-wildcard-import

ALLOWED_HOSTS = ["staging.eval.ai", "monitoring-staging.eval.ai"]

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = (
    "https://evalai.s3.amazonaws.com",
    "https://staging-evalai.s3.amazonaws.com",
    "https://staging.eval.ai",
    "https://monitoring-staging.eval.ai",
    "https://monitoring.eval.ai",
)

# Security headers inherited from prod.py
# SECURE_SSL_REDIRECT, SESSION_COOKIE_SECURE, CSRF_COOKIE_SECURE, etc.
# are all set in prod.py and apply here as well
