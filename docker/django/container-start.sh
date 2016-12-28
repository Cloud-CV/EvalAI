#!/bin/sh
cd /code && python manage.py migrate --noinput && python manage.py collectstatic --noinput
supervisord -n -c /etc/supervisor/supervisord.conf
