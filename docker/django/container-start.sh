#!/bin/sh
cd /code && python manage.py migrate --noinput --settings=settings.dev && python manage.py collectstatic --noinput --settings=settings.dev
supervisord -n -c /etc/supervisor/supervisord.conf
