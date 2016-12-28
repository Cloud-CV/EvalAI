#!/bin/sh
cd /code && python manage.py migrate --noinput && python manage.py collectstatic --noinput
supervisord -n -c /etc/supervisor/supervisord.conf

# Next line commented since we are not going to use websockets for V1
# cd /code && daphne -b 0.0.0.0 -p 8001 evalai.asgi:channel_layer
