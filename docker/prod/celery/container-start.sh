#!/bin/sh
# Celery worker with optimized settings for small EC2 instances
# Settings are configurable via environment variables with sensible defaults
# Defaults: Production (t3.medium / 4GB) - concurrency=2, max-memory=600MB
# Override via: CELERY_CONCURRENCY, CELERY_MAX_MEMORY_PER_CHILD, CELERY_MAX_TASKS_PER_CHILD

# Set defaults based on environment (staging uses smaller defaults)
if [ -z "$CELERY_CONCURRENCY" ]; then
    # Default: 2 for production, 1 for staging (check via DJANGO_SETTINGS_MODULE or ENVIRONMENT)
    if [ "$DJANGO_SETTINGS_MODULE" = "settings.staging" ] || [ "${ENVIRONMENT:-}" = "staging" ]; then
        CELERY_CONCURRENCY=1
    else
        CELERY_CONCURRENCY=2
    fi
fi

if [ -z "$CELERY_MAX_MEMORY_PER_CHILD" ]; then
    # Default: 600MB for production, 350MB for staging
    if [ "$DJANGO_SETTINGS_MODULE" = "settings.staging" ] || [ "${ENVIRONMENT:-}" = "staging" ]; then
        CELERY_MAX_MEMORY_PER_CHILD=350000
    else
        CELERY_MAX_MEMORY_PER_CHILD=600000
    fi
fi

if [ -z "$CELERY_MAX_TASKS_PER_CHILD" ]; then
    # Default: 200 for production, 100 for staging
    if [ "$DJANGO_SETTINGS_MODULE" = "settings.staging" ] || [ "${ENVIRONMENT:-}" = "staging" ]; then
        CELERY_MAX_TASKS_PER_CHILD=100
    else
        CELERY_MAX_TASKS_PER_CHILD=200
    fi
fi

cd /code && \
celery -A evalai worker \
    --loglevel=INFO \
    --concurrency=${CELERY_CONCURRENCY} \
    --prefetch-multiplier=1 \
    --max-tasks-per-child=${CELERY_MAX_TASKS_PER_CHILD} \
    --max-memory-per-child=${CELERY_MAX_MEMORY_PER_CHILD}
