# Worker Setup

Submission workers pull messages from the queue and execute challenge `evaluate()` functions.

## Development

From the repository root (where `manage.py` lives):

```bash
python scripts/workers/submission_worker.py
```

Ensure Django, database, and SQS (or local queue) match your `docker-compose` development setup.

## Docker Compose

Start worker services with the worker profile:

```bash
docker compose --profile worker up --build
```

After approving a challenge on a self-hosted instance, restart workers so they reload evaluation scripts:

```bash
docker compose restart worker
```

## Worker startup behavior

On start, the worker:

1. Creates a temporary working directory.
2. Loads active challenges and evaluation scripts into `EVALUATION_SCRIPTS`.
3. Connects to the submission queue and listens for messages.

## Message format

Submission messages include:

```json
{
  "challenge_id": "<pk>",
  "phase_id": "<phase_pk>",
  "submission_id": "<submission_pk>"
}
```

Processing details: see [Submission Types](../../03-for-participants/submissions/submission-types.html).

## Remote and code-upload workers

- Remote evaluation: hosts run `EvalAI-Starters/remote_challenge_evaluation` — see [Remote Evaluation](../../02-for-challenge-hosts/evaluation/remote-evaluation.html).
- Code upload: `scripts/workers/code_upload_submission_worker.py`.

## See also

- [Production Deployment](production-deployment.html)
- [Scaling Guidelines](scaling-guidelines.html)
