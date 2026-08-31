#!/usr/bin/env bash
# SessionStart hook for Claude Code on the web.
#
# EvalAI normally runs through docker-compose, but the Docker daemon is not
# available in Claude Code on the web containers. This provisions the same
# stack natively so tests and linters work in a web session:
#
#   * Python 3.9 (matches PYTHON_RUNTIME_VERSION in .github/workflows/ci-cd.yml)
#     in a virtualenv outside the repo, with requirements/dev.txt installed.
#   * A local PostgreSQL server, since settings/test.py expects one on
#     localhost:5432.
#   * Node dependencies for the frontend linter.
#
# Runs only on the web; local Docker workflows in AGENTS.md are untouched.

set -euo pipefail

[ "${CLAUDE_CODE_REMOTE:-}" = "true" ] || exit 0

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
VENV_DIR="/opt/evalai-venv"
PYTHON_VERSION="3.9"
LOG_FILE="${TMPDIR:-/tmp}/evalai-session-start.log"

POSTGRES_DB_NAME="evalai"
POSTGRES_DB_USER="postgres"
POSTGRES_DB_PASSWORD="postgres"

: >"$LOG_FILE"

# Keep the transcript short: full output goes to $LOG_FILE, only step results
# are printed, since a SessionStart hook's stdout is added to the context.
run() {
  if ! "$@" >>"$LOG_FILE" 2>&1; then
    return 1
  fi
}

note() { printf '  %s\n' "$*"; }

if [ "$(id -u)" -eq 0 ]; then
  as_root() { "$@"; }
  as_postgres() { su postgres -c "$1"; }
else
  as_root() { sudo "$@"; }
  as_postgres() { sudo -u postgres bash -c "$1"; }
fi

echo "EvalAI environment setup (log: $LOG_FILE)"

