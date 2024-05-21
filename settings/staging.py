from .prod import *  # noqa: ignore=F405

ALLOWED_HOSTS = ["*"]

CORS_ORIGIN_ALLOW_ALL = True

CORS_ORIGIN_WHITELIST = (
    "https://evalai.s3.amazonaws.com",
    "https://staging-evalai.s3.amazonaws.com",
    "https://staging.eval.ai",
    "https://monitoring-staging.eval.ai",
    "https://monitoring.eval.ai",
)
