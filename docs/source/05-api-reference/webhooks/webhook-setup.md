# Webhook Setup

Evaluation scripts receive submission metadata via `**kwargs` in `evaluate()`. You can forward results to Slack or custom webhooks from inside your script.

## Slack example

```python
import json
import requests

def evaluate(test_annotation_file, user_annotation_file, phase_codename, **kwargs):
    submission_metadata = kwargs.get("submission_metadata")
    score = 0.95  # your metric

    if score > 0.9:
        webhook_url = "https://hooks.slack.com/services/..."
        requests.post(
            webhook_url,
            data=json.dumps({"text": f"High score submission: {submission_metadata}"}),
            headers={"Content-Type": "application/json"},
        )

    return {"result": [{"test_split": {"Accuracy": score}}]}
```

Create incoming webhooks in your Slack workspace admin settings.

## Custom webhooks

POST JSON payloads to your endpoint with any fields you extract from:

- `submission_metadata`
- File paths passed to `evaluate()`
- Computed metrics before returning `result`

Secure webhooks with secrets and HTTPS. Do not embed tokens in public challenge repositories.

## Platform webhooks

EvalAI does not expose a separate first-class “challenge webhook” URL per challenge in core open-source docs; host logic runs inside the evaluation script on workers or remote workers.

## See also

- [Webhook events](webhook-events.html)
- [Evaluation Scripts](../../02-for-challenge-hosts/evaluation/evaluation-scripts.html)
