# Docker Setup


# EvalAI Installation

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

Then clone your fork locally:
```shell
git clone https://github.com/<your-username>/EvalAI.git
cd EvalAI
```


**Environment Setup (Optional but Recommended)**

EvalAI ships with sensible defaults, so no .env file is required for basic local usage. However, if you want to customize configuration later (ports, secrets, email, etc.), you can add:
```shell
cp .env.example .env
```


**Step 2: Build and Run EvalAI Using Docker**

Start core services. This starts:
- Django backend
- PostgreSQL database
- SQS mock service
- Node.js frontend service

```shell
docker compose up --build
```


⏳ **Note:** First build may take several minutes. Be patient and don't panic!

During the build process, you may see:
- npm package installation messages
- npm engine version warnings (these are harmless - see troubleshooting section)
- Gulp build tasks running (css, js, html, images, fonts)
- Sass deprecation warnings (these are harmless - see troubleshooting section)
- Karma test runner starting (if running tests)

All of these are normal and expected during the build process. 

**Access EvalAI in Browser**

Once containers are running, open:
```
http://127.0.0.1:8888
```

> **Note:** The frontend is served by the Node.js service on port 8888, while the Django backend API runs on port 8000.

**Start Worker Services (Optional)**
- Required if you want to test challenge evaluations locally.
- EvalAI supports multiple Python versions for workers. You can start workers for specific Python versions:
```shell
# Start Python 3.7 worker
docker compose --profile worker_py3_7 up --build

# Start Python 3.8 worker
docker compose --profile worker_py3_8 up --build

# Start Python 3.9 worker
docker compose --profile worker_py3_9 up --build

# Start all worker versions together
docker compose --profile worker_py3_7 --profile worker_py3_8 --profile worker_py3_9 up --build
```

**Start StatsD Exporter (Optional)**
- For metrics collection and monitoring:
```shell
docker compose --profile statsd up --build
```

**Start All Services Together**
- To start all optional services (all workers + statsd):
```shell
docker compose --profile worker_py3_7 --profile worker_py3_8 --profile worker_py3_9 --profile statsd up --build
```

## Default Login Credentials

EvalAI automatically creates the following users:

| User type   | Username    | Password   | Permissions                                                                            |
| ----------- | ----------- | ---------- | -------------------------------------------------------------------------------------- |
| Superuser   | admin       | `password` | Perform CRUD operations on all tables in the database<br /> through django admin panel |
| Host        | host        | `password` | Create and manage challenges                                                           |
| Participant | participant | `password` | Participate in different challenges and make submissions                               |

