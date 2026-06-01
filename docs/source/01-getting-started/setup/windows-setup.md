# Windows Setup

Run EvalAI on Windows with Docker Desktop.

## Prerequisites

- [Docker Desktop for Windows](https://docs.docker.com/desktop/install/windows-install/) (WSL 2 backend recommended)
- Git for Windows

## Install

In PowerShell or Git Bash:

```bash
git clone https://github.com/Cloud-CV/EvalAI.git evalai
cd evalai
docker compose up --build
```

Browse to [http://127.0.0.1:8888](http://127.0.0.1:8888).

## Workers

```bash
docker compose --profile worker up --build
```

## Notes

- Keep the repository folder named `evalai` (lowercase).
- Line endings: use `git clone` with default settings; avoid CRLF issues in shell scripts inside containers when possible.
- For native Windows Python development without Docker, prefer WSL2 and follow [Linux setup](linux-setup.html) inside WSL.

## Default users

| Role | Username | Password |
|------|----------|----------|
| Superuser | `admin` | `password` |
| Host | `host` | `password` |
| Participant | `participant` | `password` |

## See also

- [Installation issues](../../07-troubleshooting/common-issues/installation-issues.html)
