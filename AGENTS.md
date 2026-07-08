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
