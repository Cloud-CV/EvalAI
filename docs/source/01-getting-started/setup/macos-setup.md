# macOS Setup

Run EvalAI on macOS using Docker Desktop.

## Prerequisites

- [Docker Desktop for Mac](https://docs.docker.com/desktop/install/mac-install/)
- Git

## Install

```bash
git clone https://github.com/Cloud-CV/EvalAI.git evalai
cd evalai
docker compose up --build
```

Open [http://127.0.0.1:8888](http://127.0.0.1:8888) after containers start.

## Workers

```bash
docker compose --profile worker up --build
```

## Resources

Allocate sufficient memory to Docker Desktop (Preferences → Resources) if builds fail or containers OOM.

## Default users

| Role | Username | Password |
|------|----------|----------|
| Superuser | `admin` | `password` |
| Host | `host` | `password` |
| Participant | `participant` | `password` |

## See also

- [Linux setup](linux-setup.html) — identical compose commands
- [Installation issues](../../07-troubleshooting/common-issues/installation-issues.html)
