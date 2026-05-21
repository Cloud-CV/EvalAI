# Remote Evaluation Example

End-to-end outline for a remote evaluation challenge. Full reference: [Remote Evaluation guide](../../02-for-challenge-hosts/evaluation/remote-evaluation.html).

## 1. Fork EvalAI-Starters

Use the [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) template and configure GitHub secrets as in [Getting Started](../../02-for-challenge-hosts/hosting-guide/getting-started.html).

## 2. Enable remote evaluation

In `challenge_config.yaml`:

```yaml
remote_evaluation: true
```

## 3. Configure the evaluation worker

Copy `remote_challenge_evaluation/` from the template. Set environment variables:

- `AUTH_TOKEN`
- `API_SERVER` (`https://eval.ai` or staging)
- `QUEUE_NAME`
- `CHALLENGE_PK`
- `SAVE_DIR` (optional)

Values come from the challenge **Manage** tab on EvalAI.

## 4. Implement `evaluate()`

Edit the starter `evaluate()` to load submissions, run your metrics, and return the standard `result` structure.

## 5. Push and approve

Push to the `challenge` branch. After the challenge is created and approved, install requirements and run:

```bash
cd EvalAI-Starters/remote_challenge_evaluation
python main.py
```

Keep the process running while the challenge accepts submissions.

## 6. Test

Submit a sample file from the UI or CLI and confirm the leaderboard updates.

## See also

- [Host a remote evaluation challenge](../../02-for-challenge-hosts/hosting-guide/host-challenge.html#host-a-remote-evaluation-challenge)
- [GitHub integration example](../integration-examples/github-integration.html)
