from .prod import *   # noqa: ignore=F405

ALLOWED_HOSTS = [
    'staging.evalai.cloudcv.org',
]

# Database
# https://docs.djangoproject.com/en/1.10.2/ref/settings/#databases

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = (
    'evalai.cloudcv.org',
    'staging-evalai.s3.amazonaws.com',
    'staging.evalai.cloudcv.org',
)
