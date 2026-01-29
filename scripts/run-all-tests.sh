#!/usr/bin/env bash
# Run both frontend and backend test suites (Docker).
# Usage: ./scripts/run-all-tests.sh

set -e

echo "=== Running frontend tests ==="
docker exec evalai-nodejs-1 npm test -- --single-run

echo ""
echo "=== Running backend tests ==="
docker exec -e DJANGO_SETTINGS_MODULE=settings.test evalai-django-1 bash -c '
  python manage.py flush --noinput
  pytest --cov . --cov-config .coveragerc -q
'

echo ""
echo "=== All tests finished ==="
