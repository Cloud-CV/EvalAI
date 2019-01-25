#!/bin/sh
cd /code && \
<<<<<<< HEAD
python manage.py migrate --noinput --settings=settings.dev && \
python manage.py seed --settings=settings.dev && \
python manage.py runserver 0.0.0.0:8000 --settings=settings.dev
=======
python manage.py migrate --noinput && \
python manage.py seed && \
python manage.py runserver 0.0.0.0:8000
>>>>>>> 98065e3257db0cd629bc64b959a29bae519b0bfe
