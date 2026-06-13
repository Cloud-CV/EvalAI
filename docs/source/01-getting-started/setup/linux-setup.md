# Linux Setup

Run EvalAI locally on Linux with Docker (recommended).

## Prerequisites

- [Docker Engine](https://docs.docker.com/engine/install/)
- [Docker Compose](https://docs.docker.com/compose/install/)
- Git

## Install

```bash
git clone https://github.com/Cloud-CV/EvalAI.git evalai
cd evalai
docker compose up --build
```

Default services: `db`, `sqs`, `django`. Frontend: [http://127.0.0.1:8888](http://127.0.0.1:8888).

## Workers (optional)

```bash
docker compose --profile worker up --build
```

## Default users

| Role | Username | Password |
|------|----------|----------|
| Superuser | `admin` | `password` |
| Host | `host` | `password` |
| Participant | `participant` | `password` |

## Troubleshooting

- Clone directory must be named `evalai` (lowercase) for correct image names.
- Port conflicts: stop local PostgreSQL on 5432 if needed.

See [Installation issues](../../07-troubleshooting/common-issues/installation-issues.html).

## See also

- [Docker setup](docker-setup.html)
- [Manual setup](manual-setup.html)
