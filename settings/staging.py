from .prod import *   # noqa: ignore=F405

ALLOWED_HOSTS = [
    'staging-evalai.cloudcv.org',
]

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = (
    'staging-evalai.s3.amazonaws.com',
    'evalai-staging.cloudcv.org',
)
