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
```shell
docker compose up --build
```


⏳ First build may take several minutes. Be patient and don't panic. 

**Access EvalAI in Browser**

Once containers are running, open:
```shell
http://127.0.0.1:8888

```
**Start Worker Services (Optional)**
- Required if you want to test challenge evaluations locally.
```shell
docker compose --profile worker up --build
```
- Start StatsD Exporter (Optional)
```shell
docker compose --profile statsd up --build
```
- Start All Services Together
```shell
docker compose --profile worker --profile statsd up --build
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
- **evalai-worker** = Worker service responsible for executing evaluation logic.
This container appears only if the worker profile is enabled.


## Common Issues & Troubleshooting

### Port Already in Use

If **port 8888** is occupied, stop the conflicting service or update port mappings in **docker-compose.yml**.

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

**Database Errors on First Run**
- Reset containers and volumes:
```shell
docker compose down -v
docker compose up --build
```

- Containers Fail to Start
Check logs for details:
```shell
docker compose logs -f
```

**Stopping EvalAI**
```shell
docker compose down
```
- To remove volumes as well:
```shell
docker compose down -v
```
# Important Notes
- Non-Docker installation is not officially supported
- Docker setup works consistently across Windows, Linux, and macOS
- This is the recommended setup for contributors and challenge hosts

# Contribution

If you are interested in contributing to EvalAI, please follow the [Contribution guidelines](https://github.com/Cloud-CV/EvalAI/blob/master/.github/CONTRIBUTING.md)
