#!/bin/bash
# SessionStart hook for Claude Code cloud sessions: starts Docker and brings up
# the dev stack (db, sqs, django, nodejs) so tests and linters can run.
# Idempotent: on later runs the image builds are cached and `up -d` is a no-op.
set -euo pipefail

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

REPO="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "$0")/../.." && pwd)}"
CA_BUNDLE="${CCR_CA_BUNDLE:-/root/.ccr/ca-bundle.crt}"
GEN_DIR="${HOME}/.cache/evalai-docker"
LOG=/tmp/evalai-session-start.log
: >"$LOG"

fail() {
  echo "EvalAI session setup failed while $1. Full log: $LOG" >&2
  tail -40 "$LOG" >&2
  exit 2
}

cd "$REPO"

# Docker daemon with the fuse-overlayfs storage driver (see AGENTS.md).
if ! command -v fuse-overlayfs >/dev/null 2>&1; then
  { apt-get update -q && apt-get install -y -q fuse-overlayfs iptables; } >>"$LOG" 2>&1 ||
    fail "installing fuse-overlayfs"
fi
# setsid keeps the dockerd that install.sh backgrounds alive after this hook exits.
setsid --wait bash cloud-agent/install.sh >>"$LOG" 2>&1 || fail "starting Docker"

# Builds must trust the egress proxy CA when the session has one.
compose_files="$REPO/docker-compose.yml"
if [ -f "$CA_BUNDLE" ]; then
  bash .claude/hooks/docker-proxy-ca.sh "$REPO" "$GEN_DIR" "$CA_BUNDLE" >>"$LOG" 2>&1 ||
    fail "generating proxy CA build files"
  compose_files="$compose_files:$GEN_DIR/docker-compose.proxy-ca.yml"
fi
export COMPOSE_FILE="$compose_files"
export COMPOSE_PROJECT_NAME=evalai
if [ -n "${CLAUDE_ENV_FILE:-}" ]; then
  for line in "export COMPOSE_FILE=\"$COMPOSE_FILE\"" "export COMPOSE_PROJECT_NAME=$COMPOSE_PROJECT_NAME"; do
    grep -qxF "$line" "$CLAUDE_ENV_FILE" 2>/dev/null || echo "$line" >>"$CLAUDE_ENV_FILE"
  done
fi

docker compose build django nodejs >>"$LOG" 2>&1 || fail "building images"
docker compose up -d db sqs django nodejs >>"$LOG" 2>&1 || fail "starting services"

# Django runs migrations and the seed before serving.
django_state="not answering yet (check: docker logs evalai-django-1)"
for _ in $(seq 1 60); do
  if curl -fs -o /dev/null -m 5 http://localhost:8000/api/challenges/challenge/present/all/all; then
    django_state="ready"
    break
  fi
  sleep 5
done

cat <<EOF
EvalAI dev stack is up (compose project "evalai"; COMPOSE_FILE is set, so plain
\`docker compose\` includes the proxy CA override).
- Containers: evalai-db-1, evalai-sqs-1, evalai-django-1, evalai-nodejs-1
- Django http://localhost:8000: $django_state; frontend http://localhost:8888
- Logins: admin / host / participant_0, password "password"
- Backend tests (CI-style; wipes the dev DB, re-seed with
  \`docker exec evalai-django-1 python manage.py seed\`):
  docker compose run --rm --no-deps -e DJANGO_SETTINGS_MODULE=settings.test django bash -c 'python manage.py flush --noinput && pytest -q'
- Frontend tests: docker exec evalai-nodejs-1 bash -c 'Xvfb :99 -screen 0 1024x768x24 &>/dev/null & sleep 1 && npm test -- --single-run'
- Backend lint: docker exec evalai-django-1 bash -c 'cd /code && python -m ruff check --no-fix apps/ && python -m ruff format --check apps/'
Setup log: $LOG
EOF
