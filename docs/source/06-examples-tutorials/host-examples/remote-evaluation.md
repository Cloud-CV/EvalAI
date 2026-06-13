# Remote Evaluation Example

End-to-end outline for a remote evaluation challenge using [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters). Full reference: [Remote Evaluation guide](../../02-for-challenge-hosts/evaluation/remote-evaluation.html).

## 1. Fork EvalAI-Starters

Use the [EvalAI-Starters](https://github.com/Cloud-CV/EvalAI-Starters) template and configure GitHub secrets as in [Getting Started](../../02-for-challenge-hosts/hosting-guide/getting-started.html).

## 2. Enable remote evaluation

In [`challenge_config.yaml`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/challenge_config.yaml):

```yaml
remote_evaluation: true
```

Push to `challenge` so the challenge is created on EvalAI before starting your worker.

## 3. Configure the evaluation worker

Use [`remote_challenge_evaluation/`](https://github.com/Cloud-CV/EvalAI-Starters/tree/master/remote_challenge_evaluation) from your fork. Set environment variables (from the challenge **Manage** tab on EvalAI):

- `AUTH_TOKEN`
- `API_SERVER` (`https://eval.ai` or staging)
- `QUEUE_NAME`
- `CHALLENGE_PK`
- `SAVE_DIR` (optional)

Install dependencies from [`remote_challenge_evaluation/requirements.txt`](https://github.com/Cloud-CV/EvalAI-Starters/blob/master/remote_challenge_evaluation/requirements.txt).

## 4. Implement `evaluate()`

Edit the worker’s evaluation logic (based on the starter) to load submissions, run your metrics, and return the standard `result` structure documented in [Evaluation scripts](../../02-for-challenge-hosts/evaluation/evaluation-scripts.html).

## 5. Push and approve

After the challenge is created and approved, run the worker from your fork:

```bash
cd remote_challenge_evaluation
pip install -r requirements.txt
python main.py
```

Keep the process running while the challenge accepts submissions.

## 6. Test

Submit a sample file from the UI or CLI and confirm the leaderboard updates.

## See also

- [EvalAI-Starters challenge examples](../evalai-starters-guide.html)
- [Host a remote evaluation challenge](../../02-for-challenge-hosts/hosting-guide/host-challenge.html#host-a-remote-evaluation-challenge)
- [GitHub integration example](../integration-examples/github-integration.html)
