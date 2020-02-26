#!/bin/sh
cd /code && \
celery -A evalai worker --loglevel=INFO
