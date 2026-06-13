# Debugging Guide

Systematic steps to debug submission and evaluation problems.

## Participants

1. Reproduce with a minimal valid submission file.
2. Open failed submission → copy **stderr** and **stdout**.
3. Compare file format to challenge submission guidelines.
4. Retry after fixing; watch remaining submission quota.

## Challenge hosts

1. Run `evaluate()` locally with the same annotation and a sample submission file.
2. Confirm return dict structure matches [Metrics and Leaderboards](../../02-for-challenge-hosts/evaluation/metrics-leaderboards.html).
3. For remote evaluation, run `main.py` with debug logging and verify environment variables.
4. After script updates, wait for worker restart or restart self-hosted workers.

## Developers (local EvalAI)

1. Run `python scripts/workers/submission_worker.py` in one terminal and tail Django logs in another.
2. Inspect SQS/local queue for stuck messages.
3. Use Django shell to inspect `Submission` model state for a given PK.
4. Run targeted pytest: `pytest tests/unit/jobs/ -k submission`.

## Docker

```bash
docker compose logs django
docker compose logs worker
```

## See also

- [Evaluation issues](../common-issues/evaluation-issues.html)
- [Worker setup](../../04-development/deployment/worker-setup.html)
