#!/bin/sh
# Set uWSGI processes based on environment (staging: 1, production: 2)
if [ -z "$UWSGI_PROCESSES" ]; then
    # Default: 2 for production, 1 for staging (check via DJANGO_SETTINGS_MODULE or ENVIRONMENT)
    if [ "$DJANGO_SETTINGS_MODULE" = "settings.staging" ] || [ "${ENVIRONMENT:-}" = "staging" ]; then
        UWSGI_PROCESSES=1
    else
        UWSGI_PROCESSES=2
    fi
fi

python manage.py migrate --noinput  && \
python manage.py collectstatic --noinput  && \
uwsgi --ini /code/docker/prod/django/uwsgi.ini --processes ${UWSGI_PROCESSES}