# ---------------------------------------------------------------------------
# 1. System packages
# ---------------------------------------------------------------------------
# Build headers for the pinned C extensions in requirements/common.txt
# (psycopg2, Pillow, pycurl), mirroring docker/dev/django/Dockerfile.
# Headers may sit directly under /usr/include or in a multiarch subdirectory,
# so probe both rather than re-running apt on every session.
have_header() {
  if [ -f "/usr/include/$1" ]; then
    return 0
  fi
  local include_dir
  for include_dir in /usr/include/*/; do
    if [ -f "${include_dir}$1" ]; then
      return 0
    fi
  done
  return 1
}

missing_system_packages=()
command -v pg_config >/dev/null 2>&1 || missing_system_packages+=(libpq-dev)
have_header jpeglib.h || missing_system_packages+=(libjpeg-dev)
have_header zlib.h || missing_system_packages+=(zlib1g-dev)
have_header curl/curl.h || missing_system_packages+=(libcurl4-openssl-dev libssl-dev)
command -v cc >/dev/null 2>&1 || missing_system_packages+=(build-essential)
command -v pg_ctlcluster >/dev/null 2>&1 || missing_system_packages+=(postgresql)

if [ "${#missing_system_packages[@]}" -gt 0 ]; then
  # apt-get update warns about PPAs the egress policy blocks; that is not fatal
  # because every package needed here comes from the Ubuntu archive.
  export DEBIAN_FRONTEND=noninteractive
  as_root apt-get update -qq >>"$LOG_FILE" 2>&1 || true
  if run as_root apt-get install -y -qq --no-install-recommends \
      "${missing_system_packages[@]}"; then
    note "system packages: installed ${missing_system_packages[*]}"
  else
    note "system packages: FAILED (see $LOG_FILE)"
    exit 1
  fi
else
  note "system packages: already present"
fi

# ---------------------------------------------------------------------------
# 2. Python 3.9 virtualenv
# ---------------------------------------------------------------------------
UV_BIN="$(command -v uv || true)"
if [ -z "$UV_BIN" ] && [ -x "$HOME/.local/bin/uv" ]; then
  UV_BIN="$HOME/.local/bin/uv"
fi
if [ -z "$UV_BIN" ]; then
  note "uv: NOT FOUND — cannot provision Python $PYTHON_VERSION"
  exit 1
fi

# The Ubuntu archive has no Python 3.9 and the deadsnakes PPA is blocked by the
# egress policy, so uv's standalone build is what pins us to the CI runtime.
run "$UV_BIN" python install "$PYTHON_VERSION" || true

if [ ! -x "$VENV_DIR/bin/python" ]; then
  if run "$UV_BIN" venv --python "$PYTHON_VERSION" "$VENV_DIR"; then
    note "virtualenv: created at $VENV_DIR"
  else
    note "virtualenv: FAILED (see $LOG_FILE)"
    exit 1
  fi
else
  note "virtualenv: reusing $VENV_DIR"
fi

# requirements/*.txt pin 2020-era releases whose setup.py still imports
# setuptools.convert_path, removed in setuptools 81. Constrain the build
# backend rather than editing the pins.
BUILD_CONSTRAINTS="$(mktemp)"
trap 'rm -f "$BUILD_CONSTRAINTS"' EXIT
printf 'setuptools<70\nwheel<0.46\n' >"$BUILD_CONSTRAINTS"

if run "$UV_BIN" pip install --python "$VENV_DIR/bin/python" \
    --build-constraints "$BUILD_CONSTRAINTS" -r "$PROJECT_DIR/requirements/dev.txt"; then
  note "python deps: requirements/dev.txt installed"
else
  note "python deps: FAILED (see $LOG_FILE)"
  exit 1
fi

# moto and django-silk import pkg_resources, which uv does not seed into a
# virtualenv; setuptools 81 drops it, hence the ceiling.
run "$UV_BIN" pip install --python "$VENV_DIR/bin/python" "setuptools<81" wheel \
  || note "python deps: WARNING could not install setuptools/wheel"

# Versions pinned to the code_quality job in .github/workflows/ci-cd.yml so
# local lint results match CI. flake8 and pylint are not in requirements/dev.txt.
if run "$UV_BIN" pip install --python "$VENV_DIR/bin/python" \
    "black==24.8.0" "flake8==7.1.2" "pylint==3.3.6" "isort==5.12.0"; then
  note "lint tools: black/flake8/pylint/isort pinned to CI versions"
else
  note "lint tools: WARNING install failed (see $LOG_FILE)"
fi

# ---------------------------------------------------------------------------
# 3. PostgreSQL
# ---------------------------------------------------------------------------
# settings/test.py talks to localhost:5432; docker-compose's `db` service is
# not reachable without a Docker daemon.
# Running backend tests is the main thing this hook exists to enable, so every
# step below is a hard failure. Warning and carrying on would report a ready
# session and leave each test to fail later with a connection error.
pg_cluster_version="$(ls /usr/lib/postgresql 2>/dev/null | sort -V | tail -1 || true)"
if [ -z "$pg_cluster_version" ]; then
  note "postgres: FAILED — no server found under /usr/lib/postgresql"
  exit 1
fi

if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
  run as_root pg_ctlcluster "$pg_cluster_version" main start || true
  for _ in $(seq 1 30); do
    if pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
      break
    fi
    sleep 1
  done
fi

if ! pg_isready -h localhost -p 5432 >/dev/null 2>&1; then
  note "postgres: FAILED to start (see $LOG_FILE)"
  exit 1
fi

if ! run as_postgres "psql -tAc \"ALTER USER ${POSTGRES_DB_USER} WITH PASSWORD '${POSTGRES_DB_PASSWORD}';\""; then
  note "postgres: FAILED to set the ${POSTGRES_DB_USER} password (see $LOG_FILE)"
  exit 1
fi

if ! as_postgres "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='${POSTGRES_DB_NAME}'\"" 2>/dev/null | grep -q 1; then
  if ! run as_postgres "createdb ${POSTGRES_DB_NAME}"; then
    note "postgres: FAILED to create database '${POSTGRES_DB_NAME}' (see $LOG_FILE)"
    exit 1
  fi
fi

# Connect the way Django does — over TCP, with password auth, to the real
# database — so a cluster that is up but unreachable is caught here and not by
# a confusing test failure. Django also needs CREATEDB for the test database.
if ! run env PGPASSWORD="$POSTGRES_DB_PASSWORD" psql -h localhost -p 5432 \
    -U "$POSTGRES_DB_USER" -d "$POSTGRES_DB_NAME" -tAc "SELECT 1"; then
  note "postgres: FAILED — cannot connect the way Django will (see $LOG_FILE)"
  exit 1
fi

note "postgres: running on localhost:5432 (database '${POSTGRES_DB_NAME}')"

# ---------------------------------------------------------------------------
# 4. Frontend dependencies
# ---------------------------------------------------------------------------
cd "$PROJECT_DIR"

# .npmrc sets prefer-offline=true, so a stale packument baked into the image
# makes npm resolve transitive deps against versions it thinks do not exist.
# Clearing the cache and retrying is the fix; the first attempt stays cheap.
if run npm install --no-audit --no-fund; then
  note "npm: dependencies installed"
elif run npm cache clean --force && run npm install --no-audit --no-fund; then
  note "npm: dependencies installed (after clearing a stale npm cache)"
else
  note "npm: WARNING install failed (see $LOG_FILE)"
fi

for cli in bower gulp karma; do
  command -v "$cli" >/dev/null 2>&1 && continue
  run npm install -g bower gulp-cli karma-cli || note "npm: WARNING global CLI install failed"
  break
done

# bower resolves package names through registry.bower.io, which this
# environment's egress policy blocks (403 on CONNECT), and tarballs come from
# codeload.github.com, likewise blocked. Without bower_components the gulp
# vendor bundle cannot be built, so karma cannot run. Backend work and the
# frontend linter are unaffected, so this is a warning rather than a failure.
if [ -d "$PROJECT_DIR/bower_components" ] && [ -n "$(ls -A "$PROJECT_DIR/bower_components" 2>/dev/null)" ]; then
  note "bower: components already present"
elif run bower install --allow-root --config.interactive=false; then
  note "bower: components installed"
  run env SASS_SILENCE_DEPRECATIONS=legacy-js-api,import gulp dev \
    && note "frontend: built into frontend/dist" \
    || note "frontend: WARNING gulp build failed (see $LOG_FILE)"
else
  note "bower: SKIPPED — registry.bower.io is blocked by the egress policy,"
  note "       so frontend/dist cannot be built and karma tests cannot run."
  note "       Backend tests and the ESLint frontend linter still work."
fi

# ---------------------------------------------------------------------------
# 5. Session environment
# ---------------------------------------------------------------------------
CHROME_BINARY=""
for candidate in /usr/bin/google-chrome /opt/pw-browsers/chromium /usr/bin/chromium; do
  if [ -x "$candidate" ]; then
    CHROME_BINARY="$candidate"
    break
  fi
done

if [ -n "${CLAUDE_ENV_FILE:-}" ] && ! grep -q "evalai-venv" "$CLAUDE_ENV_FILE" 2>/dev/null; then
  {
    echo "export PATH=\"$VENV_DIR/bin:\$PATH\""
    # DJANGO_SETTINGS_MODULE is deliberately not exported. pytest-django gives
    # the environment variable precedence over pytest.ini, so exporting
    # settings.dev would silently run the suite with django-silk profiling
    # active and break query-count assertions. Leaving it unset lets
    # pytest.ini select settings.test; management commands pass it explicitly.
    echo "export POSTGRES_NAME=$POSTGRES_DB_NAME"
    echo "export POSTGRES_USER=$POSTGRES_DB_USER"
    echo "export POSTGRES_PASSWORD=$POSTGRES_DB_PASSWORD"
    echo "export POSTGRES_HOST=localhost"
    echo "export POSTGRES_PORT=5432"
    echo "export SASS_SILENCE_DEPRECATIONS=legacy-js-api,import"
    if [ -n "$CHROME_BINARY" ]; then
      echo "export CHROME_BIN=$CHROME_BINARY"
    fi
  } >>"$CLAUDE_ENV_FILE"
  note "env: PATH and Postgres variables exported"
fi

echo "Ready. Backend: pytest <path>  |  Lint: black/isort/flake8/pylint, npx eslint"
