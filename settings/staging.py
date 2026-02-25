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

AWS_SES_MESSAGE_TAGS = {"environment": "staging"}

CELERY_WORKER_MAX_TASKS_PER_CHILD = 100  # Recycle more frequently
CELERYD_PREFETCH_MULTIPLIER = 1
CELERY_TASK_SOFT_TIME_LIMIT = 40 * 60  # 40 minutes (shorter for staging)
CELERY_TASK_TIME_LIMIT = 50 * 60  # 50 minutes
