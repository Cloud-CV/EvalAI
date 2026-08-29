#!/bin/sh
# Set uWSGI processes based on environment (staging: 1, production: 2)
if [ -z "$UWSGI_PROCESSES" ]; then
    # Default: 2 for production, 1 for staging (check via DJANGO_SETTINGS_MODULE or ENVIRONMENT)
    if [ "$DJANGO_SETTINGS_MODULE" = "settings.staging" ] || [ "${ENVIRONMENT:-}" = "staging" ]; then
        UWSGI_PROCESSES=1
    else
        UWSGI_PROCESSES=3
    fi
fi

# No migrate/collectstatic here on purpose. Both are release steps that must
# run exactly once per deploy, not once per container: two containers booting
# together race on CREATE TABLE (pg_type_typname_nsp_index), and collectstatic
# uploads to S3, so every extra container repeats the same upload. The deploy
# pipeline runs them as one-off tasks before starting the service -- see the
# prepare-release operation in scripts/deployment/deploy.sh. This is also what
# lets the service run more than one container at a time.
if [ "$UWSGI_PROCESSES" -eq 1 ]; then
    # Don't use cheaper autoscaling when only 1 process (cheaper must be < processes)
    uwsgi --ini /code/docker/prod/django/uwsgi.ini --processes ${UWSGI_PROCESSES}
else
    # Enable cheaper autoscaling when multiple processes available
    uwsgi --ini /code/docker/prod/django/uwsgi.ini --processes ${UWSGI_PROCESSES} \
        --cheaper 1 --cheaper-initial 1 --cheaper-step 1 \
        --cheaper-overload 10 --cheaper-algo spare
fi
