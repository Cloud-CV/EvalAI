from .prod import *  # noqa: ignore=F405

ALLOWED_HOSTS = ["staging.eval.ai"]

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = (
    "staging-evalai.s3.amazonaws.com",
    "evalai-staging.cloudcv.org",
    "staging-v2.eval.ai:9999",
)
