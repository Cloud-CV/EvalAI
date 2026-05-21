# Evaluation Issues

Problems during or after submission evaluation.

## Submissions always fail

- Confirm evaluation script defines `evaluate()` with the correct signature for your challenge type (hosted vs remote).
- Ensure return value includes `result` with dataset split codenames matching `challenge_config.yaml`.
- Raise exceptions with clear messages for invalid participant files.

## Metrics missing on leaderboard

- Verify metric keys in `evaluate()` output match `leaderboard.schema.labels`.
- Check `challenge_phase_splits` visibility — scores may be host-only.
- Confirm the correct phase codename is used inside `evaluate()`.

## Remote evaluation not processing

- Host worker must be running (`python main.py` in `remote_challenge_evaluation`).
- Verify `AUTH_TOKEN`, `QUEUE_NAME`, `CHALLENGE_PK`, and `API_SERVER`.
- Confirm `remote_evaluation: true` in challenge config.

## Worker not picking up new evaluation script

After updating scripts on self-hosted EvalAI, restart workers:

```bash
docker compose restart worker
```

Allow ~10 minutes for script reload on production.

## Logs

Inspect submission **stderr** / **stdout** in the UI or database-backed logs for stack traces.

## See also

- [Evaluation Scripts](../../02-for-challenge-hosts/evaluation/evaluation-scripts.html)
- [Remote Evaluation](../../02-for-challenge-hosts/evaluation/remote-evaluation.html)
- [Submission errors](submission-errors.html)
