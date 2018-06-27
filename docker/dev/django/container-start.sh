#!/bin/sh
cd /code && \
python manage.py migrate --noinput --settings=settings.dev && \
python manage.py seed --settings=settings.dev && \
python manage.py runserver 0.0.0.0:8000 --settings=settings.dev
