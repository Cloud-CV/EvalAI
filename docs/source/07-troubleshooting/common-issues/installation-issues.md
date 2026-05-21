# Installation Issues

Common problems when setting up EvalAI locally with Docker.

## Cannot GET / on http://localhost:8888

Containers may not have finished building. Try:

```bash
docker compose down
docker compose up --build
```

## docker-compose version unsupported

Upgrade Docker Engine to a version that supports your Compose file format (Compose v3+).

## celery build: pull access denied for evalai_django

Clone directory must be named `evalai` (lowercase). Docker image names derive from the folder name; mismatches break image references.

## Login button does nothing

Clear browser cache and cookies, or use a fresh browser profile.

## DB seeding: Exception while running run() in scripts.seed

Delete the local PostgreSQL volume/database and retry. Ensure you use the Python version documented in the current README (Python 3.10+ for docs tooling; follow README for the main app).

## Peer authentication failed for postgres

Create a dedicated PostgreSQL user with database privileges, or use Docker Compose postgres service credentials from `.env` examples.

## Port 5432 already in use

```bash
sudo netstat -lpn | grep :5432
sudo kill <PID>
```

Or stop the conflicting local PostgreSQL instance.

## More help

- [Setup guides](../../01-getting-started/setup/index.html)
- [FAQ](../support/faq.html)
- [Contact support](../support/contact-support.html)
