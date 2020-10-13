from .prod import *  # noqa: ignore=F405

ALLOWED_HOSTS = ["evalai-staging.cloudcv.org"]

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = (
    "staging-evalai.s3.amazonaws.com",
    "evalai-staging.cloudcv.org",
    "evalai-staging-v2.cloudcv.org:9999",
)
