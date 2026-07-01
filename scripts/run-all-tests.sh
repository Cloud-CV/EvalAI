#!/usr/bin/env bash
# Run both frontend and backend test suites (Docker).
# Usage: ./scripts/run-all-tests.sh
#
# Auto-detects container names:
#   - workspace-* (Cloud Agent VMs, default compose project name)
#   - evalai-*    (local dev with COMPOSE_PROJECT_NAME=evalai)

set -e

detect_container() {
  local suffix="$1"
  if docker ps --format '{{.Names}}' | grep -qx "workspace-${suffix}"; then
    echo "workspace-${suffix}"
  elif docker ps --format '{{.Names}}' | grep -qx "evalai-${suffix}"; then
    echo "evalai-${suffix}"
  else
    echo "Error: Could not find ${suffix} container (expected workspace-${suffix} or evalai-${suffix})" >&2
    exit 1
  fi
}

NODEJS_CONTAINER="$(detect_container nodejs-1)"
DJANGO_CONTAINER="$(detect_container django-1)"

echo "Using containers: ${NODEJS_CONTAINER}, ${DJANGO_CONTAINER}"
echo ""
echo "=== Running frontend tests ==="
docker exec "${NODEJS_CONTAINER}" bash -c 'Xvfb :99 -screen 0 1024x768x24 &>/dev/null & sleep 1 && npm test -- --single-run'

echo ""
echo "=== Running backend tests ==="
docker exec -e DJANGO_SETTINGS_MODULE=settings.test "${DJANGO_CONTAINER}" bash -c '
  python manage.py flush --noinput
  pytest --cov . --cov-config .coveragerc -q
'

echo ""
echo "=== All tests finished ==="
