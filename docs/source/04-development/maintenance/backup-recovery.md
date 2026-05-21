# Backup and Recovery

Protect challenge data, submissions, and database state before major upgrades or migrations.

## Database

- Schedule regular PostgreSQL backups (snapshots or `pg_dump`) for production.
- Test restore procedures on staging before relying on them in incidents.
- After restoring, restart application and worker services and verify queue connectivity.

## Submission files

Submission artifacts and challenge assets are stored in object storage (S3 in production). Enable versioning and cross-region replication if your policy requires it.

## Configuration

Export challenge `challenge_config.yaml` and evaluation scripts from host repositories (GitHub) — EvalAI-Starters repos are the source of truth for hosted challenges.

## Recovery checklist

1. Restore database to a consistent point in time.
2. Restore or verify object storage keys referenced by submission records.
3. Redeploy matching application and worker image versions.
4. Restart workers and confirm active challenges load in `EVALUATION_SCRIPTS`.
5. Smoke-test submission on a staging challenge.

## See also

- [Migrations](migrations.html)
- [Monitoring](monitoring.html)
