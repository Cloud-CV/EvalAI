# Webhook Events

There is no fixed platform-wide webhook catalog. Events you handle are defined by your evaluation script when it receives submission metadata.

## Typical metadata uses

| Event (conceptual) | Trigger | Suggested action |
|--------------------|---------|------------------|
| High score | Metric above threshold | Notify Slack / email |
| Failed validation | Exception in `evaluate()` | Log internally (participant sees failure) |
| New submission | Each `evaluate()` call | Update external dashboard |

## Submission metadata

`kwargs.get("submission_metadata")` may include team name, method name, and other fields configured via `submission_meta_attributes` in YAML.

Inspect metadata during development:

```python
def evaluate(test_annotation_file, user_annotation_file, phase_codename, **kwargs):
    print(kwargs.get("submission_metadata"))
```

## Reliability

- Webhook calls from `evaluate()` should use timeouts and avoid blocking evaluation indefinitely.
- Failures in optional notifications should not mask scoring errors — still return valid `result` or raise for true failures.

## See also

- [Webhook setup](webhook-setup.html)
- [Evaluation Scripts](../../02-for-challenge-hosts/evaluation/evaluation-scripts.html)
