# Docker Setup

Guide to setup EvalAI using Docker.

## EvalAI Installation

EvalAI officially supports local development and setup using **Docker and Docker Compose**.  
This is the **recommended and most stable way** to run EvalAI across **Windows, Linux, and macOS**.

---

## Prerequisites
[EvalAI] can run on Linux, Cloud, Windows, and macOS platforms. Please install [docker] and [docker-compose] before getting started with the installation of EvalAI.

Ensure the following are installed on your system:

- Docker (v20+ recommended)
- Docker Compose (v2+ recommended)
- Git

### Verify Installation

```shell
docker --version
docker compose version
git --version
```


**Step 1: Fork and Clone the Repository**

First, fork the EvalAI repository on GitHub:
```shell
https://github.com/Cloud-CV/EvalAI
```

## Common Issues & Troubleshooting

### Port Already in Use

Q. "I get an error that port 8888 is already in use — what should I do?"

A. Either stop the conflicting service or change the port mapping in `docker-compose.yml`.

- Check the process using the port:
  - Linux/macOS: `lsof -i :8888`
  - Windows (PowerShell): `netstat -ano | findstr :8888`
- Stop the conflicting service or update the mapping in `docker-compose.yml` (example: `ports: - "9000:8888"`) and then restart: `docker compose down && docker compose up --build`.


### Website Not Accessible After Containers Start

Q. "Containers are running but I can't access the site in my browser."

A. Services may still be initializing. Wait 1–2 minutes and check logs:

- `docker compose logs django` — look for successful startup lines and database migrations.
- If containers crash or hang, follow the logs with `docker compose logs -f` for live output.


### Database Errors / Stale Volumes

Q. "I see DB errors or migrations aren't applied on first run."

A. Volumes can retain stale state. To reset local state (this deletes local data):

- `docker compose down -v`
- `docker compose up --build`


### CI, Tests & Coverage Checks (reproducing Travis / Codecov locally)

Q. "CI or coverage checks are failing in CI — how can I run the same checks locally?"

A. The project CI (see `.travis.yml`) runs several stages you can reproduce locally. Key checks:

- Build step: `docker-compose --profile worker_py3_7 --profile worker_py3_8 --profile worker_py3_9 --profile statsd build`
- Backend tests (in CI run inside the `django` service):
  - `docker-compose run -e DJANGO_SETTINGS_MODULE=settings.test django pytest --cov . --cov-config .coveragerc --cov-report=xml:coverage-backend.xml --junitxml=junit-backend.xml -o junit_family=legacy`
- Frontend tests and build (if modifying frontend):
  - `docker-compose run nodejs bash -c "npm install && gulp dev && karma start --single-run --reporters=junit,coverage && gulp staging"`

Code quality checks used in CI (install locally before running):

- `pip install black==24.8.0 isort==5.12.0 flake8==3.8.2 pylint==3.3.6`
- `black --check --diff ./`
- `isort --check-only --diff --profile=black ./`
- `flake8 --config=.flake8 ./`
- `pylint --rcfile=.pylintrc --output-format=colorized --score=y --fail-under=7.5 ./`

If any of these checks fail locally, fix the issues and re-run the relevant command until they pass.


### Coverage uploads (Codecov)

Q. "CI uploads coverage to Codecov — how is that done and what are the project targets?"

A. CI uploads backend test results and coverage to Codecov during `after_success`. Locally you can reproduce the uploads (if you have credentials) with:

- `pip install codecov-cli`
- `codecovcli do-upload --report-type test_results --file junit-backend.xml`
- `bash <(curl -s https://codecov.io/bash) -f coverage-backend.xml -F backend`

Project coverage rules are defined in `codecov.yml`. Highlights:

- Backend project target: 70% (project), 80% for patch-level checks
- Frontend project target: 70% (project), 70% for patch-level checks
- Coverage components and stricter targets exist for core modules (models, serializers, etc.) — see `codecov.yml` for details.

If coverage decreases, add tests for uncovered lines and re-run the tests/coverage commands above.


### Repro tip: run backend tests quickly (local, without Docker)

If you prefer running tests without Docker and you have a local Python dev environment configured for the project:

- Create a virtualenv and install dev dependencies (match CI pinned versions where practical)
- Run: `pytest --cov . --cov-config .coveragerc`


### Stopping EvalAI (clean shutdown)

Q. "How do I stop EvalAI and (optionally) remove volumes?"

A.
- Stop containers: `docker compose down`
- Stop and remove volumes: `docker compose down -v`


### Contribution

If you are interested in contributing to EvalAI, please follow the [Contribution guidelines](https://github.com/Cloud-CV/EvalAI/blob/master/.github/CONTRIBUTING.md).
### Port Already in Use
