# Production Deployment

EvalAI production runs on AWS with containerized Django, workers, and managed data stores. This page summarizes operator concerns; internal runbooks may contain environment-specific values.

## Components

- **Web/API** — Django application behind load balancers
- **Workers** — submission, remote, and code-upload workers
- **Database** — PostgreSQL
- **Queue** — Amazon SQS for submission messages
- **Storage** — S3 for submission files and challenge assets

## Configuration

Use environment-specific Django settings modules (`production`, `staging`). Secrets (database URLs, AWS keys, auth keys) must be supplied via environment variables or your secret manager — never committed to the repository.

## Deploying changes

Follow your organization's CI/CD pipeline (see `.github/workflows/` in the repo). Typical steps:

1. Run tests and lint in CI.
2. Build and push container images.
3. Roll out API and worker deployments with health checks.
4. Run database migrations when models change — see [Migrations](../maintenance/migrations.html).
5. After API containers restart, production/staging deploys run `refresh_worker_task_definitions --commit-id <sha>` to re-register ECS worker task definitions with the newly pushed ECR images.

## ECS worker images and ECR lifecycle

ECS task definitions pin container image digests at registration time. EvalAI refreshes Fargate worker task definitions on each deploy so workers do not reference ECR images deleted by lifecycle policies.

**Recommended ECR lifecycle rules:**

- Keep the last 20 commit-tagged images per worker repository, or retain commit tags for at least 30 days.
- Avoid deleting image digests immediately after retagging `:latest`.
- Per-challenge Python versions (`3.7`, `3.8`, `3.9`) are selected via `worker_python_version` (default `3.9`) or a custom `worker_image_url`.

**Manual recovery:**

```bash
python manage.py refresh_worker_task_definitions --commit-id=<git-sha>
```

Or use the Django admin action **Refresh worker task definitions** on selected challenges.

## Self-hosted / forked EvalAI

Fork operators approve challenges via Django admin — see [Approval Process](../../02-for-challenge-hosts/hosting-guide/approval-process.html). Restart workers after approval so evaluation scripts load.

## See also

- [Worker Setup](worker-setup.html)
- [Scaling Guidelines](scaling-guidelines.html)
- [Monitoring](../maintenance/monitoring.html)
