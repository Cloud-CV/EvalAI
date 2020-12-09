from .prod import *  # noqa: ignore=F405

ALLOWED_HOSTS = ["staging.eval.ai"]

CORS_ORIGIN_ALLOW_ALL = False

CORS_ORIGIN_WHITELIST = (
    "staging-evalai.s3.amazonaws.com",
    "staging.eval.ai",
    "beta-staging.eval.ai:9999",
)
