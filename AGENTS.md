# AGENTS.md

## Build verification (required)

Before marking any coding task complete:

1. Run build/tests for affected areas (or the full suite if unsure).
2. If anything fails, fix it and re-run until green.
3. Report what you ran in your final message.

| Scope | Command |
|-------|---------|
| Full suite | `./scripts/run-all-tests.sh` |
| Backend tests | See [Running Tests](#running-tests) below |
| Lint | See [Linting](#linting) below |

`run-all-tests.sh` resolves containers from `COMPOSE_PROJECT_NAME` (defaults to `workspace` on Cloud Agent VMs; set `COMPOSE_PROJECT_NAME=evalai` for local dev).

## Cursor Cloud-specific instructions

### Overview

EvalAI is a Docker-based application with four core services: PostgreSQL (`db`), ElasticMQ (`sqs`), Django backend (`django` on port 8000), and Node.js frontend (`nodejs` on port 8888). See `README.md` for default credentials and general setup.

### Starting Services

```bash
docker compose up --build -d db sqs django
```

The `nodejs` service has `deploy.resources` memory/CPU limits in `docker-compose.yml` which fail in Cloud Agent VMs due to cgroup v2 threaded-mode restrictions. Start it manually without resource limits:

```bash
# Ensure node_modules is a directory (not a file)
rm -f /workspace/node_modules 2>/dev/null
mkdir -p /workspace/node_modules

# Run nodejs container without resource limits
docker run -d --name workspace-nodejs-1 \
  --network workspace_default \
  --hostname nodejs \
  -e NODE_ENV=development \
  -e CHROME_BIN=/usr/bin/google-chrome \
  -e DISPLAY=:99.0 \
  -p 8888:8888 -p 35729:35729 \
  -v /workspace:/code \
  -v nodejs_nm:/code/node_modules \
  -v nodejs_bc:/code/bower_components \
  workspace-nodejs
```

If `nodejs_nm` / `nodejs_bc` volumes don't exist yet, initialize them from the image first:

```bash
docker volume create nodejs_nm && docker volume create nodejs_bc
docker run --rm -v nodejs_nm:/dest workspace-nodejs sh -c 'cp -a /code/node_modules/* /dest/'
docker run --rm -v nodejs_bc:/dest workspace-nodejs sh -c 'cp -a /code/bower_components/* /dest/'
```

### Docker Setup (Cloud Agent VMs)

Run the bootstrap script (also used by `.cursor/environment.json`):

```bash
bash cloud-agent/install.sh
```

On Ubuntu 24.04 (Noble) Cloud Agent images:

- Install `docker-compose-v2` (not `docker-compose-plugin`, which is unavailable).
- `iptables-legacy` alternatives may not exist; the bootstrap script skips that step when missing.
- If `systemctl` cannot start Docker, the script falls back to launching `dockerd` directly.

The daemon should use the `fuse-overlayfs` storage driver and `"cgroup-parent": "system.slice"` in `/etc/docker/daemon.json` to avoid cgroup v2 threaded-mode errors.

### Running Tests

- **Backend**: `docker exec -e DJANGO_SETTINGS_MODULE=settings.test workspace-django-1 bash -c 'cd /code && python manage.py flush --noinput && pytest --cov . --cov-config .coveragerc -q'`
  - Note: `flush --noinput` clears the DB. Re-run `manage.py seed` or manually recreate users afterward if you need the dev data.
- **Frontend**: `docker exec workspace-nodejs-1 bash -c 'Xvfb :99 -screen 0 1024x768x24 &>/dev/null & sleep 1 && npm test -- --single-run'`
- **Both**: `./scripts/run-all-tests.sh` (uses `COMPOSE_PROJECT_NAME`, default `workspace`)

### Linting

- **Backend**: `docker exec workspace-django-1 bash -c 'cd /code && python -m black --check --line-length=79 apps/ && python -m isort --check --profile=black --line-length=79 apps/'`
- **Frontend**: ESLint runs automatically as part of `gulp dev:runserver` (the nodejs container entrypoint). Check container logs for lint results.

### Key Gotchas

- Running `pytest` with `settings.test` flushes the database. Recreate users manually afterward if needed.
- The `manage.py seed` command creates 500 challenges with 2000 submissions each and takes ~15+ minutes. For quick dev setup, manually create users instead (admin/host/participant with password "password").
- The Django container's startup script (`docker/dev/django/container-start.sh`) runs migrations, collectstatic, and seed before starting uWSGI. To skip seed on restart, run uWSGI directly: `uwsgi --ini /code/docker/dev/django/uwsgi.ini`.

## Claude Code on the web

Web sessions run in a container with **no Docker daemon**, so the
docker-compose workflow above does not apply and `./scripts/run-all-tests.sh`
cannot be used there. `.claude/hooks/session-start.sh` (registered as a
`SessionStart` hook in `.claude/settings.json`) provisions the stack natively
instead:

- A Python 3.9 virtualenv at `/opt/evalai-venv`, kept outside the repository so
  it is never linted or collected by pytest, with `requirements/dev.txt`
  installed.
- `black`, `flake8`, `pylint` and `isort` pinned to the versions the
  `code_quality` job in `.github/workflows/ci-cd.yml` installs.
- A local PostgreSQL server on `localhost:5432` with an `evalai` database,
  since `settings/test.py` expects one there.
- Frontend Node dependencies via `npm install`.

The hook exports `PATH` and the `POSTGRES_*` variables, so commands run
directly rather than through `docker exec`:

| Scope | Command |
|-------|---------|
| Backend tests | `pytest tests/unit/web/test_models.py` |
| Backend lint | `black --check ./` · `isort --check-only --profile=black ./` · `flake8 --config=.flake8 ./` · `pylint --rcfile=.pylintrc ./` |
| Frontend lint | `npx eslint frontend/src/js/app.js` |
| Django | `DJANGO_SETTINGS_MODULE=settings.dev python manage.py check` |

`DJANGO_SETTINGS_MODULE` is deliberately **not** exported: pytest-django gives
the environment variable precedence over `pytest.ini`, so exporting
`settings.dev` would silently run the suite with django-silk profiling active
and break the query-count assertions. Leaving it unset lets `pytest.ini` select
`settings.test`; management commands need it passed explicitly, as above.

Full setup output is written to `/tmp/evalai-session-start.log`. The hook exits
immediately when `CLAUDE_CODE_REMOTE` is not `true`, so local Docker workflows
are unaffected.

### Known limitation: no frontend build or karma tests

`bower install` cannot run in a web session — the egress policy blocks
`registry.bower.io` (and `codeload.github.com`, where bower fetches tarballs).
Without `bower_components` the gulp vendor bundle is never produced, so
`gulp dev` and the karma frontend tests cannot run there. Use CI or a local
Docker checkout for those; backend tests and the ESLint frontend linter are
unaffected. Allowlisting `registry.bower.io` and `codeload.github.com` for the
environment would lift this restriction.