If you are facing any issue during installation, please see our [common errors during installation page](https://evalai.readthedocs.io/en/latest/faq(developers).html#common-errors-during-installation).

[evalai-cli]: https://cli.eval.ai/
[evalai]: http://eval.ai
[docker-compose]: https://docs.docker.com/compose/install/
[docker]: https://docs.docker.com/install/linux/docker-ce/ubuntu/
---
### Role Description

- **Admin**: Has full access to the platform, including user management and system-level configuration.
- **Host**: Can create and manage challenges, phases, datasets, and evaluation settings.
- **Participant**: Can view challenges and submit solutions.

> ⚠️ **Security Note**:  
> These credentials are intended **only for local development**.  
> Do not use them in production environments.

---
## Verify Containers Are Running

After starting EvalAI, verify that all required containers are running:

```bash
docker ps
```
**Expected Containers**
- You should see containers similar to the following:

- **evalai-django** = The main backend service running the Django application.
- **evalai-db** = PostgreSQL database used by EvalAI to store users, challenges, submissions, and results.
- **evalai-sqs** = Local SQS-compatible service used to manage submission and evaluation queues.
- **evalai-worker_py3_7**, **evalai-worker_py3_8**, **evalai-worker_py3_9** = Worker services responsible for executing evaluation logic for different Python versions.
  These containers appear only if the corresponding worker profiles are enabled.


# Troubleshooting

## Issue: Port 8888 Already in Use
By default, EvalAI exposes the web interface on port 8888. If another service is already using this port, the containers will fail to start.

### How to Check Which Process Is Using the Port

**On Linux or macOS:**
```bash
lsof -i :8888
```

**On Windows (PowerShell):**
```powershell
netstat -ano | findstr :8888
```

### Fix Option 1: Stop the Conflicting Service

Stop or disable the service currently using port 8888, then restart EvalAI:
```bash
docker compose down
docker compose up --build
```

### Fix Option 2: Change the Port Mapping

Edit the `docker-compose.yml` file and update the exposed port. Example:
```yaml
ports:
  - "9000:8888"
```

After updating the port, restart the containers:
```bash
docker compose down
docker compose up --build
```

Access EvalAI at: http://127.0.0.1:9000

## Issue: Containers Start but Website Is Not Accessible

This usually happens when services are still initializing. Recommended steps:

1. Wait 1–2 minutes after starting containers
2. Check logs to ensure Django has started successfully:
```bash
docker compose logs django
```

## Issue: Database Errors on First Run

Occasionally, Docker volumes may contain stale data.

### Fix: Reset Volumes
```bash
docker compose down -v
docker compose up --build
```

⚠️ **Warning:** This removes all local data and recreates the database.

## Issue: Containers Fail to Start

If containers fail to start, check logs for details:
```bash
docker compose logs -f
```

For specific service logs:
```bash
docker compose logs django
docker compose logs nodejs
docker compose logs db
```

## Issue: npm Engine Version Warnings During Build

When installing npm packages, you may see warnings like:

```
npm WARN EBADENGINE Unsupported engine {
npm WARN EBADENGINE   package: 'minimatch@...',
npm WARN EBADENGINE   required: { node: '20 || >=22' },
npm WARN EBADENGINE   current: { node: 'v18.19.0', npm: '10.2.3' }
npm WARN EBADENGINE }
```

**These warnings are expected and harmless.** They occur because:
- EvalAI uses Node.js 18.19.0 (which meets the project's minimum requirement of `>=18.0.0`)
- Some npm dependencies prefer Node.js 20 or 22+, but they still work with Node.js 18.19.0
- npm displays these warnings to inform you of potential future compatibility considerations

The build will complete successfully despite these warnings. The frontend will function normally. These warnings do not affect:
- Application functionality
- Package installation
- Test execution
- Code coverage reporting
- Production builds

> **Note:** These warnings are informational and can be safely ignored. The project's Node.js version (18.19.0) is compatible with all dependencies, even if some prefer newer versions.

## Issue: Sass Deprecation Warnings During Build

When building the frontend, you may see Sass deprecation warnings like:

```
Deprecation Warning [legacy-js-api]: The legacy JS API is deprecated...
Deprecation Warning [import]: Sass @import rules are deprecated...
```

**These warnings are expected and harmless.** They indicate that:
- The build system uses the legacy Sass JavaScript API (which will be updated in future versions)
- The codebase uses `@import` statements instead of the newer `@use` syntax

The build will complete successfully despite these warnings. The frontend will function normally. These warnings do not affect:
- Application functionality
- Test execution
- Code coverage reporting
- Production builds

> **Note:** These warnings are informational and will be addressed in future updates. You can safely ignore them during development.

## Issue: CI, Tests & Coverage Checks

If CI or coverage checks are failing, you can reproduce the same checks locally. The project CI (see `.travis.yml`) runs several stages:

**Build step:**
```bash
docker-compose --profile worker_py3_7 --profile worker_py3_8 --profile worker_py3_9 --profile statsd build
```

**Backend tests (in CI run inside the `django` service):**
```bash
docker-compose run -e DJANGO_SETTINGS_MODULE=settings.test django pytest --cov . --cov-config .coveragerc --cov-report=xml:coverage-backend.xml --junitxml=junit-backend.xml -o junit_family=legacy
```

**Frontend tests and build (if modifying frontend):**
```bash
docker-compose run nodejs bash -c "npm install && gulp dev && karma start --single-run --reporters=junit,coverage && gulp staging"
```

**Code quality checks used in CI (install locally before running):**
```bash
pip install black==24.8.0 isort==5.12.0 flake8==3.8.2 pylint==3.3.6
black --check --diff ./
isort --check-only --diff --profile=black ./
flake8 --config=.flake8 ./
pylint --rcfile=.pylintrc --output-format=colorized --score=y --fail-under=7.5 ./
```

If any of these checks fail locally, fix the issues and re-run the relevant command until they pass.

**Coverage uploads (Codecov):**

CI uploads backend test results and coverage to Codecov during `after_success`. Locally you can reproduce the uploads (if you have credentials) with:

```bash
pip install codecov-cli
codecovcli do-upload --report-type test_results --file junit-backend.xml
bash <(curl -s https://codecov.io/bash) -f coverage-backend.xml -F backend
```

Project coverage rules are defined in `codecov.yml`. Highlights:
- Backend project target: 70% (project), 80% for patch-level checks
- Frontend project target: 70% (project), 70% for patch-level checks
- Coverage components and stricter targets exist for core modules (models, serializers, etc.) — see `codecov.yml` for details.

If coverage decreases, add tests for uncovered lines and re-run the tests/coverage commands above.

## Stopping EvalAI

To stop all running containers:
```bash
docker compose down
```

To stop and remove volumes (this deletes all data):
```bash
docker compose down -v
```

## Important Notes
- Non-Docker installation is not officially supported
- Docker setup works consistently across Windows, Linux, and macOS
- This is the recommended setup for contributors and challenge hosts
- When running tests locally outside Docker, ensure your global `pytest` configuration files (such as any `setup.cfg` in parent directories) are compatible with the `pytest` version you are using.

## Contribution

If you are interested in contributing to EvalAI, please follow the [Contribution guidelines](https://github.com/Cloud-CV/EvalAI/blob/master/.github/CONTRIBUTING.md)
